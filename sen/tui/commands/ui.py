"""
application independent commands
"""

import logging

import urwid

from sen.exceptions import NotifyError
from sen.tui.buffer import HelpBuffer, TreeBuffer
from sen.tui.commands.base import (
    register_command, SameThreadCommand,
    Option, Argument,
    NoSuchCommand
)
from sen.util import log_traceback, log_last_traceback


logger = logging.getLogger(__name__)


class LogTracebackMixin:
    @log_traceback
    def do(self, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except NotifyError as ex:
            logger.error(repr(ex))
            self.ui.notify_message(str(ex), level="error")
        except Exception as ex:
            logger.error(repr(ex))
            self.ui.notify_message("Command failed: %s" % str(ex), level="error")
            raise


@register_command
class QuitCommand(SameThreadCommand):
    name = "quit"
    # TODO: make this configurable by asking whether to quit or not
    description = "Quit sen. No questions asked."

    def run(self):
        self.ui.quit()


@register_command
class KillBufferCommand(SameThreadCommand):
    name = "kill-buffer"
    description = "Remove currently displayed buffer."
    options_definitions = [
        Option("quit-if-no-buffer", "Quit when there's no buffer left", default=False)
    ]

    def run(self):
        buffers_left = self.ui.remove_current_buffer(close_if_no_buffer=self.arguments.quit_if_no_buffer)
        if buffers_left is None:
            self.ui.notify_message("Last buffer will not be removed.")
        elif buffers_left == 0:
            self.ui.run_command(QuitCommand.name)


@register_command
class SelectBufferCommand(SameThreadCommand):
    name = "select-buffer"
    description = "Display buffer with selected index."
    arguments_definitions = [
        Argument("index", "Index of buffer to display", default=1, action=int)
    ]

    def run(self):
        self.ui.pick_and_display_buffer(self.arguments.index)


@register_command
class SelectNextBufferCommand(SelectBufferCommand):
    name = "select-next-buffer"
    description = "Display next buffer."

    def run(self):
        self.arguments.set_argument("index", self.ui.current_buffer_index + 1)
        super().run()


@register_command
class SelectPreviousBufferCommand(SelectBufferCommand):
    name = "select-previous-buffer"
    description = "Display previous buffer."

    def run(self):
        self.arguments.set_argument("index", self.ui.current_buffer_index - 1)
        super().run()


@register_command
class DisplayBufferCommand(SameThreadCommand):
    name = "display-buffer"  # TODO: make this a universal display function

    arguments_definitions = [Argument("buffer", "Buffer instance to show.")]
    description = "This is an internal command and doesn't work from command line."

    def run(self):
        # TODO: doesn't work!, the method expects buffer class, not string
        self.ui.add_and_display_buffer(self.arguments.buffer)


@register_command
class DisplayHelpCommand(SameThreadCommand):
    name = "help"
    description = "Display help about buffer or command. When 'query' is not specified " + \
        "help for current buffer is being displayed."
    arguments_definitions = [Argument("query", "input string: command, buffer name")]

    def run(self):
        if self.arguments.query is None:
            self.ui.add_and_display_buffer(HelpBuffer(self.ui, self.buffer))
            return
        try:
            command = self.ui.commander.get_command(self.arguments.query)
        except NoSuchCommand:
            self.ui.notify_message("There is no such command: %r" % self.arguments.query)
        else:
            self.ui.add_and_display_buffer(HelpBuffer(self.ui, command))
            return
        # TODO: help view for commands could be displayed in footer


@register_command
class DisplayLayersCommand(DisplayBufferCommand):
    name = "layers"
    description = "open a tree view of all image layers (`docker images --tree` equivalent)"

    def run(self):
        self.arguments.set_argument("buffer", TreeBuffer(self.ui, self.docker_backend))
        super().run()


@log_traceback
def run_command_callback(ui, docker_object, edit_widget, text_input):
    logger.debug("%r %r", edit_widget, text_input)
    if "\n" in text_input:
        inp = text_input.strip()
        inp = inp.replace("\n", "")
        # first restore statusbar and then run the command
        ui.prompt_bar = None
        ui.set_focus("body")
        try:
            ui.run_command(inp, docker_object=docker_object)
        except NoSuchCommand as ex:
            logger.info("non-existent command initiated: %r", inp)
            ui.notify_message(str(ex), level="error")
        except Exception as ex:
            logger.info("command %r failed: %r", inp, ex)
            ui.notify_message("Error while running command '{}': {}".format(
                inp, ex
            ), level="error")
            log_last_traceback()
        ui.reload_footer()


@register_command
class PromptCommand(SameThreadCommand):
    name = "prompt"
    description = "Customize and pre-populate prompt with initial data."
    options_definitions = [
        Option("prompt-text", "Text forming the actual prompt", default=":"),
        Option("initial-text", "Prepopulated text", default="")
    ]

    def run(self):
        """
        prompt for text input.
        """
        # set up widgets
        leftpart = urwid.Text(self.arguments.prompt_text, align='left')
        editpart = urwid.Edit(multiline=True, edit_text=self.arguments.initial_text)

        # build promptwidget
        edit = urwid.Columns([
            ('fixed', len(self.arguments.prompt_text), leftpart),
            ('weight', 1, editpart),
        ])
        self.ui.prompt_bar = urwid.AttrMap(edit, "main_list_dg")

        self.ui.reload_footer()
        self.ui.set_focus("footer")

        urwid.connect_signal(editpart, "change", run_command_callback,
                             user_args=[self.ui, self.docker_object])


@register_command
class SearchCommand(SameThreadCommand, LogTracebackMixin):
    name = "search"
    description = "search and highlight (provide empty string to disable searching)"
    arguments_definitions = [
        Argument("query", "Input string to search for")
    ]
    aliases = ["/"]

    def run(self):
        # TODO: implement incsearch
        #   - match needs to be highlighted somehow, not with focus though
        #     - a line could split into a Text with multiple markups
        query = self.arguments.query if self.arguments.query is not None else ""
        self.do(self.ui.current_buffer.find_next, query)


@register_command
class SearchNextCommand(SameThreadCommand, LogTracebackMixin):
    name = "search-next"
    description = "next search occurrence"

    def run(self):
        self.do(self.ui.current_buffer.find_next)


@register_command
class SearchPreviousCommand(SameThreadCommand, LogTracebackMixin):
    name = "search-previous"
    description = "previous search occurrence"

    def run(self):
        self.do(self.ui.current_buffer.find_previous)


@register_command
class SearchCommand(SameThreadCommand, LogTracebackMixin):
    name = "filter"
    description = """\
Display only lines matching provided query (provide empty query to clear filtering)

In main listing, you may specify more precise query with these space-separated filters:
* t[ype]=c[ontainer[s]]
* t[ype]=i[mage[s]]
* s[tate]=r[unning])

Examples
* "type=container" - show only containers (short equivalent is "t=c")
* "type=image fedora" - show images with string "fedora" in name (equivalent "t=i fedora")\
"""

    arguments_definitions = [
        Argument("query", "Input query string", default="")
    ]

    def run(self):
        # TODO: realtime list change would be mindblowing
        self.do(self.ui.current_buffer.filter, self.arguments.query)


@register_command
class RefreshCurrentBufferCommand(SameThreadCommand):
    name = "refresh"
    description = "Refresh current buffer."

    def run(self):
        self.ui.current_buffer.refresh()


@register_command
class SearchPreviousCommand(SameThreadCommand):
    name = "toggle-live-updates"
    description = "Toggle realtime updates of the interface (this is useful when you are " + \
                  "removing multiple objects and don't want the listing change during " + \
                  "the process so you accidentally remove something)."

    def run(self):
        self.ui.current_buffer.widget.toggle_realtime_events()


@register_command
class RedrawUI(SameThreadCommand):
    name = "redraw"
    description = "Redraw user interface."

    def run(self):
        self.ui.loop.screen.clear()
        self.ui.refresh()
