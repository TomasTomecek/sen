"""
Definition of commands

This could be also split into two parts: generic framework part, application specific part
"""

import logging
import shlex


logger = logging.getLogger(__name__)

# command -> Class
commands_mapping = {}


class KeyNotMapped(Exception):
    pass


class NoSuchCommand(Exception):
    pass


class NoSuchOptionOrArgument(Exception):
    pass


# class decorator to register commands
def register_command(kls):
    commands_mapping[kls.name] = kls
    for a in kls.aliases:
        commands_mapping[a] = kls
    return kls


class CommandPriority:
    pass


class BackendPriority(CommandPriority):
    """ command takes long to execute """


class FrontendPriority(CommandPriority):
    """ command needs to be executed ASAP """


class SameThreadPriority(CommandPriority):
    """ run the task in same thread as UI """


def true_action(val=None):
    if val is not None:
        return val
    return True


class ArgumentBase:
    """
    Base class for arguments and options
    """
    def __init__(self, name, description, action=true_action, default=None):
        self.name = name
        self.description = description
        self.default = default
        self.action = action


class Option(ArgumentBase):
    """
    options alter behavior, are not positional
    """
    def __init__(self, name, description, action=true_action, aliases=None, default=None):
        super().__init__(name, description, action=action, default=default)
        self.aliases = aliases or []

    def __str__(self):
        return "{} default={} action=\"{}\" aliases={}".format(
            self.name, self.default, self.action, self.aliases
        )

    def __unicode__(self):
        return self.__str__()


class Argument(ArgumentBase):
    """
    arguments are positional
    """
    pass


def normalize_arg_name(name):
    return name.replace("-", "_")  # so we can access names-with-dashes


class ArgumentProcessor:
    """
    responsible for parsing given list of arguments
    """
    def __init__(self, options, arguments):
        """
        :param options: list of options
        :param arguments: list of arguments
        """
        self.given_arguments = {}
        self.options = {}
        for a in options:
            self.options[a.name] = a
            self.given_arguments[normalize_arg_name(a.name)] = a.default
            for alias in a.aliases:
                self.options[alias] = a
        for o in arguments:
            self.given_arguments[normalize_arg_name(o.name)] = o.default
        self.arguments = arguments
        logger.info("arguments = %s", arguments)
        logger.info("options = %s", options)

    def process(self, argument_list):
        """
        :param argument_list: list of str, input from user
        :return: dict:
            {"cleaned_arg_name": "value"}
        """
        arg_index = 0
        for a in argument_list:
            opt_and_val = a.split("=", 1)
            opt_name = opt_and_val[0]
            try:
                # option
                argument = self.options[opt_name]
            except KeyError:
                # argument
                try:
                    argument = self.arguments[arg_index]
                except IndexError:
                    logger.error("option/argument %r not specified", a)
                    raise NoSuchOptionOrArgument("No such option or argument: %r" % opt_name)
            logger.info("argument found: %s", argument)

            safe_arg_name = normalize_arg_name(argument.name)  # so we can access names-with-dashes

            logger.info("argument is available under name %r", safe_arg_name)

            if isinstance(argument, Argument):
                arg_index += 1
                value = (a, )
            else:
                try:
                    value = (opt_and_val[1], )
                except IndexError:
                    value = tuple()

            arg_val = argument.action(*value)

            logger.info("argument %r has value %r", safe_arg_name, arg_val)
            self.given_arguments[safe_arg_name] = arg_val
        return self.given_arguments


class CommandArgumentsGetter:
    def __init__(self, given_arguments):
        self.given_arguments = given_arguments

    def set_argument(self, arg_name, value):
        self.given_arguments[arg_name] = value

    def __getattr__(self, item):
        try:
            return self.given_arguments[item]
        except KeyError:
            # this is an error in code, not user error
            logger.error("no argument/option defined: %r", item)
            raise AttributeError("No such option or argument: %r" % item)


class Command:
    # command name, unique identifier, used also in prompt
    name = ""
    # message explaining what's about to happen
    pre_info_message = ""
    # message explaining what has happened
    post_info_message = ""
    # how long it takes to run the command - in which queue it should be executed
    priority = None
    # used in help message
    description = ""
    # define options
    options_definitions = []
    # define arguments
    arguments_definitions = []
    # command is available under these aliases
    aliases = []

    def __init__(self, ui=None, docker_backend=None, docker_object=None, buffer=None, size=None):
        """

        :param ui:
        :param docker_backend:
        :param docker_object:
        :param buffer:
        """
        logger.debug(
            "command %r initialized: ui=%r, docker_backend=%r, docker_object=%r, buffer=%r",
            self.name, ui, docker_backend, docker_object, buffer)
        self.ui = ui
        self.docker_backend = docker_backend
        self.docker_object = docker_object
        self.buffer = buffer
        self.size = size
        self.argument_processor = ArgumentProcessor(self.options_definitions,
                                                    self.arguments_definitions)
        self.arguments = None

    def process_args(self, arguments):
        """

        :param arguments: dict
        :return:
        """
        given_arguments = self.argument_processor.process(arguments)
        logger.info("given arguments = %s", given_arguments)
        self.arguments = CommandArgumentsGetter(given_arguments)

    def run(self):
        raise NotImplementedError()


class FrontendCommand(Command):
    priority = FrontendPriority()


class BackendCommand(Command):
    priority = BackendPriority()


class SameThreadCommand(Command):
    priority = SameThreadPriority()


class Commander:
    """
    Responsible for managing commands: it's up to workers to do the commands actually.
    """
    def __init__(self, ui, docker_backend):
        self.ui = ui
        self.docker_backend = docker_backend
        self.modifier_keys_pressed = []
        logger.debug("available commands: %s", commands_mapping)

    def get_command(self, command_input, docker_object=None, buffer=None, size=None):
        """
        return command instance which is the actual command to be executed

        :param command_input: str, command name and its args: "command arg arg2=val opt"
        :param docker_object:
        :param buffer:
        :param size: tuple, so we can call urwid.keypress(size, ...)
        :return: instance of Command
        """
        logger.debug("get command for command input %r", command_input)

        if not command_input:
            # noop, don't do anything
            return

        if command_input[0] in ["/"]:  # we could add here !, @, ...
            command_name = command_input[0]
            unparsed_command_args = shlex.split(command_input[1:])
        else:
            command_input_list = shlex.split(command_input)
            command_name = command_input_list[0]
            unparsed_command_args = command_input_list[1:]

        try:
            CommandClass = commands_mapping[command_name]
        except KeyError:
            logger.info("no such command: %r", command_name)
            raise NoSuchCommand("There is no such command: %s" % command_name)
        else:
            cmd = CommandClass(ui=self.ui, docker_backend=self.docker_backend,
                               docker_object=docker_object, buffer=buffer, size=size)
            cmd.process_args(unparsed_command_args)
            return cmd

    def get_command_input_by_key(self, key):
        logger.debug("get command input for key %r", key)

        modifier_keys = ["g"]  # FIXME: we should be able to figure this out from existing keybinds

        inp = "".join(self.modifier_keys_pressed) + key

        try:
            command_input = self.ui.current_buffer.get_keybinds()[inp]
        except KeyError:
            if key in modifier_keys:
                # TODO: inform user maybe
                self.modifier_keys_pressed.append(key)
                logger.info("modifier keys pressed: %s", self.modifier_keys_pressed)
                return
            else:
                logger.info("no such keybind: %r", inp)
                self.modifier_keys_pressed.clear()
                raise KeyNotMapped("No such keybind: %r." % inp)
        else:
            self.modifier_keys_pressed.clear()
            return command_input
