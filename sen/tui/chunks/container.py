"""
Container-specific chunks.
"""

import logging

from sen.tui.widgets.util import SelectableText, get_map


logger = logging.getLogger(__name__)


class ContainerStatusWidget(SelectableText):
    def __init__(self, docker_container):
        markup, attr = get_container_status_markup(docker_container)
        super().__init__(markup, attr)


class ContainerOneLinerWidget(SelectableText):
    def __init__(self, ui, docker_container):
        self.ui = ui
        self.docker_container = docker_container
        super().__init__(get_basic_container_markup(docker_container))


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


def get_container_status_markup(docker_container):
    if docker_container.running:
        attr_map = get_map("main_list_green")
    elif docker_container.exited_well:
        attr_map = get_map("main_list_orange")
    elif docker_container.status_created:
        attr_map = get_map("main_list_yellow")
    else:
        attr_map = get_map("main_list_red")
    return docker_container.status, attr_map


def get_basic_container_markup(docker_container):
    text_markup = [docker_container.short_id, " "]

    markup, attr = get_container_status_markup(docker_container)
    text_markup.append((attr["normal"], markup))

    if docker_container.names:
        text_markup.append(" ")
        text_markup.append(("main_list_lg", docker_container.names[0]))

    return text_markup