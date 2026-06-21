"""In-memory Switch simulator — no real hardware required."""

from __future__ import annotations

from typing import Any

from cpe_ta.core.errors import HardwareError
from cpe_ta.hal.base import PortStats


class SimSwitch:
    """Headless Switch implementation for use in unit/integration tests."""

    def __init__(self) -> None:
        # port_id → port state dict
        self.ports: dict[str, dict[str, Any]] = {}
        # source_port → dest_port mirror mapping
        self.mirrors: dict[str, str] = {}
        # error injection flags: key → bool
        self.error_inject: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create_port(self, port_id: str) -> dict[str, Any]:
        if port_id not in self.ports:
            self.ports[port_id] = {
                "enabled": True,
                "speed": 1000,
                "duplex": True,
                "vlan": 1,
                "tagged": False,
                "tx_frames": 0,
                "rx_frames": 0,
            }
        return self.ports[port_id]

    # ------------------------------------------------------------------
    # Switch Protocol implementation
    # ------------------------------------------------------------------

    def port_enable(self, port_id: str) -> None:
        if self.error_inject.get("fail_port_enable"):
            raise HardwareError(f"Injected error: port_enable failed for {port_id}")
        self._get_or_create_port(port_id)["enabled"] = True

    def port_disable(self, port_id: str) -> None:
        if self.error_inject.get("fail_port_disable"):
            raise HardwareError(f"Injected error: port_disable failed for {port_id}")
        self._get_or_create_port(port_id)["enabled"] = False

    def set_speed_duplex(self, port_id: str, speed_mbps: int, full_duplex: bool) -> None:
        port = self._get_or_create_port(port_id)
        port["speed"] = speed_mbps
        port["duplex"] = full_duplex

    def set_vlan(self, port_id: str, vlan_id: int, tagged: bool = False) -> None:
        port = self._get_or_create_port(port_id)
        port["vlan"] = vlan_id
        port["tagged"] = tagged

    def get_port_stats(self, port_id: str) -> PortStats:
        port = self._get_or_create_port(port_id)
        return PortStats(
            tx_frames=port["tx_frames"],
            rx_frames=port["rx_frames"],
            tx_errors=0,
            rx_errors=0,
            speed_mbps=port["speed"],
            duplex_full=port["duplex"],
        )

    def set_mirror(self, source_port: str, dest_port: str, enabled: bool) -> None:
        if enabled:
            self.mirrors[source_port] = dest_port
        else:
            self.mirrors.pop(source_port, None)

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------

    def inject_error(self, key: str, value: bool) -> None:
        """Enable or disable a named fault injection flag."""
        self.error_inject[key] = value
