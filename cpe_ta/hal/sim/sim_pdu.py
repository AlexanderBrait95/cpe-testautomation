"""In-memory PDU simulator — no real hardware required."""

from __future__ import annotations

from typing import Any

from cpe_ta.core.errors import HardwareError
from cpe_ta.hal.base import OutletState


class SimPDU:
    """Headless PDU implementation for use in unit/integration tests."""

    def __init__(self) -> None:
        # outlet_id → outlet state dict
        self.outlets: dict[str, dict[str, Any]] = {}
        # error injection flags: key → bool
        self.error_inject: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create_outlet(self, outlet_id: str) -> dict[str, Any]:
        if outlet_id not in self.outlets:
            self.outlets[outlet_id] = {"powered": True}
        return self.outlets[outlet_id]

    # ------------------------------------------------------------------
    # PDU Protocol implementation
    # ------------------------------------------------------------------

    def power_on(self, outlet_id: str) -> None:
        if self.error_inject.get("fail_power_on"):
            raise HardwareError(f"Injected error: power_on failed for outlet {outlet_id}")
        self._get_or_create_outlet(outlet_id)["powered"] = True

    def power_off(self, outlet_id: str) -> None:
        if self.error_inject.get("fail_power_off"):
            raise HardwareError(f"Injected error: power_off failed for outlet {outlet_id}")
        self._get_or_create_outlet(outlet_id)["powered"] = False

    def power_cycle(self, outlet_id: str, delay_s: float = 2.0) -> None:
        """Toggle outlet off then on (immediate in simulator — no real sleep)."""
        if self.error_inject.get("fail_power_cycle"):
            raise HardwareError(f"Injected error: power_cycle failed for outlet {outlet_id}")
        outlet = self._get_or_create_outlet(outlet_id)
        outlet["powered"] = False
        # Intentionally no sleep in simulator — tests run without real delays
        outlet["powered"] = True

    def get_outlet_state(self, outlet_id: str) -> OutletState:
        outlet = self._get_or_create_outlet(outlet_id)
        return OutletState(outlet_id=outlet_id, powered=outlet["powered"])

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------

    def inject_error(self, key: str, value: bool) -> None:
        """Enable or disable a named fault injection flag."""
        self.error_inject[key] = value
