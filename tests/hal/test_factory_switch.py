"""Tests for the HAL instrument factory — sim mode only (headless)."""

from __future__ import annotations

import pytest

from cpe_ta.hal.base import PDU, RFAttenuator, SerialConsole, Switch, USBRelay
from cpe_ta.hal.factory import (
    create_pdu,
    create_rf_attenuator,
    create_serial_console,
    create_switch,
    create_usb_relay,
)

# ===========================================================================
# Switch factory
# ===========================================================================


@pytest.mark.headless
@pytest.mark.parametrize("mode", ["sim"])
def test_create_switch_returns_switch_protocol(mode: str) -> None:
    """create_switch in sim mode returns an object satisfying the Switch Protocol."""
    result = create_switch(config={}, mode=mode)  # type: ignore[arg-type]
    assert isinstance(result, Switch)


@pytest.mark.headless
def test_create_switch_sim_is_functional() -> None:
    """Sim switch produced by factory responds to port_enable."""
    sw = create_switch(config={}, mode="sim")
    sw.port_enable("gi0/1")
    sw.port_disable("gi0/1")
    # No exception → factory returned a working simulator


@pytest.mark.headless
def test_create_switch_sim_interface_identical_to_direct() -> None:
    """Switch returned by factory is instanceof Switch — same as direct construction."""
    from cpe_ta.hal.sim.sim_switch import SimSwitch

    direct = SimSwitch()
    via_factory = create_switch(config={}, mode="sim")
    # Both must satisfy the same Protocol
    assert isinstance(direct, Switch)
    assert isinstance(via_factory, Switch)
    assert type(direct) is type(via_factory)


# ===========================================================================
# PDU factory
# ===========================================================================


@pytest.mark.headless
@pytest.mark.parametrize("mode", ["sim"])
def test_create_pdu_returns_pdu_protocol(mode: str) -> None:
    result = create_pdu(config={}, mode=mode)  # type: ignore[arg-type]
    assert isinstance(result, PDU)


@pytest.mark.headless
def test_create_pdu_sim_is_functional() -> None:
    pdu = create_pdu(config={}, mode="sim")
    pdu.power_on("1")
    pdu.power_off("1")


# ===========================================================================
# SerialConsole factory
# ===========================================================================


@pytest.mark.headless
@pytest.mark.parametrize("mode", ["sim"])
def test_create_serial_console_returns_protocol(mode: str) -> None:
    result = create_serial_console(config={}, mode=mode)  # type: ignore[arg-type]
    assert isinstance(result, SerialConsole)


@pytest.mark.headless
def test_create_serial_console_sim_is_functional() -> None:
    con = create_serial_console(config={}, mode="sim")
    con.open()
    con.send("show version")
    con.close()


# ===========================================================================
# RFAttenuator factory
# ===========================================================================


@pytest.mark.headless
@pytest.mark.parametrize("mode", ["sim"])
def test_create_rf_attenuator_returns_protocol(mode: str) -> None:
    result = create_rf_attenuator(config={}, mode=mode)  # type: ignore[arg-type]
    assert isinstance(result, RFAttenuator)


@pytest.mark.headless
def test_create_rf_attenuator_sim_is_functional() -> None:
    rf = create_rf_attenuator(config={}, mode="sim")
    rf.set_attenuation_db(1, 10.0)
    assert rf.get_attenuation(1) == pytest.approx(10.0)


# ===========================================================================
# USBRelay factory
# ===========================================================================


@pytest.mark.headless
@pytest.mark.parametrize("mode", ["sim"])
def test_create_usb_relay_returns_protocol(mode: str) -> None:
    result = create_usb_relay(config={}, mode=mode)  # type: ignore[arg-type]
    assert isinstance(result, USBRelay)


@pytest.mark.headless
def test_create_usb_relay_sim_is_functional() -> None:
    relay = create_usb_relay(config={}, mode="sim")
    relay.set_channel(1, True)
    relay.pulse(1, 0.1)
