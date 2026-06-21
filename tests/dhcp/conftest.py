"""Local conftest for DHCP tests — provides sim_dhcp fixture."""
from __future__ import annotations

import pytest

from cpe_ta.infra.sim.sim_dhcp import SimDHCPService


@pytest.fixture
def sim_dhcp() -> SimDHCPService:
    """Fresh SimDHCPService per test."""
    return SimDHCPService()
