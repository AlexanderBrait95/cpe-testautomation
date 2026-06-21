"""Simulated DHCP service for headless testing."""
from __future__ import annotations

from cpe_ta.infra.base import DHCPLease


class SimDHCPService:
    """In-memory DHCP lease pool and option store."""

    def __init__(self) -> None:
        self._pool: dict[str, str] = {}  # config: subnet, start, end, lease_time_s
        self._pool_config: dict[str, str | int] = {}
        self._static_leases: dict[str, str] = {}  # mac → ip
        self._options: dict[int, str] = {}  # option_code → value

    def set_pool(self, subnet: str, start: str, end: str, lease_time_s: int = 86400) -> None:
        self._pool_config = {
            "subnet": subnet,
            "start": start,
            "end": end,
            "lease_time_s": lease_time_s,
        }

    def add_static_lease(self, mac: str, ip: str) -> None:
        self._static_leases[mac.lower()] = ip

    def get_leases(self) -> list[DHCPLease]:
        leases: list[DHCPLease] = []
        for mac, ip in self._static_leases.items():
            leases.append(DHCPLease(mac=mac, ip=ip, hostname="sim-host", lease_expires=9999999999.0))
        return leases

    def set_option(self, option_code: int, value: str) -> None:
        self._options[option_code] = value

    def flush_leases(self) -> None:
        self._static_leases.clear()

    # Test-helper accessors
    def get_pool_config(self) -> dict[str, str | int]:
        return dict(self._pool_config)

    def get_options(self) -> dict[int, str]:
        return dict(self._options)
