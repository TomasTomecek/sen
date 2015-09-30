import logging


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
        return "{0}(name={!r}, widget={!r})".format(
            self.__class__.__name__, self.display_name, self.widget)


class MainListBuffer(Buffer):
    display_name = "Listing"


class InspectBuffer(Buffer):
    def __init__(self, docker_object):
        self.display_name = "{} inspect".format(docker_object.short_name)
        super().__init__()
