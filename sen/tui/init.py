"""
Application specific code.
"""

import logging

from sen.exceptions import NotifyError
from sen.tui.ui import get_app_in_loop
from sen.tui.buffer import LogsBuffer, MainListBuffer, InspectBuffer, HelpBuffer, ImageInfoBuffer, TreeBuffer, \
    ContainerInfoBuffer
from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend, DockerImage, DockerContainer

from sen.util import log_traceback

logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.d = DockerBackend()

        self.loop, self.ui = get_app_in_loop(PALLETE)

    def run(self):
        self.main_list_buffer = MainListBuffer(self.d, self)

        # TODO move to commands
        # FIXME: this breaks rendering -- focus is not being displayed correctly
        @log_traceback
        def chain_fcs():
            self.main_list_buffer.refresh(focus_on_top=True)
            self.add_and_display_buffer(self.main_list_buffer, redraw=True)
        self.run_quickly_in_bacakground(chain_fcs)
        super().run()

    # TODO: these display methods should be in commands

    def display_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self))

    def display_and_follow_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self, follow=True))

    def inspect(self, docker_object):
        self.add_and_display_buffer(InspectBuffer(docker_object))

    def display_info(self, docker_object):
        if isinstance(docker_object, DockerImage):
            buffer_class = ImageInfoBuffer
        elif isinstance(docker_object, DockerContainer):
            buffer_class = ContainerInfoBuffer
        else:
            self.notify_message("Can't display info for '%s'" % docker_object, level="error")
            logger.error("unable to display info buffer for %r", docker_object)
            return
        try:
            self.add_and_display_buffer(buffer_class(docker_object, self))
        except NotifyError as ex:
            self.notify_message(str(ex), level="error")
            logger.error(repr(ex))

    def refresh_main_buffer(self, refresh_buffer=True):
        assert self.main_list_buffer is not None
        if refresh_buffer:
            self.main_list_buffer.refresh()
        self.display_buffer(self.main_list_buffer)

    def display_help(self):
        self.add_and_display_buffer(HelpBuffer())

    def display_tree(self):
        self.add_and_display_buffer(TreeBuffer(self.d, self))

    # FOOTER

    def set_footer(self, widget):
        self.mainframe.set_footer(widget)

    def reload_footer(self):
        self.mainframe.reload_footer()

    def remove_notification_message(self, message):
        self.mainframe.remove_notification_message(message)

    def notify_widget(self, *args, **kwargs):
        self.mainframe.notify_widget(*args, **kwargs)

    def notify_message(self, *args, **kwargs):
        self.mainframe.notify_message(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        self.mainframe.prompt(*args, **kwargs)