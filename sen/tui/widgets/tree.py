import logging

import urwidtrees

from sen.tui.widgets.list.util import RowWidget
from sen.tui.widgets.util import SelectableText
from sen.tui.chunks.image import get_basic_image_markup

logger = logging.getLogger(__name__)


class TreeNodeWidget(SelectableText):
    def __init__(self, ui, docker_image):
        self.ui = ui
        self.docker_image = docker_image
        super().__init__(get_basic_image_markup(docker_image, with_size=True))


class TreeBackend(urwidtrees.Tree):
    # FIXME: rewrite to use SimpleTree instead (for sake of docker-1.10 changes: how does one
    #        index an image with id <missing>
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
    def __init__(self, ui, docker_backend):
        self.ui = ui
        tree = TreeBackend(docker_backend, ui)

        # We hide the usual arrow tip and use a customized collapse-icon.
        t = urwidtrees.ArrowTree(
            tree,
            arrow_att="tree",  # lines, tip
            icon_collapsed_att="tree",  # +
            icon_expanded_att="tree",  # -
            icon_frame_att="tree",  # [ ]
            indent=2,
        )
        super().__init__(t)

    @property
    def focused_docker_object(self):
        image = self.get_focus()[1]
        logger.debug("focused image is %s", image)
        return image

    def focus_first(self):
        self.set_focus(self._tree.root)

    def focus_last(self):
        # taken from alot, thanks pazz!
        logger.debug(next(self._tree.positions()))
        self.set_focus(next(self._tree.positions(reverse=True)))
