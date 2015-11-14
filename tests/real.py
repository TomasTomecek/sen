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


version_data = {'ApiVersion': '1.21',
    'Arch': 'amd64',
    'BuildTime': 'Thu Sep 10 17:53:19 UTC 2015',
    'GitCommit': 'af9b534-dirty',
    'GoVersion': 'go1.5.1',
    'KernelVersion': '4.2.5-300.fc23.x86_64',
    'Os': 'linux',
    'Version': '1.9.0-dev-fc24'
}


def images_response(*args, **kwargs):
    global image_data
    return [image_data]


def mock():
    flexmock(docker.Client, images=images_response)
    flexmock(docker.Client, version=lambda *args, **kwargs: version_data)
