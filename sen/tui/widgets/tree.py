import logging

import urwidtrees

from sen.tui.widgets.info import SelectableText
from sen.tui.widgets.list.util import RowWidget
from sen.tui.widgets.util import get_basic_image_markup, SelectableText

logger = logging.getLogger(__name__)


class TreeNodeWidget(SelectableText):
    def __init__(self, ui, docker_image):
        self.ui = ui
        self.docker_image = docker_image
        super().__init__(get_basic_image_markup(docker_image))

    def keypress(self, size, key):
        logger.debug("%s %s %s", self.__class__, key, size)
        if key == "enter":
            self.ui.display_image_info(self.docker_image)
            return
        return key


class TreeBackend(urwidtrees.Tree):
    def __init__(self, docker_backend, ui):
        super().__init__()
        self.ui = ui
        self.root = docker_backend.scratch_image

    def __getitem__(self, pos):
        return RowWidget([TreeNodeWidget(self.ui, pos)])

    # Tree API
    def parent_position(self, pos):
        return pos.parent_image

    def first_child_position(self, pos):
        ch = pos.children
        if ch:
            return pos.children[0]
        else:
            return None

    def last_child_position(self, pos):
        ch = pos.children
        if ch:
            return pos.children[-1]
        else:
            return None

    def next_sibling_position(self, pos):
        return pos.get_next_sibling()

    def prev_sibling_position(self, pos):
        return pos.get_prev_sibling()


class ImageTree(urwidtrees.TreeBox):
    def __init__(self, docker_backend, ui):
        tree = TreeBackend(docker_backend, ui)

        # We hide the usual arrow tip and use a customized collapse-icon.
        t = urwidtrees.CollapsibleArrowTree(
            tree,
            arrow_att="tree",  # lines, tip
            icon_collapsed_att="tree",  # +
            icon_expanded_att="tree",  # -
            icon_frame_att="tree",  # [ ]
        )
        super().__init__(t)
