"""T33 / T35 — Soak long-run tests — require physical hardware (hardware-deferred)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.hardware


def test_soak_24h() -> None:
    """24-hour continuous soak test on real hardware."""
    pytest.skip("Requires 24h test window and real hardware")


def test_soak_wifi_lan_voice() -> None:
    """24-hour WiFi + LAN + VoIP combined soak test."""
    pytest.skip("Requires RF chamber + VoIP hardware")
