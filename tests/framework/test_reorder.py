"""T18 — Tests that are safe to run in any order (idempotency via sim_dut fixture).

Each test receives a fresh SimCPE via the ``sim_dut`` fixture so there is
no state carry-over between tests regardless of execution order.
"""
from __future__ import annotations

import logging

import pytest

from cpe_ta.core.runner import TestbedSession, WorkerPool

# ---------------------------------------------------------------------------
# Order-independent DUT tests
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_factory_reset_restores_default_config(sim_dut):
    """After factory_reset the DUT must report the default software version."""
    sim_dut.factory_reset()
    version = sim_dut.get_parameter("Device.DeviceInfo.SoftwareVersion")
    assert version == "1.0.0"


@pytest.mark.headless
def test_set_parameter_no_carryover(sim_dut):
    """set_parameter on a fresh DUT must not see values from a previous test."""
    # Each invocation of sim_dut yields a brand-new SimCPE after factory_reset.
    # Verify we start from a clean slate, then write a value and read it back.
    original = sim_dut.get_parameter("Device.DeviceInfo.SoftwareVersion")
    assert original == "1.0.0", "Fresh DUT should have default version"

    sim_dut.set_parameter("Device.DeviceInfo.SoftwareVersion", "9.9.9")
    assert sim_dut.get_parameter("Device.DeviceInfo.SoftwareVersion") == "9.9.9"


@pytest.mark.headless
def test_power_cycle_dut_is_on(sim_dut):
    """After power_cycle the DUT must be in the powered-on state."""
    sim_dut.power_cycle()
    assert sim_dut.get_wan_ip() is not None, "DUT must be powered on after power_cycle"


# ---------------------------------------------------------------------------
# TestbedSession teardown behaviour
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_teardown_errors_empty_after_clean_teardown():
    """A clean teardown must produce no teardown_errors."""
    session = TestbedSession(testbed_id="tb-clean", sim_mode=True)
    session.setup()
    session.teardown()
    assert session.teardown_errors == []


@pytest.mark.headless
def test_teardown_error_logged_not_propagated(caplog):
    """An error inside _do_teardown must be logged, not propagated."""

    class _FaultySession(TestbedSession):
        def _do_teardown(self) -> None:
            raise RuntimeError("injected teardown failure")

    session = _FaultySession(testbed_id="tb-faulty", sim_mode=True)
    session.setup()

    with caplog.at_level(logging.ERROR, logger="cpe_ta.core.runner"):
        session.teardown()  # Must NOT raise

    assert len(session.teardown_errors) == 1
    assert "injected teardown failure" in session.teardown_errors[0]
    assert any("injected teardown failure" in r.message for r in caplog.records)


@pytest.mark.headless
def test_session_context_manager():
    """session_context must call setup and teardown automatically."""
    session = TestbedSession(testbed_id="tb-ctx", sim_mode=True)
    assert not session._setup_done

    with session.session_context():
        assert session._setup_done

    assert not session._setup_done
    assert session.teardown_errors == []


@pytest.mark.headless
def test_worker_pool_allocate_vlan_offset():
    """WorkerPool.allocate_vlan must respect the offset parameter."""
    pool = WorkerPool(worker_id=0)
    assert pool.allocate_vlan(0) == 100
    assert pool.allocate_vlan(5) == 105


@pytest.mark.headless
def test_worker_pool_allocate_instance_id():
    """WorkerPool.allocate_instance_id must embed the worker_id."""
    pool = WorkerPool(worker_id=3)
    inst_id = pool.allocate_instance_id("dut")
    assert "worker3" in inst_id
