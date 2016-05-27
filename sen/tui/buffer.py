import logging

from sen.docker_backend import DockerContainer, RootImage
from sen.exceptions import NotifyError
from sen.tui.constants import HELP_TEXT
from sen.tui.widgets.info import ImageInfoWidget, ContainerInfoWidget, ProcessTree
from sen.tui.widgets.list.main import MainListBox
from sen.tui.widgets.list.util import get_operation_notify_widget
from sen.tui.widgets.list.common import AsyncScrollableListBox, ScrollableListBox
from sen.tui.widgets.tree import ImageTree


logger = logging.getLogger(__name__)


class Buffer:
    """
    base buffer class
    """
    name = None  # unique identifier
    display_name = None  # display in status bar
    widget = None  # display this in main frame
    tag = None  # single char, for status

    # global keybinds which will be available in every buffer
    global_keybinds = {  # FIXME: half of these needs to be available on tree buffer
        # navigation
        "gg": "navigate-top",
        "G": "navigate-bottom",
        "j": "navigate-down",
        "k": "navigate-up",
        "ctrl d": "navigate-downwards",
        "ctrl u": "navigate-upwards",

        # UI
        ":": "prompt",
        "/": "prompt initial-text=\"search \"",
        "n": "search-next",
        "N": "search-previous",
        "f4": "prompt initial-text=\"filter \"",
        "x": "remove-buffer",
        "q": "kill-buffer",
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


class ImageInfoBuffer(Buffer):
    tag = "I"
    keybinds = {
        "enter": "display-info",
        "d": "rm",  # TODO: verify this works on image names
        "i": "inspect",
    }

    def __init__(self, docker_image, ui):
        """
        :param docker_image:
        :param ui: ui object so we refresh
        """
        if isinstance(docker_image, RootImage):
            raise NotifyError("Image \"scratch\" doesn't provide any more information.")
        self.display_name = docker_image.short_name
        self.widget = ImageInfoWidget(ui, docker_image)
        super().__init__()


class ContainerInfoBuffer(Buffer):
    tag = "I"
    keybinds = {
        "enter": "display-info",
        "i": "inspect",
    }

    def __init__(self, docker_container, ui):
        """
        :param docker_container:
        :param ui: ui object so we refresh
        """
        self.display_name = docker_container.short_name
        self.widget = ContainerInfoWidget(ui, docker_container)
        super().__init__()


class TreeBuffer(Buffer):
    display_name = "Tree"
    tag = "T"

    def __init__(self, ui, docker_backend):
        """
        """
        self.widget = ImageTree(ui, docker_backend)
        super().__init__()


class MainListBuffer(Buffer):
    display_name = "Listing"
    tag = "M"
    keybinds = {
        "d": "rm",  # TODO: do also rmi
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
        "@": "refresh-current-buffer",  # FIXME: move to global and refactor & rewrite
    }

    def __init__(self, ui, docker_backend):
        self.ui = ui
        self.widget = MainListBox(ui, docker_backend)
        super().__init__()

    def refresh(self, focus_on_top=False):
        logger.info("refresh listing buffer")
        self.widget.populate(focus_on_top=focus_on_top)
        self.ui.refresh()


class LogsBuffer(Buffer):

    def __init__(self, ui, docker_object, follow=False):
        """

        :param docker_object: container to display logs
        :param ui: ui object so we refresh
        """
        self.tag = "F" if follow else "L"
        self.display_name = docker_object.short_name
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
    tag = "I"

    def __init__(self, ui, docker_object):
        """

        :param docker_object: object to inspect
        """
        self.display_name = docker_object.short_name
        inspect_data = docker_object.display_inspect()
        self.widget = ScrollableListBox(ui, inspect_data)
        self.display_name = docker_object.short_name
        super().__init__()


class HelpBuffer(Buffer):
    tag = "H"
    display_name = ""

    def __init__(self, ui):
        """
        """
        self.widget = ScrollableListBox(ui, HELP_TEXT, focus_bottom=False)
        super().__init__()
