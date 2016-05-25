import logging
import threading
import webbrowser
from concurrent.futures.thread import ThreadPoolExecutor

from sen.exceptions import NotifyError
from sen.tui.commands import search, filter
from sen.tui.statusbar import UIFrameWidget
from sen.tui.buffer import LogsBuffer, MainListBuffer, InspectBuffer, HelpBuffer, ImageInfoBuffer, TreeBuffer, \
    ContainerInfoBuffer
from sen.tui.constants import PALLETE
from sen.docker_backend import DockerBackend, DockerImage, DockerContainer

import urwid

from sen.util import log_traceback, OrderedSet

logger = logging.getLogger(__name__)


class UI(urwid.MainLoop):
    def __init__(self):
        self.d = DockerBackend()

        # root widget
        self.mainframe = UIFrameWidget(self, urwid.SolidFill())
        self.buffers = []
        self.buffer_movement_history = OrderedSet()

        self.refresh_lock = threading.Lock()

        # worker for long-running tasks - requests
        self.worker = ThreadPoolExecutor(max_workers=4)
        # worker for quick ui operations
        self.ui_worker = ThreadPoolExecutor(max_workers=2)

        root_widget = urwid.AttrMap(self.mainframe, "root")
        self.main_list_buffer = None  # singleton

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(256)
        screen.register_palette(PALLETE)

        super().__init__(root_widget, screen=screen, event_loop=urwid.AsyncioEventLoop())
        self.handle_mouse = False
        self.current_buffer = None

    def run_in_background(self, task, *args, **kwargs):
        logger.info("running task %r(%s, %s) in background", task, args, kwargs)
        self.worker.submit(task, *args, **kwargs)

    def run_quickly_in_bacakground(self, task, *args, **kwargs):
        logger.info("running a quick task %r(%s, %s) in background", task, args, kwargs)
        self.ui_worker.submit(task, *args, **kwargs)

    def entering_idle(self):
        with self.refresh_lock:
            return super().entering_idle()

    def refresh(self):
        logger.debug("refresh user interface")
        try:
            with self.refresh_lock:
                self.draw_screen()
        except AssertionError:
            logger.warning("application is not running")
            pass

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
        self.buffer_movement_history.append(buffer)
        logger.debug("movement history: %s", self.buffer_movement_history)
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
        self.buffer_movement_history.remove(self.current_buffer)
        self.current_buffer.destroy()
        self.display_buffer(self.buffer_movement_history[-1], True)

    def unhandled_input(self, key):
        logger.debug("unhandled input: %r", key)
        try:
            if key in ('q', 'Q'):
                self.worker.shutdown(wait=False)
                self.ui_worker.shutdown(wait=False)
                raise urwid.ExitMainLoop()
            elif key == "ctrl o":
                self.pick_and_display_buffer(self.current_buffer_index - 1)
            elif key == "ctrl i":
                self.pick_and_display_buffer(self.current_buffer_index + 1)
            elif key == "x":
                self.remove_current_buffer()
            elif key == "/":
                self.prompt("/", search)
            elif key == "f4":
                self.mainframe.prompt("filter ", filter)
            elif key == "n":
                self.current_buffer.find_next()
            elif key == "N":
                self.current_buffer.find_previous()
            elif key in ["h", "?"]:
                self.display_help()
            elif key == "f5":
                self.display_tree()
        except NotifyError as ex:
            self.notify_message(str(ex), level="error")
            logger.error(repr(ex))

    def run(self):
        self.main_list_buffer = MainListBuffer(self.d, self)

        # FIXME: this breaks rendering -- focus is not being displayed correctly
        @log_traceback
        def chain_fcs():
            self.main_list_buffer.refresh(focus_on_top=True)
            self.add_and_display_buffer(self.main_list_buffer, redraw=True)
        self.run_quickly_in_bacakground(chain_fcs)
        super().run()

    def display_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self))

    def display_and_follow_logs(self, docker_container):
        self.add_and_display_buffer(LogsBuffer(docker_container, self, follow=True))

    def inspect(self, docker_object):
        self.add_and_display_buffer(InspectBuffer(docker_object))

    def display_info(self, docker_object):
        if isinstance(docker_object, DockerImage):
            buffer_class = ImageInfoBuffer
        elif isinstance(docker_object, DockerContainer):
            buffer_class = ContainerInfoBuffer
        else:
            self.notify_message("Can't display info for '%s'" % docker_object, level="error")
            logger.error("unable to display info buffer for %r", docker_object)
            return
        try:
            self.add_and_display_buffer(buffer_class(docker_object, self))
        except NotifyError as ex:
            self.notify_message(str(ex), level="error")
            logger.error(repr(ex))

    def open_browser(self, docker_object):
        # NOTE: there's a little delay between container's state running and ready of the application on the port
        if isinstance(docker_object, DockerContainer):
            response = docker_object.inspect().response
            if not response["State"]["Running"] or response["State"]["Paused"]:  # may throw KeyError ?
                logger.info("Container is stopped - no available ports.")
                self.notify_message("Container is not running - no ports are available.")
                return
            try:
                if len(response["NetworkSettings"]["Ports"]) == 0:
                    # I could raise TypeError for not rewriting code below but don't know if it is best practise :)
                    logger.info("No ports available for '%s" % docker_object)
                    self.notify_message("There are no ports available for '%s" % docker_object.short_name, level="info")

                for key in response["NetworkSettings"]["Ports"]:
                    url = "http://" + response["NetworkSettings"]["IPAddress"] + ":" + key.split("/")[0]
                    logger.info(url)
                    webbrowser.open(url)
            except TypeError:
                logger.info("No ports available for '%s" % docker_object)
                self.notify_message("There are no ports available for '%s" % docker_object.short_name, level="info")
        else:
            logger.info("Selected object is not a docker container.")
            self.notify_message("Selected object is not a docker container.", level="info")

    def refresh_main_buffer(self, refresh_buffer=True):
        assert self.main_list_buffer is not None
        if refresh_buffer:
            self.main_list_buffer.refresh()
        self.display_buffer(self.main_list_buffer)

    def display_help(self):
        self.add_and_display_buffer(HelpBuffer())

    def display_tree(self):
        self.add_and_display_buffer(TreeBuffer(self.d, self))

    # FOOTER

    def set_footer(self, widget):
        self.mainframe.set_footer(widget)

    def reload_footer(self):
        self.mainframe.reload_footer()

    def remove_notification_message(self, message):
        self.mainframe.remove_notification_message(message)

    def notify_widget(self, *args, **kwargs):
        self.mainframe.notify_widget(*args, **kwargs)

    def notify_message(self, *args, **kwargs):
        self.mainframe.notify_message(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        self.mainframe.prompt(*args, **kwargs)