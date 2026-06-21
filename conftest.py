"""Root conftest.py — marker registration, global fixtures.

This file is discovered by pytest automatically because it lives at the
root of the project.  It:

1. Registers all custom markers from ``cpe_ta.core.selection.MARKERS``
   so that ``--strict-markers`` (set in pyproject.toml) does not raise
   PytestUnknownMarkWarning.

2. Adds a ``--sim-mode`` CLI option (default: True) that downstream
   fixtures can query to choose between real hardware drivers and the
   headless simulators.

3. Provides the ``sim_mode`` and ``resource_pool`` fixtures consumed by
   HAL/infra factories and xdist worker isolation.

4. (T18) Adds ``worker_pool``, ``testbed_session``, ``sim_dut``,
   ``sim_acs``, ``sim_dhcp``, ``sim_traffic``, ``sim_radius``,
   ``rfc2544``, ``rfc6349`` fixtures.
"""

from __future__ import annotations

from typing import Generator

import pytest

from cpe_ta.core.selection import MARKERS


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register all custom markers so --strict-markers does not fail."""
    _marker_descriptions: dict[str, str] = {
        "smoke": "fast smoke-tests (subset of regression)",
        "full": "full test suite",
        "regression": "regression test suite",
        "tech_dsl": "requires DSL technology/connectivity",
        "tech_docsis": "requires DOCSIS technology/connectivity",
        "tech_pon": "requires PON technology/connectivity",
        "tech_fwa": "requires FWA technology/connectivity",
        "headless": "runs without any physical hardware (against simulators)",
        "hardware": "requires physical hardware — skipped when hardware absent",
    }
    for marker in MARKERS:
        description = _marker_descriptions.get(marker, marker)
        config.addinivalue_line("markers", f"{marker}: {description}")


# ---------------------------------------------------------------------------
# CLI option: --sim-mode / --no-sim-mode
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the --sim-mode flag to the pytest CLI."""
    parser.addoption(
        "--sim-mode",
        action="store_true",
        default=True,
        help=(
            "Run against headless simulators instead of real hardware "
            "(default: True; use --no-sim-mode for real hardware)"
        ),
    )
    parser.addoption(
        "--no-sim-mode",
        action="store_false",
        dest="sim_mode",
        help="Run against real hardware instead of simulators",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sim_mode(request: pytest.FixtureRequest) -> bool:
    """Return True when running in headless simulator mode.

    Use this fixture in HAL factory calls to select the simulator backend:

    .. code-block:: python

        def test_something(sim_mode):
            switch = factory.create_switch(switch_cfg, use_sim=sim_mode)
    """
    return bool(request.config.getoption("--sim-mode", default=True))


@pytest.fixture(scope="function")
def resource_pool(worker_id: str = "master") -> Generator[dict[str, int], None, None]:
    """Provide an isolated resource pool for the current test worker.

    When running under pytest-xdist each worker receives a unique integer
    ``worker_index`` that is used to derive disjoint VLAN and IP subnet
    ranges.  This prevents cross-talk between parallel test workers.

    Yields
    ------
    dict with keys:
        ``vlan_base``  — first VLAN ID in the worker's allocation block
        ``subnet_base`` — third octet of the worker's /24 subnet block
        ``worker_index`` — zero-based worker index (0 when running serial)
    """
    # Determine worker index from pytest-xdist environment variable
    import os

    xdist_worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    if xdist_worker.startswith("gw"):
        try:
            idx = int(xdist_worker[2:])
        except ValueError:
            idx = 0
    else:
        idx = 0

    # Allocate non-overlapping blocks:
    #   Worker 0: VLANs 100-199, subnet 10.100.x.y
    #   Worker 1: VLANs 200-299, subnet 10.101.x.y
    #   ...
    pool: dict[str, int] = {
        "worker_index": idx,
        "vlan_base": 100 + idx * 100,
        "subnet_base": 100 + idx,
    }
    yield pool
    # No teardown required — pools are purely numeric allocations


# ---------------------------------------------------------------------------
# T18 — Session/DUT/Infra fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def worker_pool(resource_pool: dict[str, int]) -> "WorkerPool":  # type: ignore[name-defined]
    """Return a WorkerPool instance aligned with the current xdist worker."""
    from cpe_ta.core.runner import WorkerPool

    return WorkerPool(worker_id=resource_pool["worker_index"])


@pytest.fixture
def testbed_session(sim_mode: bool, worker_pool: "WorkerPool") -> Generator["TestbedSession", None, None]:  # type: ignore[name-defined]
    """Provide a fully set-up TestbedSession, torn down after each test."""
    from cpe_ta.core.runner import TestbedSession

    session = TestbedSession(
        testbed_id=worker_pool.allocate_instance_id("tb"),
        sim_mode=sim_mode,
    )
    session.setup()
    yield session
    session.teardown()


@pytest.fixture
def sim_dut(worker_pool: "WorkerPool") -> "SimCPE":  # type: ignore[name-defined]
    """Provide a fresh SimCPE per test — ensures idempotency."""
    from cpe_ta.dut.sim.sim_cpe import SimCPE

    dut = SimCPE(dut_id=worker_pool.allocate_instance_id("dut"))
    dut.factory_reset()
    return dut


@pytest.fixture
def sim_acs() -> "SimACSService":  # type: ignore[name-defined]
    """Provide a fresh SimACSService per test."""
    from cpe_ta.infra.sim.sim_acs import SimACSService

    return SimACSService()


@pytest.fixture
def sim_dhcp() -> "SimDHCPService":  # type: ignore[name-defined]
    """Provide a fresh SimDHCPService per test."""
    from cpe_ta.infra.sim.sim_dhcp import SimDHCPService

    return SimDHCPService()


@pytest.fixture
def sim_traffic() -> "SimTrafficEndpoint":  # type: ignore[name-defined]
    """Provide a fresh SimTrafficEndpoint per test."""
    from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint

    return SimTrafficEndpoint()


@pytest.fixture
def sim_radius() -> "SimRADIUSService":  # type: ignore[name-defined]
    """Provide a fresh SimRADIUSService per test."""
    from cpe_ta.infra.sim.sim_radius import SimRADIUSService

    return SimRADIUSService()


@pytest.fixture
def rfc2544() -> "PerfCriterion":  # type: ignore[name-defined]
    """RFC 2544 performance criterion profile."""
    from cpe_ta.core.criteria import RFC2544_PROFILE

    return RFC2544_PROFILE


@pytest.fixture
def rfc6349() -> "PerfCriterion":  # type: ignore[name-defined]
    """RFC 6349 performance criterion profile."""
    from cpe_ta.core.criteria import RFC6349_PROFILE

    return RFC6349_PROFILE
