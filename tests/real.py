import logging

from flexmock import flexmock
import docker


# docker 1.10
image_data = [{
    'Created': 1500000000,
    'Id': 'sha256:3ab9a7ed8a169ab89b09fb3e12a14a390d3c662703b65b4541c0c7bde0ee97eb',
    'ParentId': '3ab9a7ed8a169ab89b09fb3e12a14a390d3c662703b65b4541c0c7bde0ee97eb',
    'RepoDigests': [],
    'RepoTags': ['image:latest'],
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


stats_data = {
  "memory_stats": {
    "max_usage": 162844672,
    "stats": {
      "hierarchical_memsw_limit": 9223372036854771712,
      "total_active_anon": 89210880,
      "rss": 89210880,
      "total_inactive_file": 61886464,
      "unevictable": 0,
      "total_writeback": 0,
      "total_pgmajfault": 443,
      "total_pgpgout": 6463,
      "pgpgout": 6463,
      "inactive_anon": 0,
      "total_swap": 0,
      "recent_rotated_anon": 28087,
      "rss_huge": 0,
      "recent_scanned_anon": 28087,
      "swap": 0,
      "total_dirty": 0,
      "pgmajfault": 443,
      "hierarchical_memory_limit": 9223372036854771712,
      "total_active_file": 7221248,
      "dirty": 0,
      "mapped_file": 44122112,
      "total_inactive_anon": 0,
      "total_cache": 69107712,
      "total_unevictable": 0,
      "pgfault": 72694,
      "inactive_file": 61886464,
      "total_pgpgin": 45115,
      "total_pgfault": 72694,
      "total_rss": 89210880,
      "pgpgin": 45115,
      "active_file": 7221248,
      "cache": 69107712,
      "recent_scanned_file": 18992,
      "total_mapped_file": 44122112,
      "recent_rotated_file": 1766,
      "total_rss_huge": 0,
      "writeback": 0,
      "active_anon": 89210880
    },
    "usage": 158318592,
    "limit": 12285616128,
    "failcnt": 0
  },
  "precpu_stats": {
    "cpu_usage": {
      "total_usage": 0,
      "usage_in_usermode": 0,
      "usage_in_kernelmode": 0,
      "percpu_usage": None
    },
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    },
    "system_cpu_usage": 0
  },
  "cpu_stats": {
    "cpu_usage": {
      "total_usage": 12270431082,
      "usage_in_usermode": 11950000000,
      "usage_in_kernelmode": 270000000,
      "percpu_usage": [
        907668070,
        2527522511,
        4443050630,
        4392189871
      ]
    },
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    },
    "system_cpu_usage": 129418060000000
  },
  "pids_stats": {},
  "read": "2016-03-04T17:54:13.542707177+01:00",
  "networks": {
    "eth0": {
      "rx_packets": 1018,
      "rx_errors": 0,
      "tx_errors": 0,
      "rx_bytes": 141847,
      "tx_packets": 20,
      "tx_bytes": 1636,
      "tx_dropped": 0,
      "rx_dropped": 0
    }
  },
  "blkio_stats": {
    "io_service_bytes_recursive": [
      {
        "value": 18249728,
        "major": 7,
        "op": "Read",
        "minor": 0
      },
      {
        "value": 253952,
        "major": 7,
        "op": "Write",
        "minor": 0
      },
      {
        "value": 135168,
        "major": 7,
        "op": "Sync",
        "minor": 0
      },
      {
        "value": 18368512,
        "major": 7,
        "op": "Async",
        "minor": 0
      },
      {
        "value": 18503680,
        "major": 7,
        "op": "Total",
        "minor": 0
      },
      {
        "value": 18249728,
        "major": 253,
        "op": "Read",
        "minor": 1
      },
      {
        "value": 253952,
        "major": 253,
        "op": "Write",
        "minor": 1
      },
      {
        "value": 135168,
        "major": 253,
        "op": "Sync",
        "minor": 1
      },
      {
        "value": 18368512,
        "major": 253,
        "op": "Async",
        "minor": 1
      },
      {
        "value": 18503680,
        "major": 253,
        "op": "Total",
        "minor": 1
      },
      {
        "value": 72112128,
        "major": 253,
        "op": "Read",
        "minor": 2
      },
      {
        "value": 1978368,
        "major": 253,
        "op": "Write",
        "minor": 2
      },
      {
        "value": 1855488,
        "major": 253,
        "op": "Sync",
        "minor": 2
      },
      {
        "value": 72235008,
        "major": 253,
        "op": "Async",
        "minor": 2
      },
      {
        "value": 74090496,
        "major": 253,
        "op": "Total",
        "minor": 2
      }
    ],
    "io_wait_time_recursive": [],
    "io_serviced_recursive": [
      {
        "value": 595,
        "major": 7,
        "op": "Read",
        "minor": 0
      },
      {
        "value": 41,
        "major": 7,
        "op": "Write",
        "minor": 0
      },
      {
        "value": 26,
        "major": 7,
        "op": "Sync",
        "minor": 0
      },
      {
        "value": 610,
        "major": 7,
        "op": "Async",
        "minor": 0
      },
      {
        "value": 636,
        "major": 7,
        "op": "Total",
        "minor": 0
      },
      {
        "value": 595,
        "major": 253,
        "op": "Read",
        "minor": 1
      },
      {
        "value": 41,
        "major": 253,
        "op": "Write",
        "minor": 1
      },
      {
        "value": 26,
        "major": 253,
        "op": "Sync",
        "minor": 1
      },
      {
        "value": 610,
        "major": 253,
        "op": "Async",
        "minor": 1
      },
      {
        "value": 636,
        "major": 253,
        "op": "Total",
        "minor": 1
      },
      {
        "value": 1176,
        "major": 253,
        "op": "Read",
        "minor": 2
      },
      {
        "value": 68,
        "major": 253,
        "op": "Write",
        "minor": 2
      },
      {
        "value": 52,
        "major": 253,
        "op": "Sync",
        "minor": 2
      },
      {
        "value": 1192,
        "major": 253,
        "op": "Async",
        "minor": 2
      },
      {
        "value": 1244,
        "major": 253,
        "op": "Total",
        "minor": 2
      }
    ],
    "io_time_recursive": [],
    "io_queue_recursive": [],
    "io_merged_recursive": [],
    "sectors_recursive": [],
    "io_service_time_recursive": []
  }
}

# docker 1.11; docker inspect fedora
inspect_image_data = [
    {
        "Id": "sha256:6547ce9b34076d54d455d99a77d6e4e4e03203610b1a82d83c60cc4a0cee1434",
        "RepoTags": [
            "fedora:latest"
        ],
        "RepoDigests": [],
        "Parent": "a79ad4dac406fcf85b9c7315fe08de5b620c1f7a12f45c8185c843f4b4a49c4e",  # faked
        "Comment": "",
        "Created": "2016-01-04T21:26:31.943198534Z",
        "Container": "328e8788d8464dca333fd928a128778871e14668f38f5ae8e4121d44eaddd177",
        "ContainerConfig": {
            "Hostname": "328e8788d846",
            "Domainname": "",
            "User": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": None,
            "Cmd": [
                "/bin/sh",
                "-c",
                "#(nop) ADD file:b028ccee96c12c106da1e17b9cd93f3dbce86b888b2114116a481b289a46def8 in /"
            ],
            "Image": "b0082ba983ef3569aad347f923a9cec8ea764c239179081a1e2c47709788dc44",
            "Volumes": None,
            "WorkingDir": "",
            "Entrypoint": None,
            "OnBuild": None,
            "Labels": None
        },
        "DockerVersion": "1.8.3",
        "Author": "Adam Miller \u003cmaxamillion@fedoraproject.org\u003e",
        "Config": {
            "Hostname": "328e8788d846",
            "Domainname": "",
            "User": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": None,
            "Cmd": None,
            "Image": "b0082ba983ef3569aad347f923a9cec8ea764c239179081a1e2c47709788dc44",
            "Volumes": None,
            "WorkingDir": "",
            "Entrypoint": None,
            "OnBuild": None,
            "Labels": None
        },
        "Architecture": "amd64",
        "Os": "linux",
        "Size": 206283556,
        "VirtualSize": 206283556,
        "GraphDriver": {
            "Name": "devicemapper",
            "Data": {
                "DeviceId": "139",
                "DeviceName": "docker-253:0-559511492-aa5ca2480c3fb5665db23937f543319feb0a5c36b09b31c396230280a80d6a69",
                "DeviceSize": "107374182400"
            }
        },
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef",
                "sha256:15b864f11a279764b047bdd56de7fcb813118196f16a4f471296bb21e18358a2"
            ]
        }
    }
]


def images_response(*args, **kwargs):
    logging.debug("fake image response")
    global image_data
    return image_data


def containers_response(*args, **kwargs):
    global container_data
    return [container_data]


def stats_response(*args, **kwargs):
    global stats_data
    return iter([stats_data])


def mock():
    try:
        client_class = docker.Client     # 1.x
    except AttributeError:
        client_class = docker.APIClient  # 2.x

    flexmock(client_class, images=images_response)
    flexmock(client_class, containers=containers_response)
    flexmock(client_class, version=lambda *args, **kwargs: version_data)
    flexmock(client_class, top=lambda *args, **kwargs: top_data)
    flexmock(client_class, stats=stats_response)
    flexmock(client_class, inspect_image=lambda *args, **kwargs: inspect_image_data)
