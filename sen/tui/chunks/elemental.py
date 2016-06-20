import logging

from sen.docker_backend import DockerImage, DockerContainer
from sen.tui.widgets.list.util import get_time_attr_map

from sen.tui.widgets.util import (
    SelectableText, get_basic_image_markup, get_container_status_markup,
    get_basic_container_markup, get_map
)


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


class ContainerStatusWidget(SelectableText):
    def __init__(self, docker_container):
        markup, attr = get_container_status_markup(docker_container)
        super().__init__(markup, attr)


class ContainerOneLinerWidget(SelectableText):
    def __init__(self, ui, docker_container):
        self.ui = ui
        self.docker_container = docker_container
        super().__init__(get_basic_container_markup(docker_container))


def get_detailed_image_row(docker_image):
    row = []
    image_id = SelectableText(docker_image.short_id, maps=get_map())
    row.append(image_id)

    command = SelectableText(docker_image.command, maps=get_map(defult="main_list_ddg"))
    row.append(command)

    base_image = docker_image.base_image()
    base_image_text = ""
    if base_image:
        base_image_text = base_image.short_name
    base_image_w = SelectableText(base_image_text, maps=get_map())
    row.append(base_image_w)

    time = SelectableText(docker_image.display_time_created(),
                          maps=get_time_attr_map(docker_image.created))
    row.append(time)

    image_names_markup = get_image_names_markup(docker_image)
    # urwid.Text([]) tracebacks
    if image_names_markup:
        image_names = SelectableText(image_names_markup)
    else:
        image_names = SelectableText("")
    row.append(image_names)

    return row


def get_image_names_markup(docker_image):
    text_markup = []
    for n in docker_image.names:
        if n.registry:
            text_markup.append(("main_list_dg", n.registry + "/"))
        if n.namespace and n.repo:
            text_markup.append(("main_list_lg", n.namespace + "/" + n.repo))
        else:
            if n.repo == "<none>":
                text_markup.append(("main_list_dg", n.repo))
            else:
                text_markup.append(("main_list_lg", n.repo))
        if n.tag:
            if n.tag not in ["<none>", "latest"]:
                text_markup.append(("main_list_dg", ":" + n.tag))
        text_markup.append(("main_list_dg", ", "))
    text_markup = text_markup[:-1]
    return text_markup


def get_detailed_container_row(docker_container):
    row = []
    container_id = SelectableText(docker_container.short_id)
    row.append(container_id)

    command = SelectableText(docker_container.command, get_map(defult="main_list_ddg"))
    row.append(command)

    image = SelectableText(docker_container.image_name())
    row.append(image)

    row.append(ContainerStatusWidget(docker_container))

    name = SelectableText(docker_container.short_name)
    row.append(name)

    return row


def get_row(docker_object):
    if isinstance(docker_object, DockerImage):
        return get_detailed_image_row(docker_object)
    elif isinstance(docker_object, DockerContainer):
        return get_detailed_container_row(docker_object)
    else:
        raise Exception("what ")
