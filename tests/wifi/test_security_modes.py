"""T25 — WiFi security mode tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE

pytestmark = [pytest.mark.headless, pytest.mark.smoke]

_SECURITY_PARAM = "Device.WiFi.AccessPoint.1.Security.ModeEnabled"
_PASSPHRASE_PARAM = "Device.WiFi.AccessPoint.1.Security.KeyPassphrase"


def test_mode_open(sim_dut: SimCPE) -> None:
    """Setting security mode to 'None' (open) must be stored correctly."""
    sim_dut.set_parameter(_SECURITY_PARAM, "None")
    assert sim_dut.get_parameter(_SECURITY_PARAM) == "None"


def test_mode_wpa2(sim_dut: SimCPE) -> None:
    """Setting security mode to WPA2-Personal must be stored correctly."""
    sim_dut.set_parameter(_SECURITY_PARAM, "WPA2-Personal")
    assert sim_dut.get_parameter(_SECURITY_PARAM) == "WPA2-Personal"


def test_mode_wpa3(sim_dut: SimCPE) -> None:
    """Setting WPA3-Personal is only tested if the DUT supports it."""
    if not sim_dut.capabilities.supports_wpa3:
        pytest.skip("DUT does not support WPA3")
    sim_dut.set_parameter(_SECURITY_PARAM, "WPA3-Personal")
    assert sim_dut.get_parameter(_SECURITY_PARAM) == "WPA3-Personal"


def test_mode_owe(sim_dut: SimCPE) -> None:
    """Setting Opportunistic Wireless Encryption (OWE) must be stored."""
    sim_dut.set_parameter(_SECURITY_PARAM, "OWE")
    assert sim_dut.get_parameter(_SECURITY_PARAM) == "OWE"


def test_wpa2_passphrase(sim_dut: SimCPE) -> None:
    """Write a passphrase, then read it back — must match exactly."""
    passphrase = "MySecurePass!42"
    sim_dut.set_parameter(_SECURITY_PARAM, "WPA2-Personal")
    sim_dut.set_parameter(_PASSPHRASE_PARAM, passphrase)
    assert sim_dut.get_parameter(_PASSPHRASE_PARAM) == passphrase


def test_mode_transition_wpa2_to_wpa3(sim_dut: SimCPE) -> None:
    """Transition from WPA2 → WPA3 and verify each step."""
    if not sim_dut.capabilities.supports_wpa3:
        pytest.skip("DUT does not support WPA3")

    sim_dut.set_parameter(_SECURITY_PARAM, "WPA2-Personal")
    assert sim_dut.get_parameter(_SECURITY_PARAM) == "WPA2-Personal"

    sim_dut.set_parameter(_SECURITY_PARAM, "WPA3-Personal")
    assert sim_dut.get_parameter(_SECURITY_PARAM) == "WPA3-Personal"
