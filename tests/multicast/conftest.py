"""Local conftest for multicast tests — provides sim_dut fixture."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE


@pytest.fixture
def sim_dut() -> SimCPE:
    """Fresh SimCPE per test."""
    dut = SimCPE(dut_id="multicast-test-dut")
    dut.factory_reset()
    return dut
