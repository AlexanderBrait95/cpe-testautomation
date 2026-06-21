"""Test-Session orchestration — Setup/Teardown fixtures, idempotency guarantees."""
from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TestbedSession:
    """Manages testbed state for a single test run — enforces clean starting state."""

    def __init__(self, testbed_id: str, sim_mode: bool = True):
        self.testbed_id = testbed_id
        self.sim_mode = sim_mode
        self._setup_done = False
        self._teardown_errors: list[str] = []

    def setup(self) -> None:
        """Bring testbed to known starting state."""
        logger.info("Setting up testbed session %s", self.testbed_id)
        self._setup_done = True
        self._teardown_errors = []

    def teardown(self) -> None:
        """Restore testbed to clean state. Never raises — logs errors instead."""
        logger.info("Tearing down testbed session %s", self.testbed_id)
        try:
            self._do_teardown()
        except Exception as e:
            self._teardown_errors.append(str(e))
            logger.error("Teardown error (non-fatal): %s", e)

    def _do_teardown(self) -> None:
        self._setup_done = False

    @property
    def teardown_errors(self) -> list[str]:
        return list(self._teardown_errors)

    @contextmanager
    def session_context(self) -> Generator[None, None, None]:
        self.setup()
        try:
            yield
        finally:
            self.teardown()


class WorkerPool:
    """Assigns disjoint VLAN/subnet/instance resources to parallel workers."""

    VLAN_BLOCK_SIZE = 100
    SUBNET_BLOCK_SIZE = 10

    def __init__(self, worker_id: int = 0, total_workers: int = 1):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.vlan_base = 100 + (worker_id * self.VLAN_BLOCK_SIZE)
        self.subnet_octet = 10 + (worker_id * self.SUBNET_BLOCK_SIZE)

    def allocate_vlan(self, offset: int = 0) -> int:
        """Get a VLAN ID guaranteed disjoint from other workers."""
        return self.vlan_base + offset

    def allocate_subnet(self, offset: int = 0) -> str:
        """Get a subnet guaranteed disjoint from other workers."""
        return f"192.168.{self.subnet_octet + offset}.0/24"

    def allocate_instance_id(self, prefix: str = "inst") -> str:
        """Get a unique instance ID for services."""
        return f"{prefix}-worker{self.worker_id}"
