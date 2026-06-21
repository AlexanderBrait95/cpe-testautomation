"""T30 — IPv6 / Dual-Stack configuration tests (headless)."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE

pytestmark = pytest.mark.headless

_DHCPV6_PARAM = "Device.DHCPv6.Client.1.Enable"
_SLAAC_PARAM = "Device.IP.Interface.1.IPv6Enable"
_PD_PARAM = "Device.DHCPv6.Client.1.RequestedOptions"
_PD_LEN_PARAM = "Device.DHCPv6.Client.1.RequestAddresses"
_FW6_PARAM = "Device.Firewall.X_IPv6_Enable"
_DSLITE_PARAM = "Device.DSLite.InterfaceSetting.1.Enable"
_MAPT_PARAM = "Device.MAP.Domain.1.Enable"
_IPV4_ADDR_PARAM = "Device.IP.Interface.1.IPv4Address.1.IPAddress"
_IPV6_ADDR_PARAM = "Device.IP.Interface.1.IPv6Address.1.IPAddress"


@pytest.mark.parametrize("ip_mode", ["ipv4", "ipv6", "dual"])
def test_dhcpv6_config(sim_dut: SimCPE, ip_mode: str) -> None:
    """Enable or disable DHCPv6 depending on ip_mode and verify the param."""
    enable = ip_mode in ("ipv6", "dual")
    sim_dut.set_parameter(_DHCPV6_PARAM, enable)
    assert sim_dut.get_parameter(_DHCPV6_PARAM) is enable


def test_slaac_config(sim_dut: SimCPE) -> None:
    """Enable SLAAC (IPv6 stateless auto-configuration) and verify the param."""
    sim_dut.set_parameter(_SLAAC_PARAM, True)
    assert sim_dut.get_parameter(_SLAAC_PARAM) is True


def test_prefix_delegation(sim_dut: SimCPE) -> None:
    """Configure Prefix Delegation request and verify stored param."""
    sim_dut.set_parameter(_PD_PARAM, "IA_PD")
    assert sim_dut.get_parameter(_PD_PARAM) == "IA_PD"


def test_ipv6_firewall(sim_dut: SimCPE) -> None:
    """Enable IPv6 firewall and verify the stored param."""
    sim_dut.set_parameter(_FW6_PARAM, True)
    assert sim_dut.get_parameter(_FW6_PARAM) is True


@pytest.mark.parametrize("ip_mode", ["ipv6", "dual"])
def test_ds_lite_profile(sim_dut: SimCPE, ip_mode: str) -> None:
    """Configure DS-Lite — only applies when ip_mode != ipv4."""
    sim_dut.set_parameter(_DSLITE_PARAM, True)
    assert sim_dut.get_parameter(_DSLITE_PARAM) is True


def test_map_t_profile(sim_dut: SimCPE) -> None:
    """Configure MAP-T and verify the domain enable parameter."""
    sim_dut.set_parameter(_MAPT_PARAM, True)
    assert sim_dut.get_parameter(_MAPT_PARAM) is True


def test_dual_stack_wan(sim_dut: SimCPE) -> None:
    """In dual mode both IPv4 and IPv6 WAN address params must be set."""
    sim_dut.set_parameter(_IPV4_ADDR_PARAM, "100.64.1.1")
    sim_dut.set_parameter(_IPV6_ADDR_PARAM, "2001:db8::1")

    assert sim_dut.get_parameter(_IPV4_ADDR_PARAM) == "100.64.1.1"
    assert sim_dut.get_parameter(_IPV6_ADDR_PARAM) == "2001:db8::1"
