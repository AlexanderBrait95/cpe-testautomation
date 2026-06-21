"""SNMP Switch driver skeleton — requires pysnmp (not in base requirements)."""

from __future__ import annotations

# Lazy import: pysnmp is optional hardware-specific dependency
try:
    from pysnmp.hlapi import (  # type: ignore[import-untyped]  # noqa: F401
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        getCmd,
        setCmd,
    )

    HAS_PYSNMP = True
except ImportError:
    HAS_PYSNMP = False

from cpe_ta.hal.base import PortStats


class SNMPSwitch:
    """Real Switch driver using SNMP (pysnmp).

    Connect this to physical managed switches that expose the standard
    IF-MIB / BRIDGE-MIB over SNMPv2c.

    Raises
    ------
    NotImplementedError
        All methods — connect to real hardware to implement.
    """

    def __init__(self, host: str, port: int = 161, community: str = "public") -> None:
        self._host = host
        self._port = port
        self._community = community

    def port_enable(self, port_id: str) -> None:
        # TODO: send ifAdminStatus = up(1) via SNMP setCmd
        raise NotImplementedError("SNMP driver: connect to real hardware")

    def port_disable(self, port_id: str) -> None:
        # TODO: send ifAdminStatus = down(2) via SNMP setCmd
        raise NotImplementedError("SNMP driver: connect to real hardware")

    def set_speed_duplex(self, port_id: str, speed_mbps: int, full_duplex: bool) -> None:
        # TODO: vendor-specific MIB OIDs for speed/duplex config
        raise NotImplementedError("SNMP driver: connect to real hardware")

    def set_vlan(self, port_id: str, vlan_id: int, tagged: bool = False) -> None:
        # TODO: Q-BRIDGE-MIB dot1qPvid / dot1qVlanStaticEgressPorts
        raise NotImplementedError("SNMP driver: connect to real hardware")

    def get_port_stats(self, port_id: str) -> PortStats:
        # TODO: IF-MIB ifInOctets / ifOutOctets / ifInErrors / ifOutErrors
        raise NotImplementedError("SNMP driver: connect to real hardware")

    def set_mirror(self, source_port: str, dest_port: str, enabled: bool) -> None:
        # TODO: vendor-specific port-mirroring MIB
        raise NotImplementedError("SNMP driver: connect to real hardware")
