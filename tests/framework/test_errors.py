"""Meta-tests for the CPE error taxonomy (cpe_ta.core.errors).

Verifies:
- Class hierarchy / isinstance relationships
- is_infrastructure_error() on HardwareError and InfraError
- CapabilityError is NOT an infrastructure error
- All exceptions are catchable as CPETestError
"""

from __future__ import annotations

import pytest

from cpe_ta.core.errors import (
    CapabilityError,
    ConfigError,
    CPETestError,
    CPETimeoutError,
    DUTError,
    HardwareError,
    InfraError,
    InventoryError,
)

# ---------------------------------------------------------------------------
# Hierarchy: all are subclasses of CPETestError
# ---------------------------------------------------------------------------


class TestHierarchy:
    def test_config_error_is_cpe_test_error(self) -> None:
        assert issubclass(ConfigError, CPETestError)

    def test_inventory_error_is_config_error(self) -> None:
        assert issubclass(InventoryError, ConfigError)

    def test_inventory_error_is_cpe_test_error(self) -> None:
        assert issubclass(InventoryError, CPETestError)

    def test_hardware_error_is_cpe_test_error(self) -> None:
        assert issubclass(HardwareError, CPETestError)

    def test_infra_error_is_hardware_error(self) -> None:
        assert issubclass(InfraError, HardwareError)

    def test_dut_error_is_cpe_test_error(self) -> None:
        assert issubclass(DUTError, CPETestError)

    def test_timeout_error_is_cpe_test_error(self) -> None:
        assert issubclass(CPETimeoutError, CPETestError)

    def test_capability_error_is_cpe_test_error(self) -> None:
        assert issubclass(CapabilityError, CPETestError)


# ---------------------------------------------------------------------------
# isinstance checks when raised and caught
# ---------------------------------------------------------------------------


class TestInstanceOf:
    def test_inventory_error_caught_as_config_error(self) -> None:
        with pytest.raises(ConfigError):
            raise InventoryError("role X not wired")

    def test_inventory_error_caught_as_cpe_test_error(self) -> None:
        with pytest.raises(CPETestError):
            raise InventoryError("role X not wired")

    def test_infra_error_caught_as_hardware_error(self) -> None:
        with pytest.raises(HardwareError):
            raise InfraError("ACS unreachable")

    def test_hardware_error_caught_as_cpe_test_error(self) -> None:
        with pytest.raises(CPETestError):
            raise HardwareError("switch timeout")

    def test_dut_error_not_hardware_error(self) -> None:
        exc = DUTError("CPE crashed")
        assert not isinstance(exc, HardwareError)

    def test_capability_error_not_hardware_error(self) -> None:
        exc = CapabilityError("WiFi 6 required")
        assert not isinstance(exc, HardwareError)


# ---------------------------------------------------------------------------
# is_infrastructure_error()
# ---------------------------------------------------------------------------


class TestInfrastructureFlag:
    def test_hardware_error_is_infra(self) -> None:
        exc = HardwareError("switch port flap")
        assert exc.is_infrastructure_error() is True

    def test_infra_error_is_infra(self) -> None:
        exc = InfraError("DHCP server down")
        assert exc.is_infrastructure_error() is True

    def test_dut_error_has_no_infra_flag(self) -> None:
        exc = DUTError("CPE kernel panic")
        assert not hasattr(exc, "is_infrastructure_error")

    def test_config_error_has_no_infra_flag(self) -> None:
        exc = ConfigError("missing field")
        assert not hasattr(exc, "is_infrastructure_error")

    def test_capability_error_has_no_infra_flag(self) -> None:
        exc = CapabilityError("no USB port")
        assert not hasattr(exc, "is_infrastructure_error")


# ---------------------------------------------------------------------------
# Message propagation
# ---------------------------------------------------------------------------


class TestMessages:
    def test_exception_message_preserved(self) -> None:
        msg = "switch 42 port 7 unresponsive"
        exc = HardwareError(msg)
        assert str(exc) == msg

    def test_inventory_error_message(self) -> None:
        msg = "role 'DUT-WAN' not wired in testbed"
        exc = InventoryError(msg)
        assert msg in str(exc)

    def test_capability_error_message(self) -> None:
        msg = "DUT has no VoIP capability"
        exc = CapabilityError(msg)
        assert msg in str(exc)
