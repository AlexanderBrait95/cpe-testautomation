"""Simulated SIP service for headless testing."""
from __future__ import annotations

from cpe_ta.infra.base import SIPCallResult


class SimSIPService:
    """In-memory SIP registrar and call simulator."""

    DEFAULT_CODEC = "G.711"
    DEFAULT_MOS = 4.2

    def __init__(self) -> None:
        # extension → password
        self._registrations: dict[str, str] = {}
        self._call_counter: int = 0
        self._active_calls: dict[str, dict[str, object]] = {}

    def register(self, extension: str, password: str) -> None:
        self._registrations[extension] = password

    def make_call(self, from_ext: str, to_ext: str, duration_s: float = 5.0) -> SIPCallResult:
        self._call_counter += 1
        call_id = f"call-{self._call_counter}"
        self._active_calls[call_id] = {
            "from": from_ext,
            "to": to_ext,
            "duration_s": duration_s,
        }
        return SIPCallResult(
            success=True,
            duration_s=duration_s,
            codec=self.DEFAULT_CODEC,
            mos_score=self.DEFAULT_MOS,
        )

    def hangup(self, call_id: str) -> None:
        self._active_calls.pop(call_id, None)

    # Test-helper accessors
    def is_registered(self, extension: str) -> bool:
        return extension in self._registrations

    def get_active_calls(self) -> dict[str, dict[str, object]]:
        return dict(self._active_calls)
