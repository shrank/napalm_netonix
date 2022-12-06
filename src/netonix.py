import json
from typing import Optional, Dict, Type, Any, List, Union
from netonix_api import Netonix
from napalm.base.base import NetworkDriver
from napalm.base import models


class NetonixDriver(NetworkDriver):

    _speed = {
        "1G": 1000.0,
        "1M-F": 1.0,
        "1M-H": 1.0,
        "Down": 0.0
    }

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        timeout: int = 60,
        optional_args: Dict = None,
    )  -> None:
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.n = None

    def _port_fmt(self, port):
        return "Port %s" % port

    def open(self) -> None:
        """
        Opens a connection to the device.
        """
        self.n = Netonix()
        self.n.open(self.hostname, self.username, self.password)

    def close(self) -> None:
        """
        Closes the connection to the device.
        """
        self.n = None

    def is_alive(self) -> models.AliveDict:
        """
        Returns a flag with the connection state.
        Depends on the nature of API used by each driver.
        The state does not reflect only on the connection status (when SSH), it must also take into
        consideration other parameters, e.g.: NETCONF session might not be usable, althought the
        underlying SSH session is still open etc.
        """
        try:
            self.n.getID()
            return {"is_alive": True}
        except:
            return {"is_alive": False}

    def get_interfaces(self) -> Dict[str, models.InterfaceDict]:
        """
        Returns a dictionary of dictionaries. The keys for the first dictionary will be the \
        interfaces in the devices. The inner dictionary will containing the following data for \
        each interface:
         * is_up (True/False)
         * is_enabled (True/False)
         * description (string)
         * last_flapped (float in seconds)
         * speed (float in Mbit)
         * MTU (in Bytes)
         * mac_address (string)
        Example::
            {
            u'Management1':
                {
                'is_up': False,
                'is_enabled': False,
                'description': '',
                'last_flapped': -1.0,
                'speed': 1000.0,
                'mtu': 1500,
                'mac_address': 'FA:16:3E:57:33:61',
                },
            u'Ethernet1':
                {
                'is_up': True,
                'is_enabled': True,
                'description': 'foo',
                'last_flapped': 1429978575.1554043,
                'speed': 1000.0,
                'mtu': 1500,
                'mac_address': 'FA:16:3E:57:33:62',
                },
            u'Ethernet2':
                {
                'is_up': True,
                'is_enabled': True,
                'description': 'bla',
                'last_flapped': 1429978575.1555667,
                'speed': 1000.0,
                'mtu': 1500,
                'mac_address': 'FA:16:3E:57:33:63',
                },
            u'Ethernet3':
                {
                'is_up': False,
                'is_enabled': True,
                'description': 'bar',
                'last_flapped': -1.0,
                'speed': 1000.0,
                'mtu': 1500,
                'mac_address': 'FA:16:3E:57:33:64',
                }
            }
        """
        res = {}
        self.n.getStatus()
        for a in self.n.status["Ports"]:
            port = self._port_fmt(a["Number"])
            res[port] = {
                'is_up': (a["Link"] != "Down"),
                'is_enabled': True,
                'description': '',
                'last_flapped': -1.0,
                'speed': self._speed[a["Link"]],
                'mtu': 1500,
                'mac_address': '',
                }
        self.n.getConfig()
        for a in self.n.config["Ports"]:
            port = self._port_fmt(a["Number"])
            res[port]["description"] = a["Name"]
            res[port]["is_enabled"] = a["Enable"]
            res[port]["mtu"] = a["MTU"]
        return res

    def get_interfaces_counters(self) -> Dict[str, models.InterfaceCounterDict]:
        """
        Returns a dictionary of dictionaries where the first key is an interface name and the
        inner dictionary contains the following keys:
            * tx_errors (int)
            * rx_errors (int)
            * tx_discards (int)
            * rx_discards (int)
            * tx_octets (int)
            * rx_octets (int)
            * tx_unicast_packets (int)
            * rx_unicast_packets (int)
            * tx_multicast_packets (int)
            * rx_multicast_packets (int)
            * tx_broadcast_packets (int)
            * rx_broadcast_packets (int)
        Example::
            {
                u'Ethernet2': {
                    'tx_multicast_packets': 699,
                    'tx_discards': 0,
                    'tx_octets': 88577,
                    'tx_errors': 0,
                    'rx_octets': 0,
                    'tx_unicast_packets': 0,
                    'rx_errors': 0,
                    'tx_broadcast_packets': 0,
                    'rx_multicast_packets': 0,
                    'rx_broadcast_packets': 0,
                    'rx_discards': 0,
                    'rx_unicast_packets': 0
                },
                u'Management1': {
                     'tx_multicast_packets': 0,
                     'tx_discards': 0,
                     'tx_octets': 159159,
                     'tx_errors': 0,
                     'rx_octets': 167644,
                     'tx_unicast_packets': 1241,
                     'rx_errors': 0,
                     'tx_broadcast_packets': 0,
                     'rx_multicast_packets': 0,
                     'rx_broadcast_packets': 80,
                     'rx_discards': 0,
                     'rx_unicast_packets': 0
                },
                u'Ethernet1': {
                     'tx_multicast_packets': 293,
                     'tx_discards': 0,
                     'tx_octets': 38639,
                     'tx_errors': 0,
                     'rx_octets': 0,
                     'tx_unicast_packets': 0,
                     'rx_errors': 0,
                     'tx_broadcast_packets': 0,
                     'rx_multicast_packets': 0,
                     'rx_broadcast_packets': 0,
                     'rx_discards': 0,
                     'rx_unicast_packets': 0
                }
            }
        """
        res = {}
        self.n.getStatus()
        for a in self.n.status["Ports"]:
            port = self._port_fmt(a["Number"])
            res[port] = {
                     'tx_multicast_packets': 0,
                     'tx_discards': 0,
                     'tx_octets': int(a["TxOctets"]),
                     'tx_errors': int(a["TxErrors"]),
                     'rx_octets': int(a["RxOctets"]),
                     'tx_unicast_packets': 0,
                     'rx_errors': int(a["RxErrors"]),
                     'tx_broadcast_packets': 0,
                     'rx_multicast_packets': 0,
                     'rx_broadcast_packets': 0,
                     'rx_discards': 0,
                     'rx_unicast_packets': 0
                }
        return res

    def get_mac_address_table(self) -> List[models.MACAdressTable]:
        """
        Returns a lists of dictionaries. Each dictionary represents an entry in the MAC Address
        Table, having the following keys:
            * mac (string)
            * interface (string)
            * vlan (int)
            * active (boolean)
            * static (boolean)
            * moves (int)
            * last_move (float)
        However, please note that not all vendors provide all these details.
        E.g.: field last_move is not available on JUNOS devices etc.
        Example::
            [
                {
                    'mac'       : '00:1C:58:29:4A:71',
                    'interface' : 'Ethernet47',
                    'vlan'      : 100,
                    'static'    : False,
                    'active'    : True,
                    'moves'     : 1,
                    'last_move' : 1454417742.58
                },
                {
                    'mac'       : '00:1C:58:29:4A:C1',
                    'interface' : 'xe-1/0/1',
                    'vlan'       : 100,
                    'static'    : False,
                    'active'    : True,
                    'moves'     : 2,
                    'last_move' : 1453191948.11
                },
                {
                    'mac'       : '00:1C:58:29:4A:C2',
                    'interface' : 'ae7.900',
                    'vlan'      : 900,
                    'static'    : False,
                    'active'    : True,
                    'moves'     : None,
                    'last_move' : None
                }
            ]
        """
        self.n.getMAC()
        res = []
        for a in self.n.mac:
            res.append(
                {
                    'mac'       : a["MAC"].replace("-", ":"),
                    'interface' : self._port_fmt(a["Port"]),
                    'vlan'      : a["VLAN_ID"],
                    'static'    : False,
                    'active'    : True,
                    'moves'     : None,
                    'last_move' : None
                }
            )
        return res

    def get_config(
        self, retrieve: str = "all", full: bool = False, sanitized: bool = False
    ) -> models.ConfigDict:
        """
        Return the configuration of a device.
        Args:
            retrieve(string): Which configuration type you want to populate, default is all of them.
                              The rest will be set to "".
            full(bool): Retrieve all the configuration. For instance, on ios, "sh run all".
            sanitized(bool): Remove secret data. Default: ``False``.
        Returns:
          The object returned is a dictionary with a key for each configuration store:
            - running(string) - Representation of the native running configuration
            - candidate(string) - Representation of the native candidate configuration. If the
              device doesnt differentiate between running and startup configuration this will an
              empty string
            - startup(string) - Representation of the native startup configuration. If the
              device doesnt differentiate between running and startup configuration this will an
              empty string
        """
        self.n.getConfig()
        return {
            "running": json.dumps(self.n.config, indent=2),
            "candidate": "",
            "startup": ""
        }

    def load_replace_candidate(
        self, filename: Optional[str] = None, config: Optional[str] = None
    ) -> None:
        """
        Populates the candidate configuration. You can populate it from a file or from a string.
        If you send both a filename and a string containing the configuration, the file takes
        precedence.
        If you use this method the existing configuration will be replaced entirely by the
        candidate configuration once you commit the changes. This method will not change the
        configuration by itself.
        :param filename: Path to the file containing the desired configuration. By default is None.
        :param config: String containing the desired configuration.
        :raise ReplaceConfigException: If there is an error on the configuration sent.
        """
        if(filename is not None):
            with open(filename, 'r') as f:
                config = f.read()
        json_config = json.loads(config)
        self.n.getConfig()
        self.n.replaceConfig(json_config)

    def load_merge_candidate(
        self, filename: Optional[str] = None, config: Optional[str] = None
    ) -> None:
        """
        Populates the candidate configuration. You can populate it from a file or from a string.
        If you send both a filename and a string containing the configuration, the file takes
        precedence.
        If you use this method the existing configuration will be merged with the candidate
        configuration once you commit the changes. This method will not change the configuration
        by itself.
        :param filename: Path to the file containing the desired configuration. By default is None.
        :param config: String containing the desired configuration.
        :raise MergeConfigException: If there is an error on the configuration sent.
        """
        if(filename is not None):
            with open(filename, 'r') as f:
                config = f.read()
        json_config = json.loads(config)
        self.n.getConfig()
        self.n.mergeConfig(json_config)

    def compare_config(self) -> str:
        """
        :return: A string showing the difference between the running configuration and the \
        candidate configuration. The running_config is loaded automatically just before doing the \
        comparison so there is no need for you to do it.
        """
        diff = self.n.getDiff()
        return json.dumps(diff, indent=2)

    def commit_config(self, message: str = "", revert_in: Optional[int] = None) -> None:
        """
        Commits the changes requested by the method load_replace_candidate or load_merge_candidate.
        NAPALM drivers that support 'commit confirm' should cause self.has_pending_commit
        to return True when a 'commit confirm' is in progress.
        Implementations should raise an exception if commit_config is called multiple times while a
        'commit confirm' is pending.
        :param message: Optional - configuration session commit message
        :type message: str
        :param revert_in: Optional - number of seconds before the configuration will be reverted
        :type revert_in: int|None
        """
        self.n.putConfig()
