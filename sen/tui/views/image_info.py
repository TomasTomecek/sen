import logging

import urwid

from sen.docker_backend import RootImage
from sen.tui.chunks.container import ContainerOneLinerWidget
from sen.tui.chunks.image import LayerWidget
from sen.tui.views.base import View
from sen.tui.widgets.list.base import WidgetBase
from sen.tui.widgets.list.util import RowWidget
from sen.tui.widgets.table import assemble_rows
from sen.tui.widgets.util import SelectableText, get_map
from sen.util import humanize_bytes


logger = logging.getLogger(__name__)


class TagWidget(SelectableText):
    """
    so we can easily access image and tag
    """
    def __init__(self, docker_image, tag):
        self.docker_image = docker_image
        self.tag = tag
        super().__init__(str(self.tag))


class ImageInfoWidget(WidgetBase, View):
    """
    display info about image
    """
    def __init__(self, ui, docker_image):
        self.walker = urwid.SimpleFocusListWalker([])
        super().__init__(ui, self.walker)

        self.docker_image = docker_image

    def refresh(self):
        self.docker_image.refresh()
        self.walker.clear()
        self._basic_data()
        self._containers()
        self._image_names()
        self._layers()
        self._labels()
        self.set_focus(0)

    @property
    def focused_docker_object(self):
        # TODO: enable removing image names
        try:
            return self.focus.columns.widget_list[0].docker_container
        except AttributeError:
            try:
                return self.focus.columns.widget_list[0].docker_image
            except AttributeError:
                return None

    def _basic_data(self):
        data = [
            [SelectableText("Id", maps=get_map("main_list_green")),
             SelectableText(self.docker_image.image_id)],
            [SelectableText("Created", maps=get_map("main_list_green")),
             SelectableText("{0}, {1}".format(self.docker_image.display_formal_time_created(),
                                              self.docker_image.display_time_created()))],
            [SelectableText("Size", maps=get_map("main_list_green")),
             SelectableText(humanize_bytes(self.docker_image.total_size))],
        ]
        if self.docker_image.unique_size:
            data.append(
                [SelectableText("Unique Size", maps=get_map("main_list_green")),
                 SelectableText(humanize_bytes(self.docker_image.unique_size))])
        if self.docker_image.shared_size:
            data.append(
                [SelectableText("Shared Size", maps=get_map("main_list_green")),
                 SelectableText(humanize_bytes(self.docker_image.shared_size))])
        data.append([SelectableText("Command", maps=get_map("main_list_green")),
                     SelectableText(self.docker_image.container_command)])
        self.walker.extend(assemble_rows(data, ignore_columns=[1]))

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
        parent = i.parent_image
        layers = self.docker_image.layers
        index = 0

        if isinstance(parent, RootImage) and len(layers) > 0:  # pulled image, docker 1.10+
            for image in layers:
                self.walker.append(
                    RowWidget([LayerWidget(self.ui, image, index=index)])
                )
                index += 1
        else:
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
        self.walker.extend(assemble_rows(data, ignore_columns=[1]))

    def _containers(self):
        if not self.docker_image.containers():
            return
        self.walker.append(RowWidget([SelectableText("")]))
        self.walker.append(RowWidget([SelectableText("Containers", maps=get_map("main_list_white"))]))
        for container in self.docker_image.containers():
            self.walker.append(RowWidget([ContainerOneLinerWidget(self.ui, container)]))
