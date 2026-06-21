"""Local conftest for LAN tests — provides sim_switch and sim_dut fixtures."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE
from cpe_ta.hal.sim.sim_switch import SimSwitch


@pytest.fixture
def sim_switch() -> SimSwitch:
    """Fresh SimSwitch per test."""
    return SimSwitch()


@pytest.fixture
def sim_dut() -> SimCPE:
    """Fresh SimCPE per test."""
    dut = SimCPE(dut_id="lan-test-dut")
    dut.factory_reset()
    return dut
