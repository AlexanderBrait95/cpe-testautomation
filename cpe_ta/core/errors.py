"""Typed exception hierarchy for the CPE Test-Automation framework.

Hierarchy
---------
CPETestError
├── ConfigError
│   └── InventoryError
├── HardwareError          # is_infrastructure_error() → True
│   └── InfraError
├── DUTError
├── CPETimeoutError        # named to avoid shadowing built-in TimeoutError
└── CapabilityError        # used for capability-skip signalling

Design notes
------------
- Tests that raise HardwareError / InfraError are classified as *error*
  (infrastructure problem), not *fail* (DUT/product problem).
- CapabilityError is raised when a required capability is absent; the
  test-runner fixture catches it and converts it to pytest.skip().
"""

from __future__ import annotations


class CPETestError(Exception):
    """Base class for all CPE Test-Automation exceptions."""


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class ConfigError(CPETestError):
    """Raised for invalid or inconsistent configuration / inventory."""


class InventoryError(ConfigError):
    """Raised when the testbed inventory is structurally invalid.

    Examples: role not wired, duplicate switch port assignment.
    """


# ---------------------------------------------------------------------------
# Hardware / infrastructure errors
# ---------------------------------------------------------------------------


class HardwareError(CPETestError):
    """Raised when a lab instrument (switch, PDU, attenuator …) fails.

    These errors signal *infrastructure* problems, not DUT/product bugs.
    """

    def is_infrastructure_error(self) -> bool:
        """Return True — HardwareError is always an infrastructure error."""
        return True


class InfraError(HardwareError):
    """Raised when a reference infrastructure service (ACS, RADIUS, DHCP …)
    is unavailable or misbehaves in a way that prevents test execution.
    """


# ---------------------------------------------------------------------------
# DUT errors
# ---------------------------------------------------------------------------


class DUTError(CPETestError):
    """Raised when the Device-Under-Test (CPE) behaves unexpectedly.

    Unlike HardwareError this indicates a *product* failure that should be
    counted as a test *fail*, not an infrastructure *error*.
    """


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


class CPETimeoutError(CPETestError):
    """Raised when an operation on a DUT or instrument exceeds its deadline.

    The name avoids shadowing the Python built-in ``TimeoutError``.
    """


# ---------------------------------------------------------------------------
# Capability skip
# ---------------------------------------------------------------------------


class CapabilityError(CPETestError):
    """Raised when the DUT lacks a capability required by the current test.

    The conftest fixture catches this and converts it to ``pytest.skip()``,
    so the test appears as *skipped* rather than *failed*.
    """
