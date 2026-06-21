"""T28 — DHCP basic pool and lease tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.infra.sim.sim_dhcp import SimDHCPService

pytestmark = [pytest.mark.headless, pytest.mark.smoke]


def test_set_pool(sim_dhcp: SimDHCPService) -> None:
    """set_pool stores the correct subnet, start, and end addresses."""
    sim_dhcp.set_pool("192.168.1.0/24", "192.168.1.100", "192.168.1.200")
    config = sim_dhcp.get_pool_config()
    assert config["subnet"] == "192.168.1.0/24"
    assert config["start"] == "192.168.1.100"
    assert config["end"] == "192.168.1.200"


def test_static_lease(sim_dhcp: SimDHCPService) -> None:
    """add_static_lease stores the mapping and get_leases returns it."""
    mac = "aa:bb:cc:dd:ee:ff"
    ip = "192.168.1.50"
    sim_dhcp.add_static_lease(mac, ip)
    leases = sim_dhcp.get_leases()
    assert len(leases) >= 1
    macs = [lease.mac for lease in leases]
    assert mac.lower() in macs


def test_dynamic_allocation(sim_dhcp: SimDHCPService) -> None:
    """After set_pool the service has a valid pool config structure."""
    sim_dhcp.set_pool("192.168.1.0/24", "192.168.1.100", "192.168.1.200")
    config = sim_dhcp.get_pool_config()
    assert "subnet" in config
    assert "start" in config
    assert "end" in config
    assert "lease_time_s" in config


def test_flush_leases(sim_dhcp: SimDHCPService) -> None:
    """flush_leases must empty all previously added static leases."""
    sim_dhcp.add_static_lease("11:22:33:44:55:66", "192.168.1.55")
    sim_dhcp.flush_leases()
    leases = sim_dhcp.get_leases()
    assert leases == []


def test_default_subnet_10(sim_dhcp: SimDHCPService) -> None:
    """set_pool with 10.x subnet must store the correct subnet."""
    sim_dhcp.set_pool("10.0.0.0/24", "10.0.0.100", "10.0.0.200")
    config = sim_dhcp.get_pool_config()
    assert config["subnet"] == "10.0.0.0/24"


def test_default_subnet_192_168_0(sim_dhcp: SimDHCPService) -> None:
    """set_pool with 192.168.0.x subnet must store the correct start/end."""
    sim_dhcp.set_pool("192.168.0.0/24", "192.168.0.100", "192.168.0.200")
    config = sim_dhcp.get_pool_config()
    assert config["start"] == "192.168.0.100"
    assert config["end"] == "192.168.0.200"


def test_default_subnet_192_168_1(sim_dhcp: SimDHCPService) -> None:
    """set_pool with 192.168.1.x subnet must store correctly."""
    sim_dhcp.set_pool("192.168.1.0/24", "192.168.1.2", "192.168.1.254")
    config = sim_dhcp.get_pool_config()
    assert config["subnet"] == "192.168.1.0/24"
