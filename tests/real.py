from flexmock import flexmock
import docker


image_data = {
    'Created': 1414577076,
    'Id': '3ab9a7ed8a169ab89b09fb3e12a14a390d3c662703b65b4541c0c7bde0ee97eb',
    'ParentId': 'a79ad4dac406fcf85b9c7315fe08de5b620c1f7a12f45c8185c843f4b4a49c4e',
    'RepoTags': ['image:latest'],
    'Size': 0,
    'VirtualSize': 856564160
}


def images_response(*args, **kwargs):
    global image_data
    return [image_data]


def mock():
    flexmock(docker.AutoVersionClient, images=images_response)
