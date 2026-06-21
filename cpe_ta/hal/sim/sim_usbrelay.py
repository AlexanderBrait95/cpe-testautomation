"""In-memory USB Relay simulator — no real hardware required."""

from __future__ import annotations

from cpe_ta.core.errors import HardwareError


class SimUSBRelay:
    """Headless USBRelay implementation for use in unit/integration tests."""

    def __init__(self) -> None:
        # channel → state (True = closed/on, False = open/off)
        self.channels: dict[int, bool] = {}
        # log of (channel, duration_s) pulse calls
        self.pulse_log: list[tuple[int, float]] = []
        # error injection flags
        self.error_inject: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # USBRelay Protocol implementation
    # ------------------------------------------------------------------

    def set_channel(self, channel: int, state: bool) -> None:
        if self.error_inject.get("fail_set_channel"):
            raise HardwareError(f"Injected error: set_channel failed for channel {channel}")
        self.channels[channel] = state

    def pulse(self, channel: int, duration_s: float = 0.5) -> None:
        """Record a pulse operation (no real delay in simulator)."""
        if self.error_inject.get("fail_pulse"):
            raise HardwareError(f"Injected error: pulse failed for channel {channel}")
        self.pulse_log.append((channel, duration_s))
        # Simulate: briefly activate then deactivate
        self.channels[channel] = True
        self.channels[channel] = False

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------

    def inject_error(self, key: str, value: bool) -> None:
        """Enable or disable a named fault injection flag."""
        self.error_inject[key] = value
