import logging
from concurrent.futures.thread import ThreadPoolExecutor

from sen.exceptions import NotifyError
from sen.tui.statusbar import Footer
from sen.tui.buffer import LogsBuffer, MainListBuffer, InspectBuffer, HelpBuffer
from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend

import urwid


logger = logging.getLogger(__name__)


class UI(urwid.MainLoop):
    def __init__(self):
        self.d = DockerBackend()

        # root widget
        self.mainframe = urwid.Frame(urwid.SolidFill())
        self.footer = Footer(self)

        self.prompt_active = False

        self.executor = ThreadPoolExecutor(max_workers=4)

        root_widget = urwid.AttrMap(self.mainframe, "root")
        self.main_list_buffer = None  # singleton

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(256)
        screen.register_palette(PALLETE)

        super().__init__(root_widget, screen=screen)
        self.handle_mouse = False
        self.current_buffer = None
        self.buffers = []

    def run_in_background(self, task, *args, **kwargs):
        logger.info("running task %r(%s, %s) in background", task, args, kwargs)
        self.executor.submit(task, *args, **kwargs)

    def refresh(self):
        self.draw_screen()

    def _set_main_widget(self, widget, redraw):
        """
        add provided widget to widget list and display it

        :param widget:
        :return:
        """
        self.mainframe.set_body(widget)
        self.reload_footer()
        if redraw:
            logger.debug("redraw main widget")
            self.refresh()

    def display_buffer(self, buffer, redraw=True):
        """
        display provided buffer

        :param buffer: Buffer
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
        logger.debug("unhandled input: %r", key)
        try:
            if self.prompt_active:
                return
            elif key in ('q', 'Q'):
                raise urwid.ExitMainLoop()
            elif key == "ctrl o":
                self.pick_and_display_buffer(self.current_buffer_index - 1)
            elif key == "ctrl i":
                self.pick_and_display_buffer(self.current_buffer_index + 1)
            elif key == "x":
                self.remove_current_buffer()
            elif key == "@":
                self.run_in_background(self.refresh_main_buffer)
            elif key == "/":
                self.prompt("/")
            elif key == "n":
                self.current_buffer.find_next()
            elif key == "N":
                self.current_buffer.find_previous()
            elif key in ["h", "?"]:
                self.display_help()
        except NotifyError as ex:
            self.notify(str(ex), level="error")
            logger.error(repr(ex))

    def run(self):
        self.main_list_buffer = MainListBuffer(self.d, self)
        self.run_in_background(self.main_list_buffer.refresh, focus_on_top=True)
        self.add_and_display_buffer(self.main_list_buffer, redraw=False)
        super().run()

    def display_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self))

    def display_and_follow_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self, follow=True))

    def inspect(self, docker_object):
        self.add_and_display_buffer(InspectBuffer(docker_object))

    def refresh_main_buffer(self, refresh_buffer=True):
        assert self.main_list_buffer is not None
        if refresh_buffer:
            self.main_list_buffer.refresh()
        self.display_buffer(self.main_list_buffer)

    def display_help(self):
        self.add_and_display_buffer(HelpBuffer())

    # FOOTER

    def set_footer(self, widget):
        self.mainframe.set_footer(widget)

    def reload_footer(self):
        self.footer.reload_footer()

    def notify_widget(self, *args, **kwargs):
        self.footer.notify_widget(*args, **kwargs)

    def notify_message(self, *args, **kwargs):
        self.footer.notify_message(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        self.footer.prompt(*args, **kwargs)