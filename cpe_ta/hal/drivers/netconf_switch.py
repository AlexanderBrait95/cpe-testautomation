"""NETCONF Switch driver skeleton — requires ncclient (not in base requirements)."""

from __future__ import annotations

# Lazy import: ncclient is optional hardware-specific dependency
try:
    from ncclient import manager as ncclient_manager  # type: ignore[import-untyped]  # noqa: F401

    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

from cpe_ta.hal.base import PortStats


class NetconfSwitch:
    """Real Switch driver using NETCONF (ncclient).

    Connect this to physical managed switches that expose a NETCONF interface
    (RFC 6241), typically running YANG data models (ietf-interfaces, etc.).

    Raises
    ------
    NotImplementedError
        All methods — connect to real hardware to implement.
    """

    def __init__(
        self,
        host: str,
        port: int = 830,
        username: str = "admin",
        password: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    def port_enable(self, port_id: str) -> None:
        # TODO: edit-config with ietf-interfaces:enabled = true
        raise NotImplementedError("NETCONF driver: connect to real hardware")

    def port_disable(self, port_id: str) -> None:
        # TODO: edit-config with ietf-interfaces:enabled = false
        raise NotImplementedError("NETCONF driver: connect to real hardware")

    def set_speed_duplex(self, port_id: str, speed_mbps: int, full_duplex: bool) -> None:
        # TODO: vendor YANG augmentation for speed/duplex
        raise NotImplementedError("NETCONF driver: connect to real hardware")

    def set_vlan(self, port_id: str, vlan_id: int, tagged: bool = False) -> None:
        # TODO: ieee802-dot1q-bridge YANG model
        raise NotImplementedError("NETCONF driver: connect to real hardware")

    def get_port_stats(self, port_id: str) -> PortStats:
        # TODO: get-data from ietf-interfaces operational state
        raise NotImplementedError("NETCONF driver: connect to real hardware")

    def set_mirror(self, source_port: str, dest_port: str, enabled: bool) -> None:
        # TODO: vendor-specific YANG for port mirroring
        raise NotImplementedError("NETCONF driver: connect to real hardware")
