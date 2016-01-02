import logging

from sen.docker_backend import DockerContainer, RootImage
from sen.exceptions import NotifyError
from sen.tui.constants import HELP_TEXT
from sen.tui.widgets.info import ImageInfoWidget
from sen.tui.widgets.list.main import MainListBox
from sen.tui.widgets.list.util import get_operation_notify_widget
from sen.tui.widgets.list.common import AsyncScrollableListBox, ScrollableListBox
from sen.tui.widgets.tree import ImageTree


logger = logging.getLogger(__name__)


class Buffer:
    """
    base buffer class
    """
    display_name = None  # display in status bar
    widget = None  # display this in main frame
    tag = None  # single char, for status

    def __init__(self):
        logger.debug("creating buffer %r", self)

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
        widgets = self.widget.filter(s)
        if widgets is not None:
            self.widget.set_body(widgets)


class ImageInfoBuffer(Buffer):
    tag = "I"

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


class TreeBuffer(Buffer):
    display_name = "Tree"
    tag = "T"

    def __init__(self, docker_backend, ui):
        """
        """
        self.widget = ImageTree(docker_backend, ui)
        super().__init__()


class MainListBuffer(Buffer):
    display_name = "Listing"
    tag = "M"

    def __init__(self, docker_backend, ui):
        self.ui = ui
        self.widget = MainListBox(docker_backend, ui)
        super().__init__()

    def refresh(self, focus_on_top=False):
        self.widget.populate(focus_on_top=focus_on_top)
        self.ui.refresh()


class LogsBuffer(Buffer):

    def __init__(self, docker_object, ui, follow=False):
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
                operation = docker_object.logs(follow=follow)
                ui.remove_notification_message(pre_message)
                ui.notify_widget(get_operation_notify_widget(operation, display_always=False))
                if follow:
                    self.widget = AsyncScrollableListBox(operation.response, ui)
                else:
                    self.widget = ScrollableListBox(operation.response)
            except Exception as ex:
                # FIXME: let's catch 404 and print that container doesn't exist
                #        instead of printing ugly HTTP error
                raise NotifyError("Error getting logs for container %s: %r" % (docker_object, ex))
        else:
            raise NotifyError("Only containers have logs.")
        super().__init__()


class InspectBuffer(Buffer):
    tag = "I"

    def __init__(self, docker_object):
        """

        :param docker_object: object to inspect
        """
        self.display_name = docker_object.short_name
        inspect_data = docker_object.display_inspect()
        self.widget = ScrollableListBox(inspect_data)
        self.display_name = docker_object.short_name
        super().__init__()


class HelpBuffer(Buffer):
    tag = "H"
    display_name = ""

    def __init__(self):
        """
        """
        self.widget = ScrollableListBox(HELP_TEXT)
        super().__init__()
