import logging

from sen.tui.buffer import LogsBuffer, MainListBuffer, InspectBuffer
from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend

import urwid


logger = logging.getLogger(__name__)


class UI(urwid.MainLoop):
    def __init__(self):
        self.d = DockerBackend()

        # root widget
        self.mainframe = urwid.Frame(urwid.SolidFill())
        root_widget = urwid.AttrMap(self.mainframe, "root")

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(256)
        screen.register_palette(PALLETE)

        super().__init__(root_widget, screen=screen)
        self.handle_mouse = False
        self.current_buffer = None
        self.buffers = []

    def refresh(self):
        self.draw_screen()

    def _set_main_widget(self, widget, redraw):
        """
        add provided widget to widget list and display it

        :param widget:
        :return:
        """
        self.mainframe.set_body(widget)
        self.mainframe.set_footer(self.build_statusbar())
        if redraw:
            logger.debug("redraw main widget")
            self.refresh()

    def display_buffer(self, buffer, redraw=True):
        """
        display provided buffer

        :param buffer:
        :return:
        """
        self.current_buffer = buffer
        self._set_main_widget(buffer.widget, redraw=redraw)

    def add_and_display_buffer(self, buffer, redraw=True):
        """
        add provided buffer to buffer list and display it

        :param buffer:
        :return:
        """
        if buffer not in self.buffers:
            logger.debug("adding new buffer {!r}".format(buffer))
            self.buffers.append(buffer)
        self.display_buffer(buffer, redraw=redraw)

    def pick_and_display_buffer(self, i):
        """
        pick i-th buffer from list and display it

        :param i: int
        :return: None
        """
        if len(self.buffers) == 1:
            # we don't need to display anything
            # listing is already displayed
            return
        else:
            try:
                self.display_buffer(self.buffers[i])
            except IndexError:
                # i > len
                self.display_buffer(self.buffers[0])

    @property
    def current_buffer_index(self):
        return self.buffers.index(self.current_buffer)

    def remove_current_buffer(self):
        # don't allow removing main_list
        if isinstance(self.current_buffer, MainListBuffer):
            logger.warning("you can't remove main list widget")
            return
        self.buffers.remove(self.current_buffer)
        self.current_buffer.destroy()
        # FIXME: we should display last displayed widget here
        self.display_buffer(self.buffers[0], True)

    def unhandled_input(self, key):
        logger.debug("got %r", key)
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == "p":
            self.pick_and_display_buffer(self.current_buffer_index - 1)
        elif key == "n":
            self.pick_and_display_buffer(self.current_buffer_index + 1)
        elif key == "x":
            self.remove_current_buffer()

    def run(self):
        main_list = MainListBuffer(self.d, self)
        self.add_and_display_buffer(main_list, redraw=False)
        super().run()

    def display_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self))

    def inspect(self, docker_object):
        self.add_and_display_buffer(InspectBuffer(docker_object))

    def build_statusbar(self):
        """construct and return statusbar widget"""
        lefttxt = ("Images: {images}, Containers: {all_containers},"
                   " Running: {running_containers}, {last_command}() -> {last_command_took:f} ms".
        format(
            last_command=self.d.last_command,  # these gotta be first
            last_command_took=self.d.last_command_took,
            images=len(self.d.images(cached=True, sort_by_time=False)),
            all_containers=len(self.d.containers(cached=True, sort_by_time=False)),
            running_containers=len(self.d.containers(cached=True, sort_by_time=False,
                                                     stopped=False)),
        ))
        t = []
        for idx, buffer in enumerate(self.buffers):
            fmt = "[{}] {}"
            if buffer == self.current_buffer:
                fmt += "*"
            t.append(fmt.format(idx, buffer.display_name))
        righttxt = " ".join(t)

        footerleft = urwid.Text(lefttxt, align='left')

        footerright = urwid.Text(righttxt, align='right')
        columns = urwid.Columns([
            footerleft,
            ('fixed', len(righttxt), footerright)])
        return urwid.AttrMap(columns, "default")
