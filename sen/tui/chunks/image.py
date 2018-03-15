"""
Image specific chunks.
"""

import logging

from sen.util import humanize_bytes

from sen.docker_backend import RootImage
from sen.tui.widgets.list.util import get_time_attr_map
from sen.tui.widgets.util import SelectableText, get_map


logger = logging.getLogger(__name__)


class LayerWidget(SelectableText):
    def __init__(self, ui, docker_image, index=None):
        self.ui = ui
        self.docker_image = docker_image
        label = []
        logger.debug("creating layer widget for %s", docker_image)
        if index is not None:
            separator = "└─"
            if index == 0:
                label = [separator]
            else:
                label = [2 * index * " " + separator]
        super().__init__(label + get_basic_image_markup(docker_image, with_size=True))


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


def get_basic_image_markup(docker_image, with_size=False):
    if isinstance(docker_image, RootImage):
        return [str(docker_image)]

    text_markup = [docker_image.short_id]

    if docker_image.names:
        text_markup.append(" ")
        text_markup.append(("main_list_lg", docker_image.names[0].to_str()))

    c = docker_image.container_command or docker_image.comment
    if c:
        text_markup.append(" ")
        text_markup.append(("main_list_ddg", c))

    if with_size:
        text_markup.append(" ")
        text_markup.append(("main_list_ddg", "(%s)" % humanize_bytes(docker_image.total_size)))

    return text_markup
