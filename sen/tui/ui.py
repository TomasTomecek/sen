"""
This is a framework for terminal interfaces built on top of urwid.Frame.

It must NOT contain any application specific code.
"""
import logging
import threading
from concurrent.futures.thread import ThreadPoolExecutor

import urwid

from sen.exceptions import NotifyError
from sen.tui.commands.base import (
    FrontendPriority, BackendPriority,
    SameThreadPriority, KeyNotMapped
)
from sen.tui.constants import CLEAR_NOTIF_BAR_MESSAGE_IN
from sen.tui.widgets.util import ThreadSafeFrame
from sen.util import log_traceback, OrderedSet


logger = logging.getLogger(__name__)


class ConcurrencyMixin:
    def __init__(self):
        # worker for long-running tasks - requests
        self.worker = ThreadPoolExecutor(max_workers=4)
        # worker for quick ui operations
        self.ui_worker = ThreadPoolExecutor(max_workers=2)

    @staticmethod
    def _run(worker, f, *args, **kwargs):
        # TODO: do another wrapper to wrap notify exceptions and show them
        f = log_traceback(f)
        worker.submit(f, *args, **kwargs)

    def run_in_background(self, task, *args, **kwargs):
        logger.info("running task %r(%s, %s) in background", task, args, kwargs)
        self._run(self.worker, task, *args, **kwargs)

    def run_quickly_in_background(self, task, *args, **kwargs):
        logger.info("running a quick task %r(%s, %s) in background", task, args, kwargs)
        self._run(self.ui_worker, task, *args, **kwargs)


class UI(ThreadSafeFrame, ConcurrencyMixin):
    """
    handles all UI-specific code
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # widget -> message or None
        self.widget_message_dict = {}
        # message -> widget
        self.message_widget_dict = {}
        self.status_bar = None
        self.prompt_bar = None

        # lock when managing notifications:
        #  * when accessing self.notification_*
        #  * when accessing widgets
        # and most importantly, remember, locking is voodoo
        self.notifications_lock = threading.RLock()

        # populated when loop and UI are instantiated
        self.loop = None
        self.commander = None

        self.buffers = []
        self.buffer_movement_history = OrderedSet()

        self.main_list_buffer = None  # singleton

        self.current_buffer = None

    def refresh(self):
        self.loop.refresh()

    def quit(self):
        """
        This could be called from another thread, so let's do this via alarm
        """
        def q(*args):
            raise urwid.ExitMainLoop()
        self.worker.shutdown(wait=False)
        self.ui_worker.shutdown(wait=False)
        self.loop.set_alarm_in(0, q)

    # FIXME: move these to separate mixin
    def _set_main_widget(self, widget, redraw):
        """
        add provided widget to widget list and display it

        :param widget:
        :return:
        """
        self.set_body(widget)
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
        logger.debug("display buffer %r", buffer)
        self.buffer_movement_history.append(buffer)
        self.current_buffer = buffer
        self._set_main_widget(buffer.widget, redraw=redraw)

    def add_and_display_buffer(self, buffer, redraw=True):
        """
        add provided buffer to buffer list and display it

        :param buffer:
        :return:
        """
        # FIXME: some buffers have arguments, do a proper comparison -- override __eq__
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

    def remove_current_buffer(self, close_if_no_buffer=False):
        if len(self.buffers) == 1 and not close_if_no_buffer:
            return
        self.buffers.remove(self.current_buffer)
        self.buffer_movement_history.remove(self.current_buffer)
        self.current_buffer.destroy()
        if len(self.buffers) > 0:
            self.display_buffer(self.buffer_movement_history[-1], True)
        return len(self.buffers)

    def reload_footer(self, refresh=True, rebuild_statusbar=True):
        logger.debug("reload footer")
        footer = list(self.widget_message_dict.keys())
        if self.prompt_bar:
            footer.append(self.prompt_bar)
        else:
            if rebuild_statusbar or self.status_bar is None:
                self.status_bar = self.build_statusbar()
            footer.append(self.status_bar)
        # logger.debug(footer)
        self.set_footer(urwid.Pile(footer))
        if refresh:
            self.loop.refresh()

    def build_statusbar(self):
        """construct and return statusbar widget"""
        if self.prompt_bar:
            logger.info("prompt is active, won't build status bar")
            return
        try:
            left_widgets = self.current_buffer.build_status_bar() or []
        except AttributeError:
            left_widgets = []
        text_list = []
        # FIXME: this code should be placed in buffer
        # TODO: display current active worker threads
        for idx, buffer in enumerate(self.buffers):
            #  #1 [I] fedora #2 [L]
            fmt = "#{idx} [{name}]"
            markup = fmt.format(idx=idx, name=buffer.display_name)
            text_list.append((
                "status_box_focus" if buffer == self.current_buffer else "status_box",
                markup,
            ))
            text_list.append(" ")
        text_list = text_list[:-1]

        if text_list:
            buffer_text = urwid.Text(text_list, align="right")
        else:
            buffer_text = urwid.Text("", align="right")
        columns = urwid.Columns(left_widgets + [buffer_text])
        return urwid.AttrMap(columns, "status")

    def remove_notification_message(self, message):
        logger.debug("requested remove of message %r from notif bar", message)
        with self.notifications_lock:
            try:
                w = self.message_widget_dict[message]
            except KeyError:
                logger.warning("there is no notification %r displayed: %s",
                               message, self.message_widget_dict)
                return
            else:
                logger.debug("remove widget %r from new pile", w)
                del self.widget_message_dict[w]
                del self.message_widget_dict[message]
        self.reload_footer(rebuild_statusbar=False)

    def remove_widget(self, widget, message=None):
        logger.debug("remove widget %r from notif bar", widget)
        with self.notifications_lock:
            try:
                del self.widget_message_dict[widget]
            except KeyError:
                logger.info("widget %s was already removed", widget)
                return
            if message:
                del self.message_widget_dict[message]
        self.reload_footer(rebuild_statusbar=False)

    def notify_message(self, message, level="info", clear_if_dupl=True,
                       clear_in=CLEAR_NOTIF_BAR_MESSAGE_IN):
        """
        :param message, str
        :param level: str, {info, error}
        :param clear_if_dupl: bool, if True, don't display the notification again
        :param clear_in: seconds, remove the notificantion after some time

        opens notification popup.
        """
        with self.notifications_lock:
            if clear_if_dupl and message in self.message_widget_dict.keys():
                logger.debug("notification %r is already displayed", message)
                return
            logger.debug("display notification %r", message)
            widget = urwid.AttrMap(urwid.Text(message), "notif_{}".format(level))
        return self.notify_widget(widget, message=message, clear_in=clear_in)

    def notify_widget(self, widget, message=None, clear_in=CLEAR_NOTIF_BAR_MESSAGE_IN):
        """
        opens notification popup.

        :param widget: instance of Widget, widget to display
        :param message: str, message to remove from list of notifications
        :param clear_in: int, time seconds when notification should be removed
        """

        @log_traceback
        def clear_notification(*args, **kwargs):
            # the point here is the log_traceback
            self.remove_widget(widget, message=message)

        if not widget:
            return

        logger.debug("display notification widget %s", widget)

        with self.notifications_lock:
            self.widget_message_dict[widget] = message
            if message:
                self.message_widget_dict[message] = widget

        self.reload_footer(rebuild_statusbar=False)
        self.loop.set_alarm_in(clear_in, clear_notification)

        return widget

    def run_command(self, command_input, queue=None, **kwargs):
        kwargs["buffer"] = self.current_buffer
        command = self.commander.get_command(command_input, **kwargs)
        if command is None:
            return
        if queue is None:
            queue = command.priority
        if isinstance(queue, FrontendPriority):
            self.run_quickly_in_background(command.run)
        elif isinstance(queue, BackendPriority):
            self.run_in_background(command.run)
        elif isinstance(queue, SameThreadPriority):
            logger.info("running command %s", command)
            try:
                command.run()
            except NotifyError as ex:
                self.notify_message(str(ex), level="error")
                logger.error(repr(ex))
        else:
            raise RuntimeError("command %s doesn't have any priority: %s %s" %
                               (command_input, command.priority, FrontendPriority))

    def run_command_by_key(self, key, size, **kwargs):
        command_input = self.commander.get_command_input_by_key(key)
        self.run_command(command_input, size=size, **kwargs)

    def keypress(self, size, key):
        logger.debug("%s keypress %r", self.__class__.__name__, key)

        # we should pass the key to header, body, footer first so it's consumed in e.g. statusbar
        key = super().keypress(size, key)
        if key is None:
            logger.info("key was consumed by frame components")
            return

        logger.info("key was not consumed by frame components")

        focused_docker_object = None
        selected_widget = getattr(self.current_buffer, "widget", None)
        if selected_widget:
            focused_docker_object = getattr(self.current_buffer.widget, "focused_docker_object", None)
            logger.debug("focused docker object is %s", focused_docker_object)
        try:
            self.run_command_by_key(
                key,
                docker_object=focused_docker_object,
                size=size
            )
        except KeyNotMapped as ex:
            super_class = ThreadSafeFrame
            logger.debug("calling: %s.keypress(%s, %s)", super_class, size, key)
            # TODO: up/down doesn't do anything if len(lines) < screen height, that's confusing
            key = super_class.keypress(self, size, key)
            if key:
                self.notify_message(str(ex), level="error")
            logger.debug("was key handled? %s", "yes" if key is None else "no")
            return key
        return


class ThreadSafeLoop(urwid.MainLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_lock = threading.RLock()

    def entering_idle(self):
        with self.refresh_lock:
            return super().entering_idle()

    def refresh(self):
        """
        explicitely refresh user interface; useful when changing widgets dynamically
        """
        logger.debug("refresh user interface")
        try:
            with self.refresh_lock:
                self.draw_screen()
        except AssertionError:
            logger.warning("application is not running")
            pass


def get_app_in_loop(pallete):
    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(256)
    screen.register_palette(pallete)

    ui = UI(urwid.SolidFill())
    decorated_ui = urwid.AttrMap(ui, "root")
    loop = ThreadSafeLoop(decorated_ui, screen=screen, event_loop=urwid.AsyncioEventLoop(),
                          handle_mouse=False)
    ui.loop = loop

    return loop, ui
