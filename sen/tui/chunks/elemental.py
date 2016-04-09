import logging

from sen.tui.widgets.util import SelectableText, get_basic_image_markup, get_container_status_markup, \
    get_basic_container_markup

logger = logging.getLogger(__name__)


class LayerWidget(SelectableText):
    def __init__(self, ui, docker_image, index=None):
        self.ui = ui
        self.docker_image = docker_image
        label = []
        if index is not None:
            separator = "└─"
            if index == 0:
                label = [separator]
            else:
                label = [2 * index * " " + separator]
        super().__init__(label + get_basic_image_markup(docker_image))

    def keypress(self, size, key):
        logger.debug("%s %s %s", self.__class__, key, size)
        if key == "enter":
            self.ui.display_info(self.docker_image)
            return
        elif key == "i":
            self.ui.inspect(self.docker_image)  # FIXME: do this async
            return
        return key


class ContainerStatusWidget(SelectableText):
    def __init__(self, docker_container):
        markup, attr = get_container_status_markup(docker_container)
        super().__init__(markup, attr)


class ContainerOneLinerWidget(SelectableText):
    def __init__(self, ui, docker_container):
        self.ui = ui
        self.docker_container = docker_container
        super().__init__(get_basic_container_markup(docker_container))

    def keypress(self, size, key):
        logger.debug("%s %s %s", self.__class__, key, size)
        if key == "enter":
            self.ui.display_info(self.docker_container)
            return
        elif key == "i":
            self.ui.inspect(self.docker_container)  # FIXME: do this async
            return
        return key
