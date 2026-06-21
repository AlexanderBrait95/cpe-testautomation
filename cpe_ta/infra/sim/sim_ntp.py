"""Simulated NTP service for headless testing."""
from __future__ import annotations

# Fixed deterministic timestamp: 2025-06-15 ~10:26:40 UTC
_FIXED_TIMESTAMP: float = 1750000000.0


class SimNTPService:
    """Deterministic NTP simulator — always returns a fixed timestamp."""

    def __init__(self, fixed_time: float = _FIXED_TIMESTAMP, synchronized: bool = True) -> None:
        self._fixed_time = fixed_time
        self._synchronized = synchronized

    def get_time(self) -> float:
        return self._fixed_time

    def is_synchronized(self) -> bool:
        return self._synchronized
