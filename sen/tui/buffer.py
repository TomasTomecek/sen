import logging

from sen.docker_backend import DockerContainer, RootImage
from sen.exceptions import NotifyError
from sen.tui.commands.base import Command
from sen.tui.views.disk_usage import DfBufferView
from sen.tui.views.help import HelpBufferView, HelpCommandView
from sen.tui.views.main import MainListBox
from sen.tui.views.image_info import ImageInfoWidget
from sen.tui.views.container_info import ContainerInfoView
from sen.tui.widgets.list.common import AsyncScrollableListBox, ScrollableListBox
from sen.tui.widgets.list.util import get_operation_notify_widget
from sen.tui.widgets.tree import ImageTree


logger = logging.getLogger(__name__)


class Buffer:
    """
    base buffer class
    """
    name = None  # unique identifier
    description = None  # for help
    display_name = None  # display in status bar
    widget = None  # display this in main frame

    # global keybinds which will be available in every buffer
    global_keybinds = {
        # navigation
        "home": "navigate-top",
        "gg": "navigate-top",
        "end": "navigate-bottom",
        "G": "navigate-bottom",
        "down": "navigate-down",
        "j": "navigate-down",
        "up": "navigate-up",
        "k": "navigate-up",
        "ctrl d": "navigate-downwards",
        "ctrl u": "navigate-upwards",

        # UI
        ":": "prompt",
        "/": "prompt prompt-text=\"\" initial-text=\"/\"",
        "n": "search-next",
        "N": "search-previous",
        "f4": "prompt initial-text=\"filter \"",
        "x": "kill-buffer",
        "q": "kill-buffer quit-if-no-buffer",
        "ctrl i": "select-next-buffer",
        "ctrl o": "select-previous-buffer",
        "h": "help",
        "?": "help",
        "f5": "layers",
    }

    # buffer specific keybinds
    keybinds = {}

    def __init__(self):
        logger.debug("creating buffer %r", self)
        self._keybinds = None  # cache
        self.refresh()

    def __repr__(self):
        return "{}(name={!r}, widget={!r})".format(
            self.__class__.__name__, self.display_name, self.widget)

    def destroy(self):
        destroy_method = getattr(self.widget, "destroy", None)
        if destroy_method:
            destroy_method()

    def find_previous(self, s=None):
        logger.debug("searching next %r in %r", s, self.__class__.__name__)
        try:
            self.widget.find_previous(s)
        except AttributeError as ex:
            logger.debug(repr(ex))
            raise NotifyError("Can't search in this buffer.")

    def find_next(self, s=None):
        logger.debug("searching next %r in %r", s, self.__class__.__name__)
        try:
            self.widget.find_next(s)
        except AttributeError as ex:
            logger.debug(repr(ex))
            raise NotifyError("Can't search in this buffer.")

    def build_status_bar(self):
        status_bar = getattr(self.widget, "status_bar", None)
        if status_bar:
            return status_bar()

    def filter(self, s):
        logger.debug("filter widget %r with query %r", self.widget, s)
        self.widget.filter(s)

    def get_keybinds(self):
        if self._keybinds is None:
            self._keybinds = {}
            self._keybinds.update(self.global_keybinds)
            self._keybinds.update(self.keybinds)
        return self._keybinds

    def refresh(self):
        refresh_func = getattr(self.widget, "refresh", None)
        if refresh_func:
            logger.info("refreshing widget %s", self.widget)
            refresh_func()

    def process_realtime_event(self, event):
        logger.info("buffer %s doesn't process realtime events", self)
        return


class ImageInfoBuffer(Buffer):
    description = "Dashboard for information about selected image.\n" + \
                  "You can run command `df` to get more detailed info about disk usage."
    keybinds = {
        "enter": "display-info",
        "d": "rm",
        "i": "inspect",
        "@": "refresh",
    }

    def __init__(self, docker_image, ui):
        """
        :param docker_image:
        :param ui: ui object so we refresh
        """
        if isinstance(docker_image, RootImage):
            raise NotifyError("Image \"scratch\" doesn't provide any more information.")
        if docker_image.image_id == "<missing>":
            raise NotifyError("This image (layer) is not available due to changes in docker-1.10 "
                              "image representation.")
        self.docker_image = docker_image
        self.display_name = docker_image.short_name
        self.widget = ImageInfoWidget(ui, docker_image)
        super().__init__()

    def process_realtime_event(self, event):
        if event.get("id", None) == self.docker_image.object_id:
            self.widget.refresh()


class ContainerInfoBuffer(Buffer):
    description = "Detailed info about selected container presented in a slick dashboard."
    keybinds = {
        "enter": "display-info",
        "@": "refresh",
        "i": "inspect",
    }

    def __init__(self, docker_container, ui):
        """
        :param docker_container:
        :param ui: ui object so we refresh
        """
        self.docker_container = docker_container
        self.display_name = docker_container.short_name
        self.widget = ContainerInfoView(ui, docker_container)
        super().__init__()

    def process_realtime_event(self, event):
        action = event.get("Action", None)
        if action == "top":
            return
        if event.get("id", None) == self.docker_container.object_id:
            self.widget.refresh()


class TreeBuffer(Buffer):
    display_name = "Layers"
    description = "Tree view of all layers available on your docker engine."
    keybinds = {
        "enter": "display-info",
    }

    def __init__(self, ui, docker_backend):
        self.widget = ImageTree(ui, docker_backend)
        super().__init__()


class MainListBuffer(Buffer):
    display_name = "Listing"
    description = "List of all known docker images and containers display in a single list"
    keybinds = {
        "d": "rm",
        "D": "rm -f",
        "s": "start",
        "t": "stop",
        "r": "restart",
        "X": "kill",
        "p": "pause",
        "u": "unpause",
        "enter": "display-info",
        "b": "open-browser",
        "l": "logs",
        "f": "logs -f",
        "i": "inspect",
        "!": "toggle-live-updates",  # TODO: rfe: move to global so this affects every buffer
        "@": "refresh",  # FIXME: move to global and refactor & rewrite
    }

    def __init__(self, ui, docker_backend):
        self.ui = ui
        self.widget = MainListBox(ui, docker_backend)
        super().__init__()

    def process_realtime_event(self, event):
        self.widget.process_realtime_event(event)


class LogsBuffer(Buffer):
    description = "Display logs of selected container."
    display_name = "Logs "

    def __init__(self, ui, docker_object, follow=False):
        """

        :param docker_object: container to display logs
        :param ui: ui object so we can refresh
        """
        self.display_name += "({})".format(docker_object.short_name)
        if isinstance(docker_object, DockerContainer):
            try:
                pre_message = "Getting logs for container {}...".format(docker_object.short_name)
                ui.notify_message(pre_message)
                if follow:
                    # FIXME: this is a bit race-y -- we might lose some logs with this approach
                    operation = docker_object.logs(follow=follow, lines=0)
                    static_data = docker_object.logs(follow=False).response
                    self.widget = AsyncScrollableListBox(operation.response, ui, static_data=static_data)
                else:
                    operation = docker_object.logs(follow=follow)
                    self.widget = ScrollableListBox(ui, operation.response)
                ui.remove_notification_message(pre_message)
                ui.notify_widget(get_operation_notify_widget(operation, display_always=False))
            except Exception as ex:
                # FIXME: let's catch 404 and print that container doesn't exist
                #        instead of printing ugly HTTP error
                raise NotifyError("Error getting logs for container %s: %r" % (docker_object, ex))
        else:
            raise NotifyError("Only containers have logs.")
        super().__init__()


class InspectBuffer(Buffer):
    display_name = "Inspect "
    description = "Display all the information docker knows about selected object: " + \
                  "same output as `docker inspect`."

    def __init__(self, ui, docker_object):
        """

        :param docker_object: object to inspect
        """
        self.docker_object = docker_object
        self.ui = ui
        self.widget = None
        self.display_name += docker_object.short_name
        super().__init__()

    def refresh(self):
        inspect_data = self.docker_object.display_inspect()
        self.widget = ScrollableListBox(self.ui, inspect_data)

    def process_realtime_event(self, event):
        if event.get("id", None) == self.docker_object.object_id:
            self.ui.notify_message("Docker object changed, refreshing.")
            focus = self.widget.get_focus()[1]
            self.widget.set_text(self.docker_object.display_inspect())
            self.widget.set_focus(focus)


class HelpBuffer(Buffer):
    # TODO: apply this interface to other buffers: create views
    description = "Show information about currently displayed buffer and " + \
                  "what keybindings are available there"
    display_name = "Help"

    def __init__(self, ui, inp):
        """
        display buffer with more info about object 'inp'

        :param ui: UI instance
        :param inp: Buffer, Command instance
        """
        self.ui = ui
        if isinstance(inp, Buffer):
            self.display_name += "({})".format(inp.display_name)
            self.widget = HelpBufferView(ui, inp, self.global_keybinds)
        elif isinstance(inp, Command):
            self.display_name += "({})".format(inp.name)
            self.widget = HelpCommandView(ui, inp)

        super().__init__()


class DfBuffer(Buffer):
    description = "Show information about how much disk space container, images and volumes take."
    display_name = "Disk Usage"

    def __init__(self, ui):
        """
        :param ui: UI instance
        """
        self.ui = ui
        self.widget = DfBufferView(ui, self)

        super().__init__()

    def refresh(self, df=None, containers=None, images=None):
        self.widget.refresh(df=df, containers=containers, images=images)
