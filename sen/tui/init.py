from collections import deque
from functools import partial
import logging
import threading
from sen.exceptions import NotifyError

from sen.tui.buffer import LogsBuffer, MainListBuffer, InspectBuffer, HelpBuffer
from sen.tui.constants import PALLETE, MAIN_LIST_FOCUS
from sen.docker_backend import DockerBackend

import urwid
from sen.tui.widget import AdHocAttrMap

logger = logging.getLogger(__name__)


class UI(urwid.MainLoop):
    def __init__(self):
        self.d = DockerBackend()

        # root widget
        self.mainframe = urwid.Frame(urwid.SolidFill())
        self.status_bar = None
        self.notif_bar = None
        self.status_alarms = deque()
        self.status_alarm_lock = threading.Lock()
        self.status_alarm_is_active = False
        self.prompt_active = False

        root_widget = urwid.AttrMap(self.mainframe, "root")
        self.main_list_buffer = None  # singleton

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
        self.reload_footer()
        if redraw:
            logger.debug("redraw main widget")
            self.refresh()

    def reload_notif_bar(self):
        logger.debug("reload notif bar")
        bottom = []
        if self.notif_bar:
            bottom.append(self.notif_bar)
        bottom.append(self.status_bar)
        self.mainframe.set_footer(urwid.Pile(bottom))

    def reload_footer(self):
        logger.debug("reload footer")
        bottom = []
        if self.notif_bar:
            bottom.append(self.notif_bar)
        self.status_bar = self.build_statusbar()
        bottom.append(self.status_bar)
        self.mainframe.set_footer(urwid.Pile(bottom))

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
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()
            elif key == "ctrl o":
                self.pick_and_display_buffer(self.current_buffer_index - 1)
            elif key == "ctrl i":
                self.pick_and_display_buffer(self.current_buffer_index + 1)
            elif key == "x":
                self.remove_current_buffer()
            elif key == "@":
                self.refresh_main_buffer()
            elif key == "/":
                self.prompt("/")
            elif key == "n":
                self.current_buffer.find_next()
                self.refresh()
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

    def build_statusbar(self):
        """construct and return statusbar widget"""
        columns_list = []

        def add_subwidget(markup, color_attr=None):
            if color_attr is None:
                w = urwid.AttrMap(urwid.Text(markup), "status_text")
            else:
                w = urwid.AttrMap(urwid.Text(markup), color_attr)
            columns_list.append((len(markup), w))

        add_subwidget("Images: ")
        images_count = len(self.d.images)
        if images_count < 10:
            add_subwidget(str(images_count), "status_text_green")
        elif images_count < 50:
            add_subwidget(str(images_count), "status_text_yellow")
        else:
            add_subwidget(str(images_count), "status_text_orange")

        add_subwidget(", Containers: ")
        containers_count = len(self.d.containers)
        if containers_count < 5:
            add_subwidget(str(containers_count), "status_text_green")
        elif containers_count < 30:
            add_subwidget(str(containers_count), "status_text_yellow")
        elif containers_count < 100:
            add_subwidget(str(containers_count), "status_text_orange")
        else:
            add_subwidget(str(containers_count), "status_text_red")

        add_subwidget(", Running: ")
        running_containers = self.d.sorted_containers(sort_by_time=False, stopped=False)
        running_containers_n = len(running_containers)
        add_subwidget(str(running_containers_n),
                      "status_text_green" if running_containers_n > 0 else "status_text")

        try:
            command_name, command_took = self.d.last_command.popleft()
        except IndexError:
            command_name, command_took = None, None
        if command_name and command_took:
            if command_took > 100:
                add_subwidget(", {}() -> ".format(command_name))
                command_took_str = "{:.2f}".format(command_took)
                if command_took < 500:
                    add_subwidget(command_took_str, "status_text_yellow")
                elif command_took < 1000:
                    add_subwidget(command_took_str, "status_text_orange")
                else:
                    command_took_str = "{:.2f}".format(command_took / 1000.0)
                    add_subwidget(command_took_str, "status_text_red")
                    add_subwidget(" s")
                if command_took < 1000:
                    add_subwidget(" ms")

                def reload_footer(*args):
                    self.reload_footer()
                self.append_status_alarm(10, reload_footer)

        text_list = []
        for idx, buffer in enumerate(self.buffers):
            #  #1 [I] fedora #2 [L]
            fmt = "#{idx} [{tag}] {name}"
            markup = fmt.format(idx=idx, tag=buffer.tag, name=buffer.display_name)
            text_list.append((
                "status_box_focus" if buffer == self.current_buffer else "status_box",
                markup,
            ))
            text_list.append(" ")
        text_list = text_list[:-1]

        right_cols = urwid.Text(text_list, align="right")
        columns_list.append(right_cols)
        columns = urwid.Columns(columns_list)
        return urwid.AttrMap(columns, "status")

    def prompt(self, prompt_text):
        """
        prompt for text input.
        """
        oldroot = self.widget
        oldfooter = self.mainframe.get_footer()

        # set up widgets
        leftpart = urwid.Text(prompt_text, align='left')
        editpart = urwid.Edit(multiline=True)

        # build promptwidget
        both = urwid.Columns(
            [
                ('fixed', len(prompt_text), leftpart),
                ('weight', 1, editpart),
            ])
        both = urwid.AttrMap(both, "main_list_dg")

        self.mainframe.set_footer(both)

        self.prompt_active = True

        self.mainframe.set_focus("footer")

        def edited(edit_widget, text_input):
            # FIXME: this function should be somewhere else
            logger.debug("%r %r", edit_widget, text_input)
            if text_input.endswith("\n"):
                # TODO: implement incsearch
                #   - match needs to be highlighted somehow, not with focus though
                self.prompt_active = False
                self.mainframe.set_footer(oldfooter)
                try:
                    self.current_buffer.find_next(text_input[:-1])
                except NotifyError as ex:
                    self.notify(str(ex), level="error")
                    logger.error(repr(ex))
                self.mainframe.set_focus("body")

        urwid.connect_signal(editpart, "change", edited)

    def append_status_alarm(self, in_s, f):
        def chain_f(this_function, callback, loop, *args):
            callback()
            with self.status_alarm_lock:
                try:
                    s, func = self.status_alarms.popleft()
                except IndexError:
                    self.status_alarm_is_active = False
                else:
                    self.set_alarm_in(s, partial(this_function, this_function, func))

        with self.status_alarm_lock:
            if self.status_alarm_is_active:
                self.status_alarms.append((in_s, f))
            else:
                self.status_alarm_is_active = True
                self.set_alarm_in(in_s, partial(chain_f, chain_f, f))

    def notify(self, message, level="info"):
        """
        :param level: str, {info, error}

        opens notification popup.
        """
        msgs = [urwid.AttrMap(urwid.Text(message), "notif_{}".format(level))]

        # stack errors, don't overwrite them
        if not self.notif_bar:
            self.notif_bar = urwid.Pile(msgs)
        else:
            newpile = self.notif_bar.widget_list + msgs
            self.notif_bar = urwid.Pile(newpile)

        self.reload_notif_bar()

        def clear(*args):
            newpile = self.notif_bar.widget_list
            for l in msgs:
                if l in newpile:
                    newpile.remove(l)
            if newpile:
                self.notif_bar = urwid.Pile(newpile)
            else:
                self.notif_bar = None
            self.reload_notif_bar()

        self.set_alarm_in(10, clear)
