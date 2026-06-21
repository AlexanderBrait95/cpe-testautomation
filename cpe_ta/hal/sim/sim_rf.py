"""In-memory RF Attenuator simulator — no real hardware required."""

from __future__ import annotations

from cpe_ta.core.errors import HardwareError


class SimRFAttenuator:
    """Headless RFAttenuator implementation for use in unit/integration tests."""

    def __init__(self) -> None:
        # channel → attenuation in dB
        self.attenuation: dict[int, float] = {}
        self.isolated: bool = False
        # error injection flags
        self.error_inject: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # RFAttenuator Protocol implementation
    # ------------------------------------------------------------------

    def set_attenuation_db(self, channel: int, db: float) -> None:
        if self.error_inject.get("fail_set_attenuation"):
            raise HardwareError(f"Injected error: set_attenuation_db failed for channel {channel}")
        self.attenuation[channel] = db

    def get_attenuation(self, channel: int) -> float:
        return self.attenuation.get(channel, 0.0)

    def isolate(self, enabled: bool) -> None:
        if self.error_inject.get("fail_isolate"):
            raise HardwareError("Injected error: isolate failed")
        self.isolated = enabled

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------

    def inject_error(self, key: str, value: bool) -> None:
        """Enable or disable a named fault injection flag."""
        self.error_inject[key] = value
