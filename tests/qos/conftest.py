"""Local conftest for QoS tests — provides sim_traffic fixture."""
from __future__ import annotations

import pytest

from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint


@pytest.fixture
def sim_traffic() -> SimTrafficEndpoint:
    """Fresh SimTrafficEndpoint per test."""
    return SimTrafficEndpoint()
