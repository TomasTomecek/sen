from sen.docker_backend import DockerBackend
from .real import image_data, mock


def test_images_call():
    mock()
    b = DockerBackend()
    operation = b.get_images()
    images_response = operation.response
    assert len(images_response) == 1
    assert images_response[0].image_id == image_data["Id"]
    assert images_response[0].short_name == image_data["RepoTags"][0]
