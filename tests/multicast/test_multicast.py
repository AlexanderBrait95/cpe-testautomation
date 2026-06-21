"""T29 — Multicast / IGMP / MLD state-machine tests (headless, smoke)."""
from __future__ import annotations

import time

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE

pytestmark = [pytest.mark.headless, pytest.mark.smoke]

_IGMP_ENABLE_PARAM = "Device.Routing.RIP.1.X_IGMP_Enable"
_IGMP_JOIN_PARAM = "Device.IP.Interface.1.X_IGMP_Group"
_IGMP_VERSION_PARAM = "Device.IP.Interface.1.X_IGMP_Version"
_MLD_PARAM = "Device.IP.Interface.1.X_MLD_Enable"
_MLD_VERSION_PARAM = "Device.IP.Interface.1.X_MLD_Version"
_IGMP_LEAVE_PARAM = "Device.IP.Interface.1.X_IGMP_Leave"


def test_igmpv2_join(sim_dut: SimCPE) -> None:
    """Enable IGMP and set an IGMPv2 join group — both params stored."""
    sim_dut.set_parameter(_IGMP_ENABLE_PARAM, True)
    sim_dut.set_parameter(_IGMP_JOIN_PARAM, "239.1.1.1")

    assert sim_dut.get_parameter(_IGMP_ENABLE_PARAM) is True
    assert sim_dut.get_parameter(_IGMP_JOIN_PARAM) == "239.1.1.1"


def test_igmpv3_join(sim_dut: SimCPE) -> None:
    """Configure IGMPv3 mode and a multicast join group."""
    sim_dut.set_parameter(_IGMP_ENABLE_PARAM, True)
    sim_dut.set_parameter(_IGMP_VERSION_PARAM, 3)
    sim_dut.set_parameter(_IGMP_JOIN_PARAM, "239.1.1.2")

    assert sim_dut.get_parameter(_IGMP_VERSION_PARAM) == 3
    assert sim_dut.get_parameter(_IGMP_JOIN_PARAM) == "239.1.1.2"


def test_mld_v1_join(sim_dut: SimCPE) -> None:
    """Enable MLD (IPv6 multicast) and configure MLDv1."""
    sim_dut.set_parameter(_MLD_PARAM, True)
    sim_dut.set_parameter(_MLD_VERSION_PARAM, 1)

    assert sim_dut.get_parameter(_MLD_PARAM) is True
    assert sim_dut.get_parameter(_MLD_VERSION_PARAM) == 1


def test_mld_v2_join(sim_dut: SimCPE) -> None:
    """Enable MLD and configure MLDv2."""
    sim_dut.set_parameter(_MLD_PARAM, True)
    sim_dut.set_parameter(_MLD_VERSION_PARAM, 2)

    assert sim_dut.get_parameter(_MLD_VERSION_PARAM) == 2


def test_multicast_leave(sim_dut: SimCPE) -> None:
    """After a join, set a leave parameter — must be stored."""
    sim_dut.set_parameter(_IGMP_ENABLE_PARAM, True)
    sim_dut.set_parameter(_IGMP_JOIN_PARAM, "239.1.1.3")
    sim_dut.set_parameter(_IGMP_LEAVE_PARAM, "239.1.1.3")

    assert sim_dut.get_parameter(_IGMP_LEAVE_PARAM) == "239.1.1.3"


def test_parallel_streams(sim_dut: SimCPE) -> None:
    """Configure 5 multicast groups and verify all are individually stored."""
    groups = [f"239.1.1.{i}" for i in range(1, 6)]
    for i, group in enumerate(groups, start=1):
        param = f"Device.IP.Interface.1.X_IGMP_Group_{i}"
        sim_dut.set_parameter(param, group)

    for i, group in enumerate(groups, start=1):
        param = f"Device.IP.Interface.1.X_IGMP_Group_{i}"
        assert sim_dut.get_parameter(param) == group


def test_zap_time_metric(sim_dut: SimCPE) -> None:
    """Simulated zap-time (param switch) must complete in under 1 second."""
    start = time.monotonic()
    # Simulate channel zap: leave old group, join new group
    sim_dut.set_parameter(_IGMP_LEAVE_PARAM, "239.1.1.1")
    sim_dut.set_parameter(_IGMP_JOIN_PARAM, "239.1.1.2")
    elapsed = time.monotonic() - start
    assert elapsed < 1.0, f"Zap-time exceeded 1s: {elapsed:.4f}s"
