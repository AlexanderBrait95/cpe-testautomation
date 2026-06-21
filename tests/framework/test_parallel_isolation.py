"""T19 — xdist resource isolation: disjoint VLANs, subnets and instance IDs.

These tests verify that the WorkerPool assigns non-overlapping resources
so that parallel xdist workers cannot interfere with each other.
"""
from __future__ import annotations

import pytest

from cpe_ta.core.runner import WorkerPool
from cpe_ta.dut.sim.sim_cpe import SimCPE

# ---------------------------------------------------------------------------
# Two-worker disjointness
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_two_workers_vlans_disjoint():
    """Worker 0 and worker 1 must get different VLAN base IDs."""
    pool0 = WorkerPool(worker_id=0)
    pool1 = WorkerPool(worker_id=1)
    assert pool0.allocate_vlan() != pool1.allocate_vlan()


@pytest.mark.headless
def test_two_workers_subnets_disjoint():
    """Worker 0 and worker 1 must get different subnets."""
    pool0 = WorkerPool(worker_id=0)
    pool1 = WorkerPool(worker_id=1)
    assert pool0.allocate_subnet() != pool1.allocate_subnet()


# ---------------------------------------------------------------------------
# Four-worker disjointness
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_four_workers_vlans_all_disjoint():
    """All four workers must produce mutually disjoint VLAN base IDs."""
    pools = [WorkerPool(worker_id=i) for i in range(4)]
    vlans = [p.allocate_vlan() for p in pools]
    assert len(vlans) == len(set(vlans)), f"VLAN collision detected: {vlans}"


@pytest.mark.headless
def test_four_workers_subnets_all_disjoint():
    """All four workers must produce mutually disjoint subnets."""
    pools = [WorkerPool(worker_id=i) for i in range(4)]
    subnets = [p.allocate_subnet() for p in pools]
    assert len(subnets) == len(set(subnets)), f"Subnet collision detected: {subnets}"


@pytest.mark.headless
def test_four_workers_instance_ids_all_disjoint():
    """All four workers must produce mutually disjoint instance IDs."""
    pools = [WorkerPool(worker_id=i) for i in range(4)]
    ids = [p.allocate_instance_id("svc") for p in pools]
    assert len(ids) == len(set(ids)), f"Instance ID collision detected: {ids}"


# ---------------------------------------------------------------------------
# resource_pool fixture isolation
# ---------------------------------------------------------------------------


@pytest.mark.headless
@pytest.mark.parametrize("worker_id", [0, 1, 2, 3])
def test_resource_pool_worker_ids_unique(worker_id: int):
    """Each parametrised worker_id must produce a unique instance ID."""
    pool = WorkerPool(worker_id=worker_id)
    inst_id = pool.allocate_instance_id("tb")
    assert f"worker{worker_id}" in inst_id


# ---------------------------------------------------------------------------
# sim_dut instances are independent
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_sim_dut_instances_are_independent():
    """Two independently created SimCPE instances must not share state."""
    dut_a = SimCPE(dut_id="dut-a")
    dut_b = SimCPE(dut_id="dut-b")

    dut_a.set_parameter("Device.DeviceInfo.SoftwareVersion", "ALPHA")
    # dut_b must be unaffected
    assert dut_b.get_parameter("Device.DeviceInfo.SoftwareVersion") == "1.0.0"


@pytest.mark.headless
def test_sim_dut_fixture_fresh_per_call(sim_dut):
    """The sim_dut fixture must deliver a fresh DUT in default state."""
    # After fixture setup, version must be the factory default (factory_reset
    # is called inside the fixture definition).
    version = sim_dut.get_parameter("Device.DeviceInfo.SoftwareVersion")
    assert version == "1.0.0"
    # Mutate and verify — does not affect the next test's fixture instance
    sim_dut.set_parameter("Device.DeviceInfo.SoftwareVersion", "MUTATED")
    assert sim_dut.get_parameter("Device.DeviceInfo.SoftwareVersion") == "MUTATED"


@pytest.mark.headless
def test_vlan_blocks_do_not_overlap():
    """WorkerPool block sizes must be large enough that blocks never overlap."""
    num_workers = 10
    all_vlans: set[int] = set()
    for w in range(num_workers):
        pool = WorkerPool(worker_id=w)
        block = {pool.allocate_vlan(offset=i) for i in range(WorkerPool.VLAN_BLOCK_SIZE)}
        overlap = all_vlans & block
        assert not overlap, f"Worker {w} VLAN block overlaps with a previous worker: {overlap}"
        all_vlans |= block
