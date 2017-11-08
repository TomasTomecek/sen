"""
Container-specific chunks.
"""

import logging

from sen.tui.widgets.util import SelectableText, get_map


logger = logging.getLogger(__name__)


class ContainerStatusWidget(SelectableText):
    def __init__(self, docker_container, nice_status=True):
        markup, attr = get_container_status_markup(docker_container, nice_status=nice_status)
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

    commands = docker_container.command.split("\n")
    command_str = commands[0]
    if len(commands) > 0:
        command_str += "..."
    command = SelectableText(command_str, get_map(defult="main_list_ddg"))
    row.append(command)

    image = SelectableText(docker_container.image_name())
    row.append(image)

    row.append(ContainerStatusWidget(docker_container))

    name = SelectableText(docker_container.short_name)
    row.append(name)

    return row


def get_container_status_markup(docker_container, nice_status=True):
    if docker_container.running:
        attr_map = get_map("main_list_green")
    elif docker_container.status_created:
        attr_map = get_map("main_list_yellow")
    elif docker_container.exited_well:
        attr_map = get_map("main_list_orange")
    else:
        attr_map = get_map("main_list_red")
    if nice_status:
        return docker_container.nice_status, attr_map
    else:
        return docker_container.simple_status_cap, attr_map


def get_basic_container_markup(docker_container):
    text_markup = [docker_container.short_id, " "]

    markup, attr = get_container_status_markup(docker_container)
    text_markup.append((attr["normal"], markup))

    if docker_container.names:
        text_markup.append(" ")
        text_markup.append(("main_list_lg", docker_container.names[0]))

    return text_markup