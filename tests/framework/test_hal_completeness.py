"""HAL completeness meta-test.

Verifies that:
- Every Protocol interface has at least one simulator class.
- Every Protocol interface has at least one real driver skeleton class.
- Each simulator satisfies isinstance() check against its Protocol.
- All Protocol methods are present on each simulator.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from cpe_ta.hal.base import PDU, RFAttenuator, SerialConsole, Switch, USBRelay

# ---------------------------------------------------------------------------
# Mapping: Protocol → (list of simulators, list of driver classes)
# ---------------------------------------------------------------------------
# Import driver skeletons (they must be importable without hardware present)
from cpe_ta.hal.drivers.netconf_switch import NetconfSwitch
from cpe_ta.hal.drivers.pdu_http import HTTPPdu
from cpe_ta.hal.drivers.rf_attenuator import RFAttenuatorDriver
from cpe_ta.hal.drivers.serial_console import SerialConsoleDriver
from cpe_ta.hal.drivers.snmp_switch import SNMPSwitch
from cpe_ta.hal.drivers.usb_relay import USBRelayDriver
from cpe_ta.hal.sim.sim_pdu import SimPDU
from cpe_ta.hal.sim.sim_rf import SimRFAttenuator
from cpe_ta.hal.sim.sim_serial import SimSerialConsole
from cpe_ta.hal.sim.sim_switch import SimSwitch
from cpe_ta.hal.sim.sim_usbrelay import SimUSBRelay

_REGISTRY: list[
    tuple[
        type[Any],  # Protocol
        list[type[Any]],  # Simulators
        list[type[Any]],  # Driver skeletons
    ]
] = [
    (Switch, [SimSwitch], [SNMPSwitch, NetconfSwitch]),
    (PDU, [SimPDU], [HTTPPdu]),
    (SerialConsole, [SimSerialConsole], [SerialConsoleDriver]),
    (RFAttenuator, [SimRFAttenuator], [RFAttenuatorDriver]),
    (USBRelay, [SimUSBRelay], [USBRelayDriver]),
]


def _get_protocol_methods(protocol: type[Any]) -> set[str]:
    """Return all non-dunder method names defined directly on a Protocol."""
    return {
        name
        for name, member in inspect.getmembers(protocol, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


# ---------------------------------------------------------------------------
# Parametrized tests
# ---------------------------------------------------------------------------


@pytest.mark.headless
@pytest.mark.parametrize("protocol,simulators,_drivers", _REGISTRY, ids=[r[0].__name__ for r in _REGISTRY])
def test_has_at_least_one_simulator(protocol: type[Any], simulators: list[type[Any]], _drivers: list[type[Any]]) -> None:
    """Every Protocol must have at least one registered simulator."""
    assert len(simulators) >= 1, f"No simulator registered for {protocol.__name__}"


@pytest.mark.headless
@pytest.mark.parametrize("protocol,_simulators,drivers", _REGISTRY, ids=[r[0].__name__ for r in _REGISTRY])
def test_has_at_least_one_driver_skeleton(
    protocol: type[Any], _simulators: list[type[Any]], drivers: list[type[Any]]
) -> None:
    """Every Protocol must have at least one registered real driver skeleton."""
    assert len(drivers) >= 1, f"No driver skeleton registered for {protocol.__name__}"


@pytest.mark.headless
@pytest.mark.parametrize(
    "protocol,sim_class",
    [(entry[0], sim) for entry in _REGISTRY for sim in entry[1]],
    ids=[f"{entry[0].__name__}-{sim.__name__}" for entry in _REGISTRY for sim in entry[1]],
)
def test_simulator_isinstance_of_protocol(protocol: type[Any], sim_class: type[Any]) -> None:
    """Each simulator instance must satisfy isinstance() against its Protocol."""
    instance = sim_class()
    assert isinstance(instance, protocol), (
        f"{sim_class.__name__} does not satisfy isinstance({protocol.__name__})"
    )


@pytest.mark.headless
@pytest.mark.parametrize(
    "protocol,sim_class",
    [(entry[0], sim) for entry in _REGISTRY for sim in entry[1]],
    ids=[f"{entry[0].__name__}-{sim.__name__}" for entry in _REGISTRY for sim in entry[1]],
)
def test_simulator_has_all_protocol_methods(protocol: type[Any], sim_class: type[Any]) -> None:
    """Each simulator must implement every method declared on its Protocol."""
    required_methods = _get_protocol_methods(protocol)
    missing = [m for m in required_methods if not callable(getattr(sim_class, m, None))]
    assert not missing, (
        f"{sim_class.__name__} is missing methods for {protocol.__name__}: {missing}"
    )


@pytest.mark.headless
@pytest.mark.parametrize(
    "protocol,driver_class",
    [(entry[0], drv) for entry in _REGISTRY for drv in entry[2]],
    ids=[f"{entry[0].__name__}-{drv.__name__}" for entry in _REGISTRY for drv in entry[2]],
)
def test_driver_has_all_protocol_methods(protocol: type[Any], driver_class: type[Any]) -> None:
    """Each driver skeleton must implement every method declared on its Protocol."""
    required_methods = _get_protocol_methods(protocol)
    missing = [m for m in required_methods if not callable(getattr(driver_class, m, None))]
    assert not missing, (
        f"{driver_class.__name__} is missing methods for {protocol.__name__}: {missing}"
    )
