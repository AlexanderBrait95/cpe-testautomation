"""T25 / T35 — WiFi RF tests — require physical RF chamber (hardware-deferred)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.hardware


def test_rf_throughput_2_4() -> None:
    """Measure actual 2.4 GHz throughput in an RF shielded chamber."""
    pytest.skip("Requires RF chamber and a real WiFi client device")


def test_rf_roaming_11r() -> None:
    """Test 802.11r fast BSS transition between multiple APs."""
    pytest.skip("Requires multiple physical APs with 802.11r support")


def test_dfs_radar_detection() -> None:
    """Test DFS radar detection and channel switch behaviour."""
    pytest.skip("Requires RF signal generator capable of radar simulation")
