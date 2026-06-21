"""Kea DHCP adapter stub — real DHCP implementation."""
from __future__ import annotations

from cpe_ta.infra.base import DHCPLease


class KeaDHCPAdapter:
    """Adapter for ISC Kea DHCP server. All methods raise NotImplementedError until connected."""

    def __init__(self, host: str, port: int = 8000) -> None:
        self._host = host
        self._port = port

    def set_pool(self, subnet: str, start: str, end: str, lease_time_s: int = 86400) -> None:
        raise NotImplementedError("Connect to Kea DHCP")

    def add_static_lease(self, mac: str, ip: str) -> None:
        raise NotImplementedError("Connect to Kea DHCP")

    def get_leases(self) -> list[DHCPLease]:
        raise NotImplementedError("Connect to Kea DHCP")

    def set_option(self, option_code: int, value: str) -> None:
        raise NotImplementedError("Connect to Kea DHCP")

    def flush_leases(self) -> None:
        raise NotImplementedError("Connect to Kea DHCP")
