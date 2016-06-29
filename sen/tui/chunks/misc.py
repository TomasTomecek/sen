"""
Unsorted chunks.
"""

import logging

from sen.docker_backend import DockerImage, DockerContainer
from sen.tui.chunks.container import get_detailed_container_row
from sen.tui.chunks.image import get_detailed_image_row


logger = logging.getLogger(__name__)


def get_row(docker_object):
    if isinstance(docker_object, DockerImage):
        return get_detailed_image_row(docker_object)
    elif isinstance(docker_object, DockerContainer):
        return get_detailed_container_row(docker_object)
    else:
        raise Exception("what ")
