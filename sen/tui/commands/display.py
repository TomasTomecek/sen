"""
commands related to displaying stuff

FIXME: some of these commands duplicate stuff in ui
"""

import logging

from sen.docker_backend import DockerImage, DockerContainer
from sen.exceptions import NotifyError
from sen.tui.buffer import (
    TreeBuffer, HelpBuffer,
    ImageInfoBuffer, ContainerInfoBuffer,
    MainListBuffer
)
from sen.tui.commands.base import FrontendCommand, register_command


logger = logging.getLogger(__name__)


@register_command
class DisplayLayersTreeCommand(FrontendCommand):
    name = "display-layers-tree"

    def run(self):
        self.ui.add_and_display_buffer(TreeBuffer(self.docker_object, self.ui))


@register_command
class DisplayHelpCommand(FrontendCommand):
    name = "display-help"

    def run(self):
        self.ui.add_and_display_buffer(HelpBuffer(self.ui, self.buffer))


@register_command
class DisplayInfoBufferCommand(FrontendCommand):
    name = "display-info"

    def run(self):
        # TODO: needs better abstraction, backend object should be tied together with frontend
        # object via a new Class
        if isinstance(self.docker_object, DockerImage):
            buffer_class = ImageInfoBuffer
        elif isinstance(self.docker_object, DockerContainer):
            buffer_class = ContainerInfoBuffer
        else:
            self.ui.notify_message("Can't display info for '%s'" % self.docker_object,
                                   level="error")
            logger.error("unable to display info buffer for %r", self.docker_object)
            return
        try:
            # FIXME: this try/except block should be in upper frame
            self.ui.add_and_display_buffer(buffer_class(self.docker_object, self.ui))
        except NotifyError as ex:
            self.ui.notify_message(str(ex), level="error")
            logger.error(repr(ex))


@register_command
class DisplayListingCommand(FrontendCommand):
    name = "display-listing"

    def run(self):
        b = MainListBuffer(self.ui, self.docker_backend)
        self.ui.add_and_display_buffer(b, redraw=True)
