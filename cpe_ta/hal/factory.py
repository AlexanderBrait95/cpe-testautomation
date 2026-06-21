"""Factory: erzeugt HAL-Instrumente aus Config — real oder sim."""

from __future__ import annotations

from typing import Literal

from cpe_ta.hal.base import PDU, RFAttenuator, SerialConsole, Switch, USBRelay

InstrumentMode = Literal["sim", "real"]


def create_switch(config: dict[str, object], mode: InstrumentMode = "sim") -> Switch:
    """Create a Switch instance in simulator or real-hardware mode.

    Parameters
    ----------
    config:
        Keyword arguments forwarded to the real driver constructor.
        Ignored in sim mode.
    mode:
        ``"sim"`` returns a headless :class:`~cpe_ta.hal.sim.sim_switch.SimSwitch`.
        ``"real"`` instantiates :class:`~cpe_ta.hal.drivers.snmp_switch.SNMPSwitch`
        with ``**config``.
    """
    if mode == "sim":
        from cpe_ta.hal.sim.sim_switch import SimSwitch

        return SimSwitch()
    else:
        from cpe_ta.hal.drivers.snmp_switch import SNMPSwitch

        return SNMPSwitch(**config)  # type: ignore[arg-type]


def create_pdu(config: dict[str, object], mode: InstrumentMode = "sim") -> PDU:
    """Create a PDU instance in simulator or real-hardware mode.

    Parameters
    ----------
    config:
        Keyword arguments forwarded to the real driver constructor.
        Ignored in sim mode.
    mode:
        ``"sim"`` returns a headless :class:`~cpe_ta.hal.sim.sim_pdu.SimPDU`.
        ``"real"`` instantiates :class:`~cpe_ta.hal.drivers.pdu_http.HTTPPdu`
        with ``**config``.
    """
    if mode == "sim":
        from cpe_ta.hal.sim.sim_pdu import SimPDU

        return SimPDU()
    else:
        from cpe_ta.hal.drivers.pdu_http import HTTPPdu

        return HTTPPdu(**config)  # type: ignore[arg-type]


def create_serial_console(config: dict[str, object], mode: InstrumentMode = "sim") -> SerialConsole:
    """Create a SerialConsole instance in simulator or real-hardware mode.

    Parameters
    ----------
    config:
        Keyword arguments forwarded to the real driver constructor.
        Ignored in sim mode.
    mode:
        ``"sim"`` returns a headless
        :class:`~cpe_ta.hal.sim.sim_serial.SimSerialConsole`.
        ``"real"`` instantiates
        :class:`~cpe_ta.hal.drivers.serial_console.SerialConsoleDriver`
        with ``**config``.
    """
    if mode == "sim":
        from cpe_ta.hal.sim.sim_serial import SimSerialConsole

        return SimSerialConsole()
    else:
        from cpe_ta.hal.drivers.serial_console import SerialConsoleDriver

        return SerialConsoleDriver(**config)  # type: ignore[arg-type]


def create_rf_attenuator(config: dict[str, object], mode: InstrumentMode = "sim") -> RFAttenuator:
    """Create an RFAttenuator instance in simulator or real-hardware mode.

    Parameters
    ----------
    config:
        Keyword arguments forwarded to the real driver constructor.
        Ignored in sim mode.
    mode:
        ``"sim"`` returns a headless
        :class:`~cpe_ta.hal.sim.sim_rf.SimRFAttenuator`.
        ``"real"`` instantiates
        :class:`~cpe_ta.hal.drivers.rf_attenuator.RFAttenuatorDriver`
        with ``**config``.
    """
    if mode == "sim":
        from cpe_ta.hal.sim.sim_rf import SimRFAttenuator

        return SimRFAttenuator()
    else:
        from cpe_ta.hal.drivers.rf_attenuator import RFAttenuatorDriver

        return RFAttenuatorDriver(**config)  # type: ignore[arg-type]


def create_usb_relay(config: dict[str, object], mode: InstrumentMode = "sim") -> USBRelay:
    """Create a USBRelay instance in simulator or real-hardware mode.

    Parameters
    ----------
    config:
        Keyword arguments forwarded to the real driver constructor.
        Ignored in sim mode.
    mode:
        ``"sim"`` returns a headless
        :class:`~cpe_ta.hal.sim.sim_usbrelay.SimUSBRelay`.
        ``"real"`` instantiates
        :class:`~cpe_ta.hal.drivers.usb_relay.USBRelayDriver`
        with ``**config``.
    """
    if mode == "sim":
        from cpe_ta.hal.sim.sim_usbrelay import SimUSBRelay

        return SimUSBRelay()
    else:
        from cpe_ta.hal.drivers.usb_relay import USBRelayDriver

        return USBRelayDriver(**config)  # type: ignore[arg-type]
