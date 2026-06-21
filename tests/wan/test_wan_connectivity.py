"""T27 — WAN connectivity / provisioning tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE

pytestmark = [pytest.mark.headless, pytest.mark.smoke]

_WAN_MODE_PARAM = "Device.X_WAN.Mode"
_WAN_USER_PARAM = "Device.PPP.Interface.1.Username"
_WAN_PASS_PARAM = "Device.PPP.Interface.1.Password"
_NTP_PARAM = "Device.Time.NTPServer1"
_DNS1_PARAM = "Device.DNS.Client.Server.1.DNSServer"
_DNS2_PARAM = "Device.DNS.Client.Server.2.DNSServer"


def test_pppoe_state_machine(sim_dut: SimCPE) -> None:
    """Set WAN mode to PPPoE, configure credentials and verify both."""
    sim_dut.set_parameter(_WAN_MODE_PARAM, "PPPoE")
    assert sim_dut.get_parameter(_WAN_MODE_PARAM) == "PPPoE"

    sim_dut.set_parameter(_WAN_USER_PARAM, "user@isp.at")
    sim_dut.set_parameter(_WAN_PASS_PARAM, "pppoe-secret")

    assert sim_dut.get_parameter(_WAN_USER_PARAM) == "user@isp.at"
    assert sim_dut.get_parameter(_WAN_PASS_PARAM) == "pppoe-secret"


def test_ipoe_dhcp(sim_dut: SimCPE) -> None:
    """Set WAN mode to IPoE and verify get_wan_ip returns a non-None value."""
    sim_dut.set_parameter(_WAN_MODE_PARAM, "IPoE")
    assert sim_dut.get_parameter(_WAN_MODE_PARAM) == "IPoE"
    # Sim always assigns a WAN IP after factory_reset
    assert sim_dut.get_wan_ip() is not None


def test_wan_ip_assigned(sim_dut: SimCPE) -> None:
    """After factory_reset the sim DUT must report a valid WAN IP."""
    wan_ip = sim_dut.get_wan_ip()
    assert wan_ip is not None
    # Must look like an IP address (contains dots)
    assert "." in wan_ip


def test_ntp_sync_config(sim_dut: SimCPE) -> None:
    """Configure an NTP server parameter and verify it is stored."""
    sim_dut.set_parameter(_NTP_PARAM, "pool.ntp.org")
    assert sim_dut.get_parameter(_NTP_PARAM) == "pool.ntp.org"


def test_dns_config(sim_dut: SimCPE) -> None:
    """Configure primary and secondary DNS servers and verify both."""
    sim_dut.set_parameter(_DNS1_PARAM, "8.8.8.8")
    sim_dut.set_parameter(_DNS2_PARAM, "8.8.4.4")

    assert sim_dut.get_parameter(_DNS1_PARAM) == "8.8.8.8"
    assert sim_dut.get_parameter(_DNS2_PARAM) == "8.8.4.4"
