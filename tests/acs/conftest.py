"""Local conftest for ACS tests — provides sim_acs and sim_dut fixtures."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE
from cpe_ta.infra.sim.sim_acs import SimACSService

_DEFAULT_SERIAL = "SIM000001"


@pytest.fixture
def sim_acs() -> SimACSService:
    """Fresh SimACSService per test."""
    return SimACSService()


@pytest.fixture
def sim_dut() -> SimCPE:
    """Fresh SimCPE per test."""
    dut = SimCPE(dut_id="acs-test-dut")
    dut.factory_reset()
    return dut


@pytest.fixture
def bootstrapped_acs(sim_acs: SimACSService) -> tuple[SimACSService, str]:
    """SimACSService with a bootstrapped CPE; returns (acs, serial)."""
    serial = _DEFAULT_SERIAL
    sim_acs.bootstrap_cpe(serial)
    return sim_acs, serial
