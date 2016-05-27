"""
application independent commands
"""

import logging

import urwid

from sen.exceptions import NotifyError
from sen.tui.buffer import HelpBuffer, TreeBuffer
from sen.tui.commands.base import register_command, SameThreadCommand, Argument, Option, \
    NoSuchCommand
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

    def run(self):
        self.ui.worker.shutdown(wait=False)
        self.ui.ui_worker.shutdown(wait=False)
        raise urwid.ExitMainLoop()


@register_command
class KillBufferCommand(SameThreadCommand):
    name = "kill-buffer"  # this could be named better

    def __init__(self, close_if_no_buffer=True, **kwargs):
        super().__init__(**kwargs)
        self.close_if_no_buffer = close_if_no_buffer

    def run(self):
        buffers_left = self.ui.remove_current_buffer(close_if_no_buffer=self.close_if_no_buffer)
        if buffers_left is None:
            self.ui.notify_message("Last buffer will not be removed.")
        elif buffers_left == 0:
            self.ui.run_command(QuitCommand.name)


@register_command
class RemoveBufferCommand(KillBufferCommand):
    name = "remove-buffer"

    def __init__(self, **kwargs):
        super().__init__(close_if_no_buffer=False, **kwargs)


@register_command
class SelectBufferCommand(SameThreadCommand):
    name = "select-buffer"
    option_definitions = [
        Option("index", "Index of buffer to display", default=1, action=int)
    ]

    def run(self):
        self.ui.pick_and_display_buffer(self.arguments.index)


@register_command
class SelectNextBufferCommand(SelectBufferCommand):
    name = "select-next-buffer"

    def run(self):
        self.arguments.set_argument("index", self.ui.current_buffer_index + 1)
        super().run()


@register_command
class SelectPreviousBufferCommand(SelectBufferCommand):
    name = "select-previous-buffer"

    def run(self):
        self.arguments.set_argument("index", self.ui.current_buffer_index - 1)
        super().run()


@register_command
class DisplayBufferCommand(SameThreadCommand):
    name = "display-buffer"
    option_definitions = [Option("buffer", "Name of buffer to show")]

    def run(self):
        self.ui.add_and_display_buffer(self.arguments.buffer)


@register_command
class DisplayHelpCommand(DisplayBufferCommand):
    name = "help"

    def run(self):
        self.arguments.set_argument("buffer", HelpBuffer(self.ui))
        super().run()


@register_command
class DisplayLayersCommand(DisplayBufferCommand):
    name = "layers"

    def run(self):
        self.arguments.set_argument("buffer", TreeBuffer(self.ui, self.docker_backend))
        super().run()


@log_traceback
def run_command_callback(ui, edit_widget, text_input):
    logger.debug("%r %r", edit_widget, text_input)
    if text_input.endswith("\n"):
        inp = text_input.strip()
        try:
            ui.run_command(inp)
        except NoSuchCommand as ex:
            logger.info("non-existent command initiated: %r", inp)
            ui.notify_message(str(ex), level="error")
        except Exception as ex:
            logger.info("command %r failed: %r", inp, ex)
            ui.notify_message("Error while running command '{}': {}".format(
                inp, ex
            ), level="error")
            log_last_traceback()
        ui.prompt_bar = None
        ui.set_focus("body")
        ui.reload_footer()


@register_command
class PromptCommand(SameThreadCommand):
    name = "prompt"
    argument_definitions = [
        Argument("prompt-text", "Text forming the actual prompt", default=":"),
        Argument("initial-text", "Prepopulated text", default="")
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

        urwid.connect_signal(editpart, "change", run_command_callback, user_args=[self.ui])


@register_command
class SearchCommand(SameThreadCommand, LogTracebackMixin):
    name = "search"
    option_definitions = [
        Option("query", "Input string to search for")
    ]

    def run(self):
        # TODO: implement incsearch
        #   - match needs to be highlighted somehow, not with focus though
        #     - a line could split into a Text with multiple markups
        query = self.arguments.query if self.arguments.query is not None else ""
        self.do(self.ui.current_buffer.find_next, query)


@register_command
class SearchNextCommand(SameThreadCommand, LogTracebackMixin):
    name = "search-next"

    def run(self):
        self.do(self.ui.current_buffer.find_next)


@register_command
class SearchPreviousCommand(SameThreadCommand, LogTracebackMixin):
    name = "search-previous"

    def run(self):
        self.do(self.ui.current_buffer.find_previous)


@register_command
class SearchCommand(SameThreadCommand, LogTracebackMixin):
    name = "filter"
    option_definitions = [
        Option("query", "Filter objects which container provided input string", default="")
    ]

    def run(self):
        # TODO: realtime list change would be mindblowing
        self.do(self.ui.current_buffer.filter, self.arguments.query)


@register_command
class SearchPreviousCommand(SameThreadCommand):
    name = "refresh-current-buffer"

    def run(self):
        self.ui.current_buffer.refresh()


@register_command
class SearchPreviousCommand(SameThreadCommand):
    name = "toggle-live-updates"

    def run(self):
        self.ui.current_buffer.widget.toggle_realtime_events()

