"""T25 — WiFi SSID configuration tests (headless)."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE

pytestmark = pytest.mark.headless

_SSID_PARAM = "Device.WiFi.SSID.1.SSID"
_HIDDEN_PARAM = "Device.WiFi.SSID.1.X_Hidden"
_GUEST_SSID_PARAM = "Device.WiFi.SSID.2.SSID"
_RADIO1_PARAM = "Device.WiFi.Radio.1.Enable"
_RADIO2_PARAM = "Device.WiFi.Radio.2.Enable"


def test_ssid_visible(sim_dut: SimCPE) -> None:
    """hidden=False → SSID should be visible (param stored as False)."""
    sim_dut.set_parameter(_HIDDEN_PARAM, False)
    assert sim_dut.get_parameter(_HIDDEN_PARAM) is False


def test_ssid_hidden(sim_dut: SimCPE) -> None:
    """hidden=True → SSID broadcast disabled (param stored as True)."""
    sim_dut.set_parameter(_HIDDEN_PARAM, True)
    assert sim_dut.get_parameter(_HIDDEN_PARAM) is True


def test_ssid_change(sim_dut: SimCPE) -> None:
    """Change the primary SSID name and verify the new value is stored."""
    new_ssid = "MyNewNetwork"
    sim_dut.set_parameter(_SSID_PARAM, new_ssid)
    assert sim_dut.get_parameter(_SSID_PARAM) == new_ssid


def test_guest_ssid(sim_dut: SimCPE) -> None:
    """Configure a guest SSID and verify it is stored."""
    guest_ssid = "GuestNet"
    sim_dut.set_parameter(_GUEST_SSID_PARAM, guest_ssid)
    assert sim_dut.get_parameter(_GUEST_SSID_PARAM) == guest_ssid


def test_band_2_4(sim_dut: SimCPE) -> None:
    """Enable Radio 1 (2.4 GHz) and verify the Enable param is True."""
    sim_dut.set_parameter(_RADIO1_PARAM, True)
    assert sim_dut.get_parameter(_RADIO1_PARAM) is True


def test_band_5(sim_dut: SimCPE) -> None:
    """Enable Radio 2 (5 GHz) and verify the Enable param is True."""
    sim_dut.set_parameter(_RADIO2_PARAM, True)
    assert sim_dut.get_parameter(_RADIO2_PARAM) is True
