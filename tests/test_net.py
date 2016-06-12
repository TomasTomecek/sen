from sen.net import NetData

empty_inspect = {
    "NetworkSettings": {
        "SecondaryIPAddresses": None,
        "EndpointID": "",
        "IPv6Gateway": "",
        "IPAddress": "",
        "LinkLocalIPv6PrefixLen": 0,
        "Networks": None,
        "GlobalIPv6PrefixLen": 0,
        "MacAddress": "",
        "GlobalIPv6Address": "",
        "SandboxID": "",
        "SecondaryIPv6Addresses": None,
        "SandboxKey": "",
        "HairpinMode": False,
        "IPPrefixLen": 0,
        "Bridge": "",
        "Gateway": "",
        "Ports": None,
        "LinkLocalIPv6Address": ""
    },
}
populated_inspect = {
    "NetworkSettings": {
        "HairpinMode": False,
        "SandboxKey": "/var/run/docker/netns/7c1ad2c7d916",
        "MacAddress": "02:42:ac:11:00:07",
        "SandboxID": "7c1ad2c7d916cdbb6f92ef22feb420b67b186eb719d7b968fa508820e55617ab",
        "SecondaryIPAddresses": None,
        "Ports": {
            "8080/tcp": [
                {
                    "HostPort": "31003",
                    "HostIp": "0.0.0.0"
                }
            ]
        },
        "SecondaryIPv6Addresses": None,
        "IPAddress": "172.17.0.7",
        "GlobalIPv6Address": "",
        "EndpointID": "4ec3605fe3c70ef85cacee52d29db70c67f87cf85fd8021bf9e35ae09d4a5be2",
        "LinkLocalIPv6Address": "",
        "Networks": {
            "bridge": {
                "MacAddress": "02:42:ac:11:00:07",
                "Links": None,
                "IPAMConfig": None,
                "IPAddress": "172.17.0.7",
                "NetworkID": "2e90eba6e82abb1fe2ba82bfafbb1cf675e92cb9b33e667c78d5ab12cc3ab5b5",
                "GlobalIPv6Address": "",
                "GlobalIPv6PrefixLen": 0,
                "Aliases": None,
                "IPv6Gateway": "",
                "Gateway": "172.17.0.1",
                "EndpointID": "4ec3605fe3c70ef85cacee52d29db70c67f87cf85fd8021bf9e35ae09d4a5be2",
                "IPPrefixLen": 16
            }
        },
        "Bridge": "",
        "LinkLocalIPv6PrefixLen": 0,
        "IPv6Gateway": "",
        "Gateway": "172.17.0.1",
        "GlobalIPv6PrefixLen": 0,
        "IPPrefixLen": 16
    },
    "Config": {
        "ExposedPorts": {
            "8787/tcp": {}
        },
    }
}


def test_empty_network():
    nd = NetData(empty_inspect)
    assert nd.ips == {}
    assert nd.ports == {}


def test_populated_network():
    nd = NetData(populated_inspect)
    assert nd.ips == {"bridge": {"ip_address4": "172.17.0.7"},
                      "default": {"ip_address4": "172.17.0.7"}}
    assert nd.ports == {"8080": "31003", "8787": None}
