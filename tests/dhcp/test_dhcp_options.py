"""T28 — DHCP option configuration tests (headless)."""
from __future__ import annotations

import pytest

from cpe_ta.infra.sim.sim_dhcp import SimDHCPService

pytestmark = pytest.mark.headless


def test_option_60_vendor_class(sim_dhcp: SimDHCPService) -> None:
    """DHCP option 60 (Vendor Class Identifier) must be stored correctly."""
    sim_dhcp.set_option(60, "VendorClass")
    options = sim_dhcp.get_options()
    assert options[60] == "VendorClass"


def test_option_43_vendor_specific(sim_dhcp: SimDHCPService) -> None:
    """DHCP option 43 (Vendor Specific) must be stored correctly."""
    sim_dhcp.set_option(43, "01:01:01")
    options = sim_dhcp.get_options()
    assert options[43] == "01:01:01"


def test_option_121_classless_static(sim_dhcp: SimDHCPService) -> None:
    """DHCP option 121 (Classless Static Route) must be stored correctly."""
    route_val = "192.168.2.0/24:192.168.1.1"
    sim_dhcp.set_option(121, route_val)
    options = sim_dhcp.get_options()
    assert options[121] == route_val


def test_option_15_domain_name(sim_dhcp: SimDHCPService) -> None:
    """DHCP option 15 (Domain Name) must be stored correctly."""
    sim_dhcp.set_option(15, "example.com")
    options = sim_dhcp.get_options()
    assert options[15] == "example.com"


def test_option_42_ntp(sim_dhcp: SimDHCPService) -> None:
    """DHCP option 42 (NTP Server) must be stored correctly."""
    sim_dhcp.set_option(42, "192.168.1.1")
    options = sim_dhcp.get_options()
    assert options[42] == "192.168.1.1"


def test_option_125_vendor_identifying(sim_dhcp: SimDHCPService) -> None:
    """DHCP option 125 (Vendor-Identifying Vendor-Specific) must be stored."""
    vi_val = "enterprise:00000368:featureflags"
    sim_dhcp.set_option(125, vi_val)
    options = sim_dhcp.get_options()
    assert options[125] == vi_val
