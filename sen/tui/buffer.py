import logging
from sen.docker_backend import DockerContainer
from sen.tui.widget import AsyncScrollableListBox, MainListBox, ScrollableListBox

logger = logging.getLogger(__name__)


class Buffer:
    """
    base buffer class
    """
    display_name = None  # display in status bar
    widget = None  # display this in main frame

    def __init__(self):
        logger.debug("creating buffer %r", self)

    def __repr__(self):
        return "{}(name={!r}, widget={!r})".format(
            self.__class__.__name__, self.display_name, self.widget)

    def destroy(self):
        destroy_method = getattr(self.widget, "destroy", None)
        if destroy_method:
            destroy_method()


class MainListBuffer(Buffer):
    display_name = "Listing"

    def __init__(self, docker_backend, ui):
        self.widget = MainListBox(docker_backend, ui)
        super().__init__()
        self.refresh()

    def refresh(self):
        self.widget.populate()


class LogsBuffer(Buffer):
    def __init__(self, docker_object, ui):
        """

        :param docker_object: container to display logs
        :param ui: ui object so we refresh
        """
        self.display_name = "{} logs".format(docker_object.short_name)
        if isinstance(docker_object, DockerContainer):
            logs_data, logs_generator = docker_object.logs()
            self.widget = AsyncScrollableListBox(logs_data, logs_generator, ui)
        else:
            raise Exception("Only containers have logs.")
        super().__init__()


class InspectBuffer(Buffer):
    def __init__(self, docker_object):
        """

        :param docker_object: object to inspect
        """
        inspect_data = docker_object.display_inspect()
        self.widget = ScrollableListBox(inspect_data)
        self.display_name = "{} inspect".format(docker_object.short_name)
        super().__init__()
