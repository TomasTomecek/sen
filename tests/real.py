from flexmock import flexmock
import docker


# docker 1.9
image_data = [{
    'Created': 1414577076,
    'Id': '3ab9a7ed8a169ab89b09fb3e12a14a390d3c662703b65b4541c0c7bde0ee97eb',
    'ParentId': 'a79ad4dac406fcf85b9c7315fe08de5b620c1f7a12f45c8185c843f4b4a49c4e',
    'RepoDigests': [],
    'RepoTags': ['image:latest'],
    'Size': 0,
    'VirtualSize': 856564160
}, {  # docker 1.10
    'Created': 1500000000,
    'Id': 'sha256:3ab9a7ed8a169ab89b09fb3e12a14a390d3c662703b65b4541c0c7bde0ee97eb',
    'ParentId': '3ab9a7ed8a169ab89b09fb3e12a14a390d3c662703b65b4541c0c7bde0ee97eb',
    'RepoDigests': [],
    'RepoTags': ['banana:latest'],
    'Size': 0,
    'VirtualSize': 850000000
}]


container_data = {
    'Command': 'ls',
    'Created': 1451419101,
    'HostConfig': {'NetworkMode': 'default'},
    'Id': 'ce3779014be349654fb757d6eed61954fb33b75510a3845e0dd8107ed8bef765',
    'Image': 'banana',
    'ImageID': '0a31ac8bd1d47354c824984916e298726fe2525ba19f07da7865004b256588a3',
    'Labels': {'aqwe': 'zxcasd', 'aqwe2': 'zxcasd2', 'x': 'y'},
    'Names': ['/elated_bose'],
    'Ports': [],
    'Status': 'Exited (0) 47 hours ago'
}


version_data = {
    'ApiVersion': '1.21',
    'Arch': 'amd64',
    'BuildTime': 'Thu Sep 10 17:53:19 UTC 2015',
    'GitCommit': 'af9b534-dirty',
    'GoVersion': 'go1.5.1',
    'KernelVersion': '4.2.5-300.fc23.x86_64',
    'Os': 'linux',
    'Version': '1.9.0-dev-fc24'
}

top_data = {
    "Titles": [
        "PID",
        "PPID",
        "WCHAN",
        "COMMAND"
    ],
    "Processes": [
        [
            "18725",
            "23743",
            "hrtime",
            "sleep 100000"
        ],
        [
            "18733",
            "23743",
            "hrtime",
            "sleep 100000"
        ],
        [
            "18743",
            "23743",
            "hrtime",
            "sleep 100000"
        ],
        [
            "23743",
            "24542",
            "poll_s",
            "sh"
        ],
        [
            "23819",
            "23743",
            "hrtime",
            "sleep 100000"
        ],
        [
            "24502",
            "21459",
            "wait",
            "sh"
        ],
        [
            "24542",
            "24502",
            "wait",
            "sh"
        ]
    ]
}


def images_response(*args, **kwargs):
    global image_data
    return image_data


def containers_response(*args, **kwargs):
    global container_data
    return [container_data]


def mock():
    flexmock(docker.Client, images=images_response)
    flexmock(docker.Client, containers=containers_response)
    flexmock(docker.Client, version=lambda *args, **kwargs: version_data)
    flexmock(docker.Client, top=lambda *args, **kwargs: top_data)
