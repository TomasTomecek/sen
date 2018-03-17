"""
Application specific code.
"""

import logging
import threading

from sen.exceptions import NotifyError
from sen.tui.commands.base import Commander, SameThreadPriority
from sen.tui.commands.display import DisplayListingCommand
from sen.tui.ui import get_app_in_loop
from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend


logger = logging.getLogger(__name__)


class Application:
    def __init__(self, yolo=False):
        self.d = DockerBackend()

        self.loop, self.ui = get_app_in_loop(PALLETE)

        self.ui.yolo = yolo

        self.ui.commander = Commander(self.ui, self.d)

        self.rt_thread = threading.Thread(target=self.realtime_updates, daemon=True)
        self.rt_thread.start()

    def run(self):
        self.ui.run_command(DisplayListingCommand.name, queue=SameThreadPriority())
        self.loop.run()

    def realtime_updates(self):
        """
        fetch realtime events from docker and pass them to buffers

        :return: None
        """
        # TODO: make this available for every buffer
        logger.info("starting receiving events from docker")
        it = self.d.realtime_updates()
        while True:
            try:
                event = next(it)
            except NotifyError as ex:
                self.ui.notify_message("error when receiving realtime events from docker: %s" % ex,
                                       level="error")
                return
            # FIXME: we should pass events to all buffers
            # ATM the buffers can't be rendered since they are not displayed
            # and hence traceback like this: ListBoxError("Listbox contents too short! ...
            logger.debug("pass event to current buffer %s", self.ui.current_buffer)
            try:
                self.ui.current_buffer.process_realtime_event(event)
            except Exception as ex:
                # swallow any exc
                logger.error("error while processing runtime event: %r", ex)
