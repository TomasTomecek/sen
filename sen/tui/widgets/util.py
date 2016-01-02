import logging

import urwid

from sen.docker_backend import RootImage
from sen.tui.constants import MAIN_LIST_FOCUS

logger = logging.getLogger(__name__)


class AdHocAttrMap(urwid.AttrMap):
    """
    Ad-hoc attr map change

    taken from https://github.com/pazz/alot/
    """
    def __init__(self, w, maps, init_map='normal'):
        self.maps = maps
        urwid.AttrMap.__init__(self, w, maps[init_map])
        if isinstance(w, urwid.Text):
            self.attrs = [x[0] for x in self.original_widget.get_text()[1]]

    def set_map(self, attrstring):
        attr_map = {None: self.maps[attrstring]}

        # for urwid.Text only: do hovering for all markups in the widget
        if isinstance(self.original_widget, urwid.Text):
            if attrstring == "normal":
                for a in self.attrs:
                    attr_map[self.maps["focus"]] = a
            elif attrstring == "focus":
                for a in self.attrs:
                    attr_map[a] = self.maps["focus"]
        self.set_attr_map(attr_map)


def get_basic_image_markup(docker_image):
    if isinstance(docker_image, RootImage):
        return [str(docker_image)]

    text_markup = [docker_image.short_id]

    if docker_image.names:
        text_markup.append(" ")
        text_markup.append(("main_list_lg", docker_image.names[0].to_str()))

    text_markup.append(" ")
    text_markup.append(("main_list_ddg", docker_image.container_command))

    return text_markup
