"""T27 — NAT / Firewall configuration tests (headless)."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE

pytestmark = pytest.mark.headless

_NAT_PARAM = "Device.NAT.Enable"
_PF_PROTO_PARAM = "Device.NAT.PortMapping.1.Protocol"
_PF_EPORT_PARAM = "Device.NAT.PortMapping.1.ExternalPort"
_PF_IPORT_PARAM = "Device.NAT.PortMapping.1.InternalPort"
_PF_IHOST_PARAM = "Device.NAT.PortMapping.1.InternalClient"
_FW_PARAM = "Device.Firewall.Enable"
_FW6_PARAM = "Device.Firewall.X_IPv6_Enable"
_UPNP_PARAM = "Device.UPnP.Device.Enable"


def test_nat_enabled(sim_dut: SimCPE) -> None:
    """Setting NAT.Enable=True must be stored and read back as True."""
    sim_dut.set_parameter(_NAT_PARAM, True)
    assert sim_dut.get_parameter(_NAT_PARAM) is True


def test_port_forwarding_add(sim_dut: SimCPE) -> None:
    """Add a port-forwarding entry and verify all sub-parameters are stored."""
    sim_dut.set_parameter(_PF_PROTO_PARAM, "TCP")
    sim_dut.set_parameter(_PF_EPORT_PARAM, 8080)
    sim_dut.set_parameter(_PF_IPORT_PARAM, 80)
    sim_dut.set_parameter(_PF_IHOST_PARAM, "192.168.1.100")

    assert sim_dut.get_parameter(_PF_PROTO_PARAM) == "TCP"
    assert sim_dut.get_parameter(_PF_EPORT_PARAM) == 8080
    assert sim_dut.get_parameter(_PF_IPORT_PARAM) == 80
    assert sim_dut.get_parameter(_PF_IHOST_PARAM) == "192.168.1.100"


def test_firewall_default_deny_ipv4(sim_dut: SimCPE) -> None:
    """Enable the IPv4 firewall and verify the stored value."""
    sim_dut.set_parameter(_FW_PARAM, True)
    assert sim_dut.get_parameter(_FW_PARAM) is True


def test_firewall_default_deny_ipv6(sim_dut: SimCPE) -> None:
    """Enable the IPv6 firewall parameter and verify the stored value."""
    sim_dut.set_parameter(_FW6_PARAM, True)
    assert sim_dut.get_parameter(_FW6_PARAM) is True


def test_upnp_config(sim_dut: SimCPE) -> None:
    """Configure UPnP enable parameter and verify it is stored."""
    sim_dut.set_parameter(_UPNP_PARAM, True)
    assert sim_dut.get_parameter(_UPNP_PARAM) is True
