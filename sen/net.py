"""
networking in docker backend
"""
from sen.util import graceful_chain_get


def extract_data_from_inspect(network_name, network_data):
    """
    :param network_name: str
    :param network_data: dict
    :return: dict:
        {
            "ip_address4": "12.34.56.78"
            "ip_address6": "ff:fa:..."
        }
    """
    a4 = None
    if network_name == "host":
        a4 = "127.0.0.1"
    n = {}
    a4 = graceful_chain_get(network_data, "IPAddress") or a4
    if a4:
        n["ip_address4"] = a4
    a6 = graceful_chain_get(network_data, "GlobalIPv6Address")
    if a6:
        n["ip_address4"] = a6
    return n


class NetData:
    def __init__(self, inspect_data):
        self.inspect_data = inspect_data
        self.net_settings = graceful_chain_get(self.inspect_data, "NetworkSettings")
        self._ports = None
        self._ips = None

    @property
    def ports(self):
        """
        :return: dict
            {
                # container -> host
                "1234": "2345"
            }
        """

        if self._ports is None:
            self._ports = {}
            if self.net_settings["Ports"]:
                for key, value in self.net_settings["Ports"].items():
                    cleaned_port = key.split("/")[0]
                    self._ports[cleaned_port] = graceful_chain_get(value, 0, "HostPort")
            # in case of --net=host, there's nothing in network settings, let's get it from "Config"
            exposed_ports_section = graceful_chain_get(self.inspect_data, "Config", "ExposedPorts")
            if exposed_ports_section:
                for key, value in exposed_ports_section.items():
                    cleaned_port = key.split("/")[0]
                    self._ports[cleaned_port] = None  # extremely docker specific
        return self._ports

    @property
    def ips(self):
        """
        :return: dict:
        {
            "default": {
                "ip_address4": "12.34.56.78"
                "ip_address6": "ff:fa:..."
            }
            "other": {
                ...
            }
        }
        """
        if self._ips is None:
            self._ips = {}
            default_net = extract_data_from_inspect("default", self.net_settings)
            if default_net:
                self._ips["default"] = default_net
            # this can be None
            networks = self.inspect_data["NetworkSettings"]["Networks"]
            if networks:
                for network_name, network_data in networks.items():
                    self._ips[network_name] = extract_data_from_inspect(network_name, network_data)

        return self._ips
