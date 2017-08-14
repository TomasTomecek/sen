from sen.docker_backend import DockerBackend
from sen.util import calculate_cpu_percent2, calculate_cpu_percent
from .real import image_data, mock, container_data


def test_images_call():
    mock()
    b = DockerBackend()
    operation = b.get_images(cached=False)
    images_response = operation.response
    assert len(images_response) == 1
    assert images_response[0].image_id == image_data[0]["Id"]
    assert images_response[0].short_name == image_data[0]["RepoTags"][0]
    assert images_response[0].parent_id == image_data[0]["ParentId"]
    assert images_response[0].created_int == image_data[0]["Created"]
    assert [str(x) for x in images_response[0].names] == image_data[0]["RepoTags"]


def test_containers_call():
    mock()
    b = DockerBackend()
    operation = b.get_containers(cached=False)
    containers_response = operation.response
    assert len(containers_response) == 1
    assert containers_response[0].container_id == container_data["Id"]
    assert containers_response[0].names == container_data["Names"]
    assert containers_response[0].short_name == container_data["Names"][0]
    assert containers_response[0].created_int == container_data["Created"]
    assert containers_response[0].command == container_data["Command"]
    assert containers_response[0].nice_status == container_data["Status"]
    assert containers_response[0].image_id == container_data["ImageID"]
    # assert containers_response[0].image_name()


def test_short_id():
    mock()
    b = DockerBackend()
    operation = b.get_images()
    images_response = operation.response
    assert images_response[0].short_id == image_data[0]["Id"][image_data[0]["Id"].index(":")+1:][:12]


def test_top():
    pass


def test_stats():
    mock()
    b = DockerBackend()
    c = b.get_containers()
    c0 = c.response.pop()
    operation = c0.stats()
    stats_stream = operation.response
    assert next(stats_stream)

    for x in c0.d.stats('x', decode=True, stream=True):
        calculate_cpu_percent(x)

    t = 0.0
    s = 0.0
    for x in c0.d.stats('x', decode=True, stream=True):
        calculate_cpu_percent(x)
        _, s, t = calculate_cpu_percent2(x, t, s)
