import logging

from sen.exceptions import NotifyError
from sen.util import log_traceback


logger = logging.getLogger(__name__)


@log_traceback
def search(ui, oldfooter, edit_widget, text_input):
    logger.debug("%r %r", edit_widget, text_input)
    if text_input.endswith("\n"):
        # TODO: implement incsearch
        #   - match needs to be highlighted somehow, not with focus though
        ui.mainframe.prompt_bar = None
        ui.mainframe.set_footer(oldfooter)
        try:
            ui.current_buffer.find_next(text_input[:-1])
        except NotifyError as ex:
            logger.error(repr(ex))
            ui.notify_message(str(ex), level="error")
        ui.mainframe.set_focus("body")
        ui.reload_footer()


@log_traceback
def filter(ui, oldfooter, edit_widget, text_input):
    logger.debug("%r %r", edit_widget, text_input)
    if text_input.endswith("\n"):
        ui.mainframe.prompt_bar = None
        ui.mainframe.set_footer(oldfooter)
        try:
            ui.current_buffer.filter(text_input[:-1])
        except NotifyError as ex:
            logger.error(repr(ex))
            ui.notify_message(str(ex), level="error")
        ui.mainframe.set_focus("body")
        ui.reload_footer()
