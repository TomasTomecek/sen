"""
Application specific code.
"""

import logging

from sen.tui.commands.base import Commander
from sen.tui.commands.display import DisplayListingCommand
from sen.tui.ui import get_app_in_loop
from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend


logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.d = DockerBackend()

        self.loop, self.ui = get_app_in_loop(PALLETE)

        self.ui.commander = Commander(self.ui, self.d)

    def run(self):
        self.ui.run_command(DisplayListingCommand.name)
        self.loop.run()
