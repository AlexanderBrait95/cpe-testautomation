"""Local conftest for stress tests — provides sim_dut and sim_traffic fixtures."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE
from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint


@pytest.fixture
def sim_dut() -> SimCPE:
    """Fresh SimCPE per test."""
    dut = SimCPE(dut_id="stress-test-dut")
    dut.factory_reset()
    return dut


@pytest.fixture
def sim_traffic() -> SimTrafficEndpoint:
    """Fresh SimTrafficEndpoint per test."""
    return SimTrafficEndpoint()
