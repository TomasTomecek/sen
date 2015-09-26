import json
import sys
import logging
import datetime

from sen.docker_backend import DockerBackend

import urwid
import humanize


logger = logging.getLogger(__name__)


def exit_on_q(key):
    logging.debug("got %r", key)
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

def image_clicked(*args):
    pass


class DockerImageColumns(urwid.Columns):

    def __init__(self, image_id, widgets):
        self.image_id = image_id
        super(DockerImageColumns, self).__init__(widgets)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

    def get_image_id(self):
        return self.image_id


class DockerImagesListBox(urwid.ListBox):
    def __init__(self, ui):
        body = []
        self.d = DockerBackend()
        self.ui = ui
        for i in self.d.images():
            # # wrap
            # clip - cut overflow
            # any - overflow
            # space - overflow
            image_id = urwid.Text(("image_id", i.image_id[:12]), align="left", wrap="any")
            time = urwid.Text(("image_id", i.display_time_created()), align="left", wrap="any")
            names = urwid.Text(("image_names", i.names or ""), align="left", wrap="clip")
            line = DockerImageColumns(i.image_id, [image_id, names, time])
            body.append(urwid.AttrMap(line, 'image_id', focus_map='reversed'))
        body = urwid.SimpleFocusListWalker(body)
        super(DockerImagesListBox, self).__init__(body)

    def keypress(self, size, key):
        logging.debug("size %r, key %r", size, key)
        # import ipdb ; ipdb.set_trace()
        if key == "i":
            columns_widget = self.get_focus()[0].original_widget
            inspect_data = self.d.inspect_image(columns_widget.get_image_id())

            self.ui.top_widget.original_widget = urwid.Filler(urwid.Text(json.dumps(inspect_data, indent=2)))
            return
        key = super(DockerImagesListBox, self).keypress(size, key)
        return key

class UI():
    def __init__(self):
        self.top_widget = urwid.Padding(DockerImagesListBox(self))
        body = []
        pallete = [
            ('reversed', 'yellow', 'brown'),
            ("image_id", "white", "black"),
            ("image_names", "light red", "black"),
        ]
        self.main_loop = urwid.MainLoop(self.top_widget, palette=pallete, unhandled_input=exit_on_q, handle_mouse=False)

    def run(self):
        self.main_loop.run()

ui = UI()
ui.run()
