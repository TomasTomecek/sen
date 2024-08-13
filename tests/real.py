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
  'Platform': {'Name': 'linux/amd64/fedora-40'},
  'Components': [{
    'Name': 'Podman Engine',
    'Version': '5.1.2',
    'Details': {
      'APIVersion': '5.1.2',
      'Arch': 'amd64',
      'BuildTime': '2024-07-10T02:00:00+02:00',
      'Experimental': 'false',
      'GitCommit': '',
      'GoVersion': 'go1.22.5',
      'KernelVersion': '6.9.11-200.fc40.x86_64',
      'MinAPIVersion': '4.0.0',
      'Os': 'linux'}},
    {
      'Name': 'Conmon',
      'Version': 'conmon version 2.1.10, commit: ',
      'Details': {'Package': 'conmon-2.1.10-1.fc40.x86_64'}},
    {
      'Name': 'OCI Runtime (crun)',
      'Version': 'crun version 1.15\ncommit: e6eacaf4034e84185fd8780ac9262bbf57082278\nrundir: /run/user/1000/crun\nspec: 1.0.0\n+SYSTEMD +SELINUX +APPARMOR +CAP +SECCOMP +EBPF +CRIU +LIBKRUN +WASM:wasmedge +YAJL',
      'Details': {'Package': 'crun-1.15-1.fc40.x86_64'}}],
  'Version': '5.1.2',
  'ApiVersion': '1.41',
  'MinAPIVersion': '1.24',
  'GitCommit': '',
  'GoVersion': 'go1.22.5',
  'Os': 'linux',
  'Arch': 'amd64',
  'KernelVersion': '6.9.11-200.fc40.x86_64',
  'BuildTime': '2024-07-10T02:00:00+02:00'
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

# stats 1.13
stats_1_13 = [
{
  "read": "2017-08-14T09:51:41.318110362Z",
  "preread": "2017-08-14T09:51:40.318034402Z",
  "pids_stats": {
    "current": 1
  },
  "blkio_stats": {
    "io_service_bytes_recursive": [
      {
        "major": 7,
        "minor": 0,
        "op": "Read",
        "value": 36864
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Write",
        "value": 12288
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Sync",
        "value": 49152
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Async",
        "value": 0
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Total",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Read",
        "value": 36864
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Write",
        "value": 12288
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Sync",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Total",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Read",
        "value": 46022656
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Write",
        "value": 155648
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Sync",
        "value": 46178304
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Total",
        "value": 46178304
      }
    ],
    "io_serviced_recursive": [
      {
        "major": 7,
        "minor": 0,
        "op": "Read",
        "value": 6
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Write",
        "value": 3
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Sync",
        "value": 9
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Async",
        "value": 0
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Total",
        "value": 9
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Read",
        "value": 6
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Write",
        "value": 3
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Sync",
        "value": 9
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Total",
        "value": 9
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Read",
        "value": 1074
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Write",
        "value": 17
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Sync",
        "value": 1091
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Total",
        "value": 1091
      }
    ],
    "io_queue_recursive": [],
    "io_service_time_recursive": [],
    "io_wait_time_recursive": [],
    "io_merged_recursive": [],
    "io_time_recursive": [],
    "sectors_recursive": []
  },
  "num_procs": 0,
  "storage_stats": {},
  "cpu_stats": {
    "cpu_usage": {
      "total_usage": 4325370082,
      "percpu_usage": [
        1583545267,
        1441574399,
        932669369,
        367581047,
        0,
        0,
        0,
        0
      ],
      "usage_in_kernelmode": 490000000,
      "usage_in_usermode": 3800000000
    },
    "system_cpu_usage": 111726360000000,
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    }
  },
  "precpu_stats": {
    "cpu_usage": {
      "total_usage": 4172062391,
      "percpu_usage": [
        1545098206,
        1408480094,
        870204053,
        348280038,
        0,
        0,
        0,
        0
      ],
      "usage_in_kernelmode": 430000000,
      "usage_in_usermode": 3710000000
    },
    "system_cpu_usage": 111722350000000,
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    }
  },
  "memory_stats": {
    "usage": 179355648,
    "max_usage": 179404800,
    "stats": {
      "active_anon": 53280768,
      "active_file": 11571200,
      "cache": 119050240,
      "dirty": 51224576,
      "hierarchical_memory_limit": 9223372036854771712,
      "hierarchical_memsw_limit": 9223372036854771712,
      "inactive_anon": 0,
      "inactive_file": 107479040,
      "mapped_file": 21954560,
      "pgfault": 37991,
      "pgmajfault": 259,
      "pgpgin": 64385,
      "pgpgout": 22312,
      "recent_rotated_anon": 35307,
      "recent_rotated_file": 2829,
      "recent_scanned_anon": 35307,
      "recent_scanned_file": 31903,
      "rss": 53280768,
      "rss_huge": 0,
      "swap": 0,
      "total_active_anon": 53280768,
      "total_active_file": 11571200,
      "total_cache": 119050240,
      "total_dirty": 51224576,
      "total_inactive_anon": 0,
      "total_inactive_file": 107479040,
      "total_mapped_file": 21954560,
      "total_pgfault": 37991,
      "total_pgmajfault": 259,
      "total_pgpgin": 64385,
      "total_pgpgout": 22312,
      "total_rss": 53280768,
      "total_rss_huge": 0,
      "total_swap": 0,
      "total_unevictable": 0,
      "total_writeback": 0,
      "unevictable": 0,
      "writeback": 0
    },
    "limit": 12283822080
  },
  "name": "/hungry_brown",
  "id": "98a9cd0009984e61a24499aec44bd244078a6a09486782015b3966916eee5c08",
  "networks": {
    "eth0": {
      "rx_bytes": 63518221,
      "rx_packets": 46327,
      "rx_errors": 0,
      "rx_dropped": 0,
      "tx_bytes": 1601338,
      "tx_packets": 23966,
      "tx_errors": 0,
      "tx_dropped": 0
    }
  }
},
{
  "read": "2017-08-14T09:51:42.318182309Z",
  "preread": "2017-08-14T09:51:41.318110362Z",
  "pids_stats": {
    "current": 1
  },
  "blkio_stats": {
    "io_service_bytes_recursive": [
      {
        "major": 7,
        "minor": 0,
        "op": "Read",
        "value": 36864
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Write",
        "value": 12288
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Sync",
        "value": 49152
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Async",
        "value": 0
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Total",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Read",
        "value": 36864
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Write",
        "value": 12288
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Sync",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Total",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Read",
        "value": 46039040
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Write",
        "value": 155648
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Sync",
        "value": 46194688
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Total",
        "value": 46194688
      }
    ],
    "io_serviced_recursive": [
      {
        "major": 7,
        "minor": 0,
        "op": "Read",
        "value": 6
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Write",
        "value": 3
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Sync",
        "value": 9
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Async",
        "value": 0
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Total",
        "value": 9
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Read",
        "value": 6
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Write",
        "value": 3
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Sync",
        "value": 9
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Total",
        "value": 9
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Read",
        "value": 1075
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Write",
        "value": 17
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Sync",
        "value": 1092
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Total",
        "value": 1092
      }
    ],
    "io_queue_recursive": [],
    "io_service_time_recursive": [],
    "io_wait_time_recursive": [],
    "io_merged_recursive": [],
    "io_time_recursive": [],
    "sectors_recursive": []
  },
  "num_procs": 0,
  "storage_stats": {},
  "cpu_stats": {
    "cpu_usage": {
      "total_usage": 4733027699,
      "percpu_usage": [
        1598666891,
        1746779810,
        999006836,
        388574162,
        0,
        0,
        0,
        0
      ],
      "usage_in_kernelmode": 550000000,
      "usage_in_usermode": 4140000000
    },
    "system_cpu_usage": 111730350000000,
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    }
  },
  "precpu_stats": {
    "cpu_usage": {
      "total_usage": 4325370082,
      "percpu_usage": [
        1583545267,
        1441574399,
        932669369,
        367581047,
        0,
        0,
        0,
        0
      ],
      "usage_in_kernelmode": 490000000,
      "usage_in_usermode": 3800000000
    },
    "system_cpu_usage": 111726360000000,
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    }
  },
  "memory_stats": {
    "usage": 186646528,
    "max_usage": 186646528,
    "stats": {
      "active_anon": 53792768,
      "active_file": 12742656,
      "cache": 125739008,
      "dirty": 57917440,
      "hierarchical_memory_limit": 9223372036854771712,
      "hierarchical_memsw_limit": 9223372036854771712,
      "inactive_anon": 0,
      "inactive_file": 112996352,
      "mapped_file": 21954560,
      "pgfault": 38262,
      "pgmajfault": 259,
      "pgpgin": 66151,
      "pgpgout": 22318,
      "recent_rotated_anon": 35432,
      "recent_rotated_file": 3121,
      "recent_scanned_anon": 35432,
      "recent_scanned_file": 33834,
      "rss": 53800960,
      "rss_huge": 0,
      "swap": 0,
      "total_active_anon": 53792768,
      "total_active_file": 12742656,
      "total_cache": 125739008,
      "total_dirty": 57917440,
      "total_inactive_anon": 0,
      "total_inactive_file": 112996352,
      "total_mapped_file": 21954560,
      "total_pgfault": 38262,
      "total_pgmajfault": 259,
      "total_pgpgin": 66151,
      "total_pgpgout": 22318,
      "total_rss": 53800960,
      "total_rss_huge": 0,
      "total_swap": 0,
      "total_unevictable": 0,
      "total_writeback": 0,
      "unevictable": 0,
      "writeback": 0
    },
    "limit": 12283822080
  },
  "name": "/hungry_brown",
  "id": "98a9cd0009984e61a24499aec44bd244078a6a09486782015b3966916eee5c08",
  "networks": {
    "eth0": {
      "rx_bytes": 70507552,
      "rx_packets": 51415,
      "rx_errors": 0,
      "rx_dropped": 0,
      "tx_bytes": 1766536,
      "tx_packets": 26469,
      "tx_errors": 0,
      "tx_dropped": 0
    }
  }
},
{
  "read": "2017-08-14T09:51:43.318289249Z",
  "preread": "2017-08-14T09:51:42.318182309Z",
  "pids_stats": {
    "current": 1
  },
  "blkio_stats": {
    "io_service_bytes_recursive": [
      {
        "major": 7,
        "minor": 0,
        "op": "Read",
        "value": 36864
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Write",
        "value": 12288
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Sync",
        "value": 49152
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Async",
        "value": 0
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Total",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Read",
        "value": 36864
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Write",
        "value": 12288
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Sync",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Total",
        "value": 49152
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Read",
        "value": 46039040
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Write",
        "value": 155648
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Sync",
        "value": 46194688
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Total",
        "value": 46194688
      }
    ],
    "io_serviced_recursive": [
      {
        "major": 7,
        "minor": 0,
        "op": "Read",
        "value": 6
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Write",
        "value": 3
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Sync",
        "value": 9
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Async",
        "value": 0
      },
      {
        "major": 7,
        "minor": 0,
        "op": "Total",
        "value": 9
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Read",
        "value": 6
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Write",
        "value": 3
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Sync",
        "value": 9
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 1,
        "op": "Total",
        "value": 9
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Read",
        "value": 1075
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Write",
        "value": 17
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Sync",
        "value": 1092
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Async",
        "value": 0
      },
      {
        "major": 253,
        "minor": 3,
        "op": "Total",
        "value": 1092
      }
    ],
    "io_queue_recursive": [],
    "io_service_time_recursive": [],
    "io_wait_time_recursive": [],
    "io_merged_recursive": [],
    "io_time_recursive": [],
    "sectors_recursive": []
  },
  "num_procs": 0,
  "storage_stats": {},
  "cpu_stats": {
    "cpu_usage": {
      "total_usage": 5723669129,
      "percpu_usage": [
        1598666891,
        2737421240,
        999006836,
        388574162,
        0,
        0,
        0,
        0
      ],
      "usage_in_kernelmode": 570000000,
      "usage_in_usermode": 5120000000
    },
    "system_cpu_usage": 111734320000000,
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    }
  },
  "precpu_stats": {
    "cpu_usage": {
      "total_usage": 4733027699,
      "percpu_usage": [
        1598666891,
        1746779810,
        999006836,
        388574162,
        0,
        0,
        0,
        0
      ],
      "usage_in_kernelmode": 550000000,
      "usage_in_usermode": 4140000000
    },
    "system_cpu_usage": 111730350000000,
    "throttling_data": {
      "periods": 0,
      "throttled_periods": 0,
      "throttled_time": 0
    }
  },
  "memory_stats": {
    "usage": 218624000,
    "max_usage": 218624000,
    "stats": {
      "active_anon": 85700608,
      "active_file": 18706432,
      "cache": 125739008,
      "dirty": 57917440,
      "hierarchical_memory_limit": 9223372036854771712,
      "hierarchical_memsw_limit": 9223372036854771712,
      "inactive_anon": 0,
      "inactive_file": 107032576,
      "mapped_file": 21954560,
      "pgfault": 46060,
      "pgmajfault": 259,
      "pgpgin": 73949,
      "pgpgout": 22318,
      "recent_rotated_anon": 43222,
      "recent_rotated_file": 4577,
      "recent_scanned_anon": 43222,
      "recent_scanned_file": 35290,
      "rss": 85741568,
      "rss_huge": 0,
      "swap": 0,
      "total_active_anon": 85700608,
      "total_active_file": 18706432,
      "total_cache": 125739008,
      "total_dirty": 57917440,
      "total_inactive_anon": 0,
      "total_inactive_file": 107032576,
      "total_mapped_file": 21954560,
      "total_pgfault": 46060,
      "total_pgmajfault": 259,
      "total_pgpgin": 73949,
      "total_pgpgout": 22318,
      "total_rss": 85741568,
      "total_rss_huge": 0,
      "total_swap": 0,
      "total_unevictable": 0,
      "total_writeback": 0,
      "unevictable": 0,
      "writeback": 0
    },
    "limit": 12283822080
  },
  "name": "/hungry_brown",
  "id": "98a9cd0009984e61a24499aec44bd244078a6a09486782015b3966916eee5c08",
  "networks": {
    "eth0": {
      "rx_bytes": 70507552,
      "rx_packets": 51415,
      "rx_errors": 0,
      "rx_dropped": 0,
      "tx_bytes": 1766606,
      "tx_packets": 26470,
      "tx_errors": 0,
      "tx_dropped": 0
    }
  }
}
]

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

def stats_response_1_13(*args, **kwargs):
    global stats_1_13
    return iter(stats_1_13)


def mock():
    try:
        client_class = docker.Client     # 1.x
    except AttributeError:
        client_class = docker.APIClient  # 2.x

    flexmock(client_class, images=images_response)
    flexmock(client_class, containers=containers_response)
    flexmock(client_class, version=lambda *args, **kwargs: version_data)
    flexmock(client_class, top=lambda *args, **kwargs: top_data)
    flexmock(client_class, stats=stats_response_1_13)
    flexmock(client_class, inspect_image=lambda *args, **kwargs: inspect_image_data)
