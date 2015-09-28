import json
import logging
import threading

import urwid

from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend, DockerImage, DockerContainer
from sen.tui.main_list import MainListBox

logger = logging.getLogger(__name__)


class UI(urwid.MainLoop):
    def __init__(self):
        self.d = DockerBackend()
        self.main_list = MainListBox(self.d, self)

        # root widget
        self.mainframe = urwid.Frame(urwid.SolidFill())
        root_widget = urwid.AttrMap(self.mainframe, "root")

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(256)
        screen.register_palette(PALLETE)

        super().__init__(root_widget, screen=screen)
        self.handle_mouse = False
        self.widgets = []

    def _set_main_widget(self, widget, redraw):
        """
        add provided widget to widget list and display it

        :param widget:
        :return:
        """
        self.mainframe.set_body(widget)
        # self._widget.original_widget = widget
        if redraw:
        #    logger.debug("redraw main widget")
        #    # FIXME: redraw on change, this doesn't work, somehow
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
        return self.widgets.index(self.current_widget)

    @property
    def current_widget(self):
        return self.mainframe.get_body()

    def remove_current_widget(self):
        # don't allow removing main_list
        if self.current_widget == self.main_list:
            logger.warning("you can't remove main list widget")
            return
        self.widgets.remove(self.current_widget)
        destroy_method = getattr(self.current_widget, "destroy", None)
        if destroy_method:
            destroy_method()
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
