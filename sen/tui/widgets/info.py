"""
Info widgets:
 * display detailed info about an object
"""
import logging

import urwid

from sen.tui.widgets.list.util import get_map, RowWidget
from sen.tui.widgets.table import ResponsiveTable, assemble_rows
from sen.util import humanize_bytes
from sen.tui.widgets.list.base import VimMovementListBox
from sen.tui.widgets.util import AdHocAttrMap, get_basic_image_markup

logger = logging.getLogger(__name__)


class SelectableText(AdHocAttrMap):
    def __init__(self, text, maps=None):
        maps = maps or get_map()
        super().__init__(urwid.Text(text, align="left", wrap="clip"), maps)

    @property
    def text(self):
        return self._original_widget.text

    def keypress(self, size, key):
        """ get rid of tback: `AttributeError: 'Text' object has no attribute 'keypress'` """
        return key


class LayerWidget(SelectableText):
    def __init__(self, ui, docker_image, index=0):
        self.ui = ui
        self.docker_image = docker_image
        separator = "└─"
        if index == 0:
            label = [separator]
        else:
            label = [2 * index * " " + separator]
        super().__init__(label + get_basic_image_markup(docker_image))

    def keypress(self, size, key):
        logger.debug("%s %s %s", self.__class__, key, size)
        if key == "enter":
            self.ui.display_image_info(self.docker_image)
            return
        elif key == "i":
            self.ui.inspect(self.docker_image)  # FIXME: do this async
            return
        return key


class TagWidget(SelectableText):
    def __init__(self, ui, docker_image, tag):
        self.ui = ui
        self.docker_image = docker_image
        self.tag = tag
        super().__init__(str(self.tag))

    def keypress(self, size, key):
        logger.debug("%s %s %s", self.__class__, key, size)
        if key == "d":
            self.docker_image.remove_tag(self.tag)  # FIXME: do this async
            # TODO: refresh
            return
        return key


class ImageInfoWidget(VimMovementListBox):
    """
    display info about image
    """
    def __init__(self, ui, docker_image):
        self.ui = ui
        self.docker_image = docker_image

        self.walker = urwid.SimpleFocusListWalker([])

        # self.widgets = []

        self._basic_data()
        self._containers()
        self._image_names()
        self._layers()
        self._labels()

        super().__init__(self.walker)

        self.set_focus(0)  # or assemble list first and then stuff it into walker

    def _basic_data(self):
        data = [
            [SelectableText("Id", maps=get_map("main_list_green")),
             SelectableText(self.docker_image.image_id)],
            [SelectableText("Created", maps=get_map("main_list_green")),
             SelectableText("{0}, {1}".format(self.docker_image.display_formal_time_created(),
                                              self.docker_image.display_time_created()))],
            [SelectableText("Size", maps=get_map("main_list_green")),
             SelectableText(humanize_bytes(self.docker_image.size))],
            [SelectableText("Command", maps=get_map("main_list_green")),
             SelectableText(self.docker_image.container_command)],
        ]
        self.walker.extend(assemble_rows(data))

    def _image_names(self):
        if not self.docker_image.names:
            return
        self.walker.append(RowWidget([SelectableText("")]))
        self.walker.append(RowWidget([SelectableText("Image Names", maps=get_map("main_list_white"))]))
        for n in self.docker_image.names:
            self.walker.append(RowWidget([TagWidget(self.ui, self.docker_image, n)]))

    def _layers(self):
        self.walker.append(RowWidget([SelectableText("")]))
        self.walker.append(RowWidget([SelectableText("Layers", maps=get_map("main_list_white"))]))

        i = self.docker_image
        index = 0
        self.walker.append(RowWidget([LayerWidget(self.ui, self.docker_image, index=index)]))
        while True:
            index += 1
            parent = i.parent_image
            if parent:
                self.walker.append(RowWidget([LayerWidget(self.ui, parent, index=index)]))
                i = parent
            else:
                break

    def _labels(self):
        if not self.docker_image.labels:
            return []
        data = []
        self.walker.append(RowWidget([SelectableText("")]))
        self.walker.append(RowWidget([SelectableText("Labels", maps=get_map("main_list_white"))]))
        for label_key, label_value in self.docker_image.labels.items():
            data.append([SelectableText(label_key, maps=get_map("main_list_green")), SelectableText(label_value)])
        self.walker.extend(assemble_rows(data))

    def _containers(self):
        if not self.docker_image.containers():
            return
        self.walker.append(RowWidget([SelectableText("")]))
        self.walker.append(RowWidget([SelectableText("Containers", maps=get_map("main_list_white"))]))
        for container in self.docker_image.containers():
            self.walker.append(RowWidget([SelectableText(str(container))]))

    def keypress(self, size, key):
        logger.debug("%s, %s", key, size)
        key = super().keypress(size, key)
        return key
