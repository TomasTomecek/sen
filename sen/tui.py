import json
import sys
import logging
import datetime
import threading

from sen.docker_backend import DockerBackend, DockerImage, DockerContainer

import urwid
import humanize


logger = logging.getLogger(__name__)


class DockerImageColumns(urwid.Columns):

    def __init__(self, docker_object, widgets):
        self.docker_object = docker_object
        super(DockerImageColumns, self).__init__(widgets)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class ScrollableListBox(urwid.ListBox):
    def __init__(self, text):
        text = urwid.Text(("text", text), align="left", wrap="any")
        body = urwid.SimpleFocusListWalker([text])
        super(ScrollableListBox, self).__init__(body)


class MainListBox(urwid.ListBox):
    def __init__(self, docker_backend, ui):
        self.d = docker_backend
        self.ui = ui
        body = urwid.SimpleFocusListWalker(self._assemble_initial_content())
        super(MainListBox, self).__init__(body)

    def _assemble_initial_content(self):
        widgets = []
        for o in self.d.initial_content():
            line = None
            if isinstance(o, DockerImage):
                image_id = urwid.Text(("image_id", o.image_id[:12]), align="left", wrap="any")
                time = urwid.Text(("image_id", o.display_time_created()), align="left", wrap="any")
                names = urwid.Text(("image_names", o.names or ""), align="left", wrap="clip")
                line = DockerImageColumns(o, [image_id, names, time])
            elif isinstance(o, DockerContainer):
                container_id = urwid.Text(("image_id", o.container_id[:12]), align="left", wrap="any")
                time = urwid.Text(("image_id", o.display_time_created()), align="left", wrap="any")
                name = urwid.Text(("image_names", o.name), align="left", wrap="clip")
                command = urwid.Text(("image_names", o.command), align="left", wrap="clip")
                status = urwid.Text(("image_names", o.status), align="left", wrap="clip")
                line = DockerImageColumns(o, [container_id, command, time, status, name])
            widgets.append(urwid.AttrMap(line, 'image_id', focus_map='reversed'))
        return widgets

    def keypress(self, size, key):
        logger.debug("size %r, key %r", size, key)
        if key == "i":
            docker_object = self.get_focus()[0].original_widget.docker_object
            if isinstance(docker_object, DockerImage):
                inspect_data = self.d.inspect_image(docker_object.image_id)
            elif isinstance(docker_object, DockerContainer):
                inspect_data = self.d.inspect_container(docker_object.container_id)
            else:
                raise RuntimeError("wat")
            rendered_json = json.dumps(inspect_data, indent=2)
            self.ui.add_and_set_main_widget(ScrollableListBox(rendered_json))
            return
        if key == "l":
            docker_object = self.get_focus()[0].original_widget.docker_object
            if isinstance(docker_object, DockerContainer):
                logs_generator = self.d.logs(docker_object.container_id)
                log_texts = []
                walker = urwid.SimpleFocusListWalker(log_texts)
                list_box = urwid.ListBox(walker)
                self.ui.add_and_set_main_widget(list_box)
                def fetch_logs():
                    for line in logs_generator:
                        logger.debug("log line emitted: %r", line)
                        walker.append(urwid.Text(("text", line.strip()), align="left", wrap="any"))
                        walker.set_focus(len(walker) - 1)
                threading.Thread(target=fetch_logs, daemon=True).start()
            return
        key = super(MainListBox, self).keypress(size, key)
        return key


class UI(urwid.MainLoop):
    def __init__(self):
        pallete = [
            ('reversed', 'yellow', 'brown'),
            ("image_id", "white", "black"),
            ("image_names", "light red", "black"),
        ]
        self.d = DockerBackend()
        self.main_list = MainListBox(self.d, self)
        # the padding is placeholder so we can change it easily
        super().__init__(urwid.Padding(self.main_list), palette=pallete)
        self.handle_mouse = False
        self.widgets = []

    def _set_main_widget(self, widget, redraw):
        """
        add provided widget to widget list and display it

        :param widget:
        :return:
        """
        self._widget.original_widget = widget
        if redraw:
            logger.debug("redraw main widget")
            # FIXME: redraw on change, this doesn't work, somehow
            self.draw_screen()

    def add_and_set_main_widget(self, widget, redraw=True):
        """
        add provided widget to widget list and display it

        :param widget:
        :return:
        """
        if widget not in self.widgets:
            logger.debug("adding new widget %r", widget)
            self.widgets.append(widget)
        self._set_main_widget(widget, redraw)

    def pick_main_widget(self, i):
        """
        pick i-th widget from list and display it

        :param i:
        :return:
        """
        if len(self.widgets) == 1:
            return
        else:
            try:
                self._set_main_widget(self.widgets[i], True)
            except IndexError:
                # i > len
                self._set_main_widget(self.widgets[0], True)

    @property
    def current_widget_index(self):
        return self.widgets.index(self._widget.original_widget)

    @property
    def current_widget(self):
        return self._widget.original_widget

    def remove_current_widget(self):
        # don't allow removing main_list
        if self.current_widget == self.main_list:
            logger.warning("you can't remove main list widget")
            return
        self.widgets.remove(self.current_widget)
        # FIXME: we should display last displayed widget here
        self._set_main_widget(self.main_list, True)

    def unhandled_input(self, key):
        logger.debug("got %r", key)
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == "p":
            self.pick_main_widget(self.current_widget_index - 1)
        elif key == "n":
            self.pick_main_widget(self.current_widget_index + 1)
        elif key == "x":
            self.remove_current_widget()

    def run(self):
        self.add_and_set_main_widget(self.main_list, redraw=False)
        super().run()
