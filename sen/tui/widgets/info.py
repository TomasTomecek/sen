"""
Info widgets:
 * display detailed info about an object
"""
import logging

import urwid

from sen.tui.widgets.list.base import VimMovementListBox
from sen.tui.widgets.list.util import get_map, RowWidget
from sen.tui.widgets.table import assemble_rows
from sen.tui.widgets.util import get_basic_image_markup, SelectableText
from sen.util import humanize_bytes


logger = logging.getLogger(__name__)


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
    """
    so we can easily access image and tag
    """
    def __init__(self, docker_image, tag):
        self.docker_image = docker_image
        self.tag = tag
        super().__init__(str(self.tag))


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
            self.walker.append(RowWidget([TagWidget(self.docker_image, n)]))

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

        def getattr_or_notify(o, attr, message):
            try:
                return getattr(o, attr)
            except AttributeError:
                self.ui.notify_message(message, level="error")

        if key == "d":
            img = getattr_or_notify(self.focus.columns.widget_list[0], "docker_image",
                                    "Focused object isn't a docker image!")
            if not img:
                return
            tag = getattr_or_notify(self.focus.columns.widget_list[0], "tag",
                                    "Focused object doesn't have a tag!")
            if not tag:
                return
            try:
                img.remove_tag(tag)  # FIXME: do this async
            except Exception as ex:
                self.ui.notify_message("Can't remove tag '%s': %s" % (tag, ex), level="error")
                return
            self.walker.remove(self.focus)
            return

        key = super().keypress(size, key)
        return key
