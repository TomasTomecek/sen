"""
these commands may take long to finish, they are usually being run against external service (e.g.
docker engine)
"""
import logging
import webbrowser

from sen.tui.buffer import LogsBuffer, InspectBuffer
from sen.tui.commands.base import BackendCommand, register_command, Argument
from sen.tui.widgets.list.util import get_operation_notify_widget
from sen.docker_backend import DockerContainer


logger = logging.getLogger(__name__)


class OperationCommand(BackendCommand):
    def do(self, fn_name, pre_message=None, notif_level="info"):
        pre_message = pre_message or self.pre_info_message.format(
            container_name=self.docker_object.short_name)
        self.ui.notify_message(pre_message)
        try:
            operation = getattr(self.docker_object, fn_name)()
        except AttributeError:
            log_txt = "you can't {} {}".format(fn_name, self.docker_object)
            logger.error(log_txt)
            notif_txt = "You can't {} {} {!r}.".format(
                fn_name,
                self.docker_object.pretty_object_type.lower(),
                self.docker_object.short_name)
            self.ui.notify_message(notif_txt, level="error")
        except Exception as ex:
            self.ui.notify_message(str(ex), level="error")
            raise
        else:
            self.ui.remove_notification_message(pre_message)
            self.ui.notify_widget(
                get_operation_notify_widget(operation, notif_level=notif_level)
            )


class MatchingOperationCommand(OperationCommand):
    """ this is just a shortcut """
    def run(self):
        self.do(self.name)


@register_command
class RemoveCommand(OperationCommand):
    name = "rm"
    description = "remove provided object, image or container"

    # FIXME: split this into rm and rmi
    def run(self):
        self.do("remove",
                pre_message="Removing {} {}...".format(
                    self.docker_object.pretty_object_type.lower(),
                    self.docker_object.short_name),
                notif_level="important")


@register_command
class StartContainerCommand(MatchingOperationCommand):
    name = "start"
    description = "start a container"
    pre_info_message = "Starting container {container_name}..."


@register_command
class StopContainerCommand(MatchingOperationCommand):
    name = "stop"
    description = "stop a container"
    pre_info_message = "Stopping container {container_name}..."


@register_command
class RestartContainerCommand(MatchingOperationCommand):
    name = "restart"
    description = "restart a container"
    pre_info_message = "Restarting container {container_name}..."


@register_command
class KillContainerCommand(MatchingOperationCommand):
    name = "kill"
    description = "kill a container"
    pre_info_message = "Killing container {container_name}..."


@register_command
class PauseContainerCommand(MatchingOperationCommand):
    name = "pause"
    description = "pause a container"
    pre_info_message = "Pausing container {container_name}..."


@register_command
class UnpauseContainerCommand(MatchingOperationCommand):
    name = "unpause"
    description = "unpause a container"
    pre_info_message = "Unpausing container {container_name}..."


@register_command
class LogsCommand(BackendCommand):
    name = "logs"
    description = "display logs of a container"
    argument_definitions = [Argument("follow", "Follow logs.", default=False, aliases=["-f", "f"])]

    def run(self):
        self.ui.add_and_display_buffer(
            LogsBuffer(self.ui, self.docker_object, follow=self.arguments.follow))


@register_command
class InspectCommand(BackendCommand):
    name = "inspect"
    description = "inspect provided object, a container or an image"

    def run(self):
        if not self.docker_object:
            self.ui.notify_message("No docker object specified.", level="error")
            return
        self.ui.add_and_display_buffer(InspectBuffer(self.ui, self.docker_object))


@register_command
class OpenPortsInBrowser(BackendCommand):
    name = "open-browser"
    description = "open exposed port in a browser"

    def run(self):
        if not self.docker_object or not isinstance(self.docker_object, DockerContainer):
            self.ui.notify_message("No docker container specified.", level="error")
            return

        if not self.docker_object.running:
            self.ui.notify_message("Container is not running - no ports are available.", level="error")
            return

        ports = self.docker_object.net.ports.values()
        logger.info(ports)
        if not ports or len(ports) < 1:
            # order of this calls is not logical but looks graphically better and I found out that's asynchronous so it
            # isn't controllable which would be first
            self.ui.notify_message("Hint: To find unmapped ports go to the detailed scope by hitting Enter.", level="info")
            self.ui.notify_message("There are no mapped ports available for '%s" % self.docker_object.short_name, level="error")
            return

        success = False
        for value in ports:
            if value:
                success = True
                url = "http://127.0.0.1:" + value
                logger.info(value)
                webbrowser.open(url)

        if not success:
            self.ui.notify_message("Hint: To find unmapped ports go to the detailed scope by hitting Enter.", level="info")
            self.ui.notify_message("There are no mapped ports available for '%s" % self.docker_object.short_name,
                                   level="error")

