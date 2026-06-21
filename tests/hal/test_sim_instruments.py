"""Tests for all HAL simulator implementations.

All tests run headless — no physical hardware required.
"""

from __future__ import annotations

import pytest

from cpe_ta.core.errors import HardwareError
from cpe_ta.hal.sim.sim_pdu import SimPDU
from cpe_ta.hal.sim.sim_rf import SimRFAttenuator
from cpe_ta.hal.sim.sim_serial import SimSerialConsole
from cpe_ta.hal.sim.sim_switch import SimSwitch
from cpe_ta.hal.sim.sim_usbrelay import SimUSBRelay

# ===========================================================================
# SimSwitch
# ===========================================================================


@pytest.mark.headless
class TestSimSwitch:
    def test_port_enable_sets_enabled_true(self) -> None:
        sw = SimSwitch()
        sw.port_disable("gi0/1")
        sw.port_enable("gi0/1")
        assert sw.ports["gi0/1"]["enabled"] is True

    def test_port_disable_sets_enabled_false(self) -> None:
        sw = SimSwitch()
        sw.port_disable("gi0/1")
        assert sw.ports["gi0/1"]["enabled"] is False

    def test_set_speed_duplex(self) -> None:
        sw = SimSwitch()
        sw.set_speed_duplex("gi0/2", 100, False)
        port = sw.ports["gi0/2"]
        assert port["speed"] == 100
        assert port["duplex"] is False

    def test_set_vlan_untagged(self) -> None:
        sw = SimSwitch()
        sw.set_vlan("gi0/3", 100, tagged=False)
        port = sw.ports["gi0/3"]
        assert port["vlan"] == 100
        assert port["tagged"] is False

    def test_set_vlan_tagged(self) -> None:
        sw = SimSwitch()
        sw.set_vlan("gi0/3", 200, tagged=True)
        port = sw.ports["gi0/3"]
        assert port["vlan"] == 200
        assert port["tagged"] is True

    def test_get_port_stats_returns_port_stats(self) -> None:
        from cpe_ta.hal.base import PortStats

        sw = SimSwitch()
        sw.set_speed_duplex("gi0/4", 1000, True)
        stats = sw.get_port_stats("gi0/4")
        assert isinstance(stats, PortStats)
        assert stats.speed_mbps == 1000
        assert stats.duplex_full is True

    def test_get_port_stats_zero_frames_initially(self) -> None:
        sw = SimSwitch()
        stats = sw.get_port_stats("gi0/5")
        assert stats.tx_frames == 0
        assert stats.rx_frames == 0

    def test_set_mirror_enabled(self) -> None:
        sw = SimSwitch()
        sw.set_mirror("gi0/1", "gi0/8", True)
        assert sw.mirrors["gi0/1"] == "gi0/8"

    def test_set_mirror_disabled_removes_entry(self) -> None:
        sw = SimSwitch()
        sw.set_mirror("gi0/1", "gi0/8", True)
        sw.set_mirror("gi0/1", "gi0/8", False)
        assert "gi0/1" not in sw.mirrors

    def test_error_injection_port_enable(self) -> None:
        sw = SimSwitch()
        sw.inject_error("fail_port_enable", True)
        with pytest.raises(HardwareError):
            sw.port_enable("gi0/1")

    def test_error_injection_port_disable(self) -> None:
        sw = SimSwitch()
        sw.inject_error("fail_port_disable", True)
        with pytest.raises(HardwareError):
            sw.port_disable("gi0/1")

    def test_error_injection_cleared(self) -> None:
        sw = SimSwitch()
        sw.inject_error("fail_port_enable", True)
        sw.inject_error("fail_port_enable", False)
        # Should not raise after clearing
        sw.port_enable("gi0/1")
        assert sw.ports["gi0/1"]["enabled"] is True


# ===========================================================================
# SimPDU
# ===========================================================================


@pytest.mark.headless
class TestSimPDU:
    def test_power_on_sets_powered_true(self) -> None:
        pdu = SimPDU()
        pdu.power_off("1")
        pdu.power_on("1")
        assert pdu.outlets["1"]["powered"] is True

    def test_power_off_sets_powered_false(self) -> None:
        pdu = SimPDU()
        pdu.power_off("1")
        assert pdu.outlets["1"]["powered"] is False

    def test_power_cycle_ends_powered_true(self) -> None:
        pdu = SimPDU()
        pdu.power_off("2")
        pdu.power_cycle("2")
        assert pdu.outlets["2"]["powered"] is True

    def test_get_outlet_state(self) -> None:
        from cpe_ta.hal.base import OutletState

        pdu = SimPDU()
        pdu.power_on("3")
        state = pdu.get_outlet_state("3")
        assert isinstance(state, OutletState)
        assert state.outlet_id == "3"
        assert state.powered is True

    def test_get_outlet_state_off(self) -> None:
        pdu = SimPDU()
        pdu.power_off("4")
        state = pdu.get_outlet_state("4")
        assert state.powered is False

    def test_error_injection_power_on(self) -> None:
        pdu = SimPDU()
        pdu.inject_error("fail_power_on", True)
        with pytest.raises(HardwareError):
            pdu.power_on("1")

    def test_error_injection_power_off(self) -> None:
        pdu = SimPDU()
        pdu.inject_error("fail_power_off", True)
        with pytest.raises(HardwareError):
            pdu.power_off("1")

    def test_error_injection_power_cycle(self) -> None:
        pdu = SimPDU()
        pdu.inject_error("fail_power_cycle", True)
        with pytest.raises(HardwareError):
            pdu.power_cycle("1")


# ===========================================================================
# SimSerialConsole
# ===========================================================================


@pytest.mark.headless
class TestSimSerialConsole:
    def test_open_sets_is_open_true(self) -> None:
        con = SimSerialConsole()
        con.open()
        assert con.is_open is True

    def test_close_sets_is_open_false(self) -> None:
        con = SimSerialConsole()
        con.open()
        con.close()
        assert con.is_open is False

    def test_send_collects_commands(self) -> None:
        con = SimSerialConsole()
        con.open()
        con.send("show version")
        con.send("show interfaces")
        assert "show version" in con.sent_commands
        assert "show interfaces" in con.sent_commands

    def test_send_raises_when_not_open(self) -> None:
        con = SimSerialConsole()
        with pytest.raises(HardwareError):
            con.send("show version")

    def test_read_until_returns_buffered_response(self) -> None:
        con = SimSerialConsole()
        con.output_buffer = ["Router>", "Router# show"]
        assert con.read_until("#") == "Router>"
        assert con.read_until("#") == "Router# show"

    def test_read_until_returns_empty_when_buffer_exhausted(self) -> None:
        con = SimSerialConsole()
        result = con.read_until("#", timeout_s=1.0)
        assert result == ""

    def test_read_metrics_returns_configured_values(self) -> None:
        con = SimSerialConsole(cpu_percent=42.0, ram_percent=55.5)
        metrics = con.read_metrics()
        assert metrics["cpu_percent"] == pytest.approx(42.0)
        assert metrics["ram_percent"] == pytest.approx(55.5)

    def test_read_metrics_default_values(self) -> None:
        con = SimSerialConsole()
        metrics = con.read_metrics()
        assert "cpu_percent" in metrics
        assert "ram_percent" in metrics
        assert metrics["cpu_percent"] == pytest.approx(10.0)
        assert metrics["ram_percent"] == pytest.approx(30.0)

    def test_error_injection_open(self) -> None:
        con = SimSerialConsole()
        con.inject_error("fail_open", True)
        with pytest.raises(HardwareError):
            con.open()


# ===========================================================================
# SimRFAttenuator
# ===========================================================================


@pytest.mark.headless
class TestSimRFAttenuator:
    def test_set_attenuation_stores_value(self) -> None:
        rf = SimRFAttenuator()
        rf.set_attenuation_db(1, 20.5)
        assert rf.attenuation[1] == pytest.approx(20.5)

    def test_get_attenuation_returns_set_value(self) -> None:
        rf = SimRFAttenuator()
        rf.set_attenuation_db(2, 15.0)
        assert rf.get_attenuation(2) == pytest.approx(15.0)

    def test_get_attenuation_returns_zero_for_unknown_channel(self) -> None:
        rf = SimRFAttenuator()
        assert rf.get_attenuation(99) == pytest.approx(0.0)

    def test_isolate_true(self) -> None:
        rf = SimRFAttenuator()
        rf.isolate(True)
        assert rf.isolated is True

    def test_isolate_false(self) -> None:
        rf = SimRFAttenuator()
        rf.isolate(True)
        rf.isolate(False)
        assert rf.isolated is False

    def test_error_injection_set_attenuation(self) -> None:
        rf = SimRFAttenuator()
        rf.inject_error("fail_set_attenuation", True)
        with pytest.raises(HardwareError):
            rf.set_attenuation_db(1, 10.0)

    def test_error_injection_isolate(self) -> None:
        rf = SimRFAttenuator()
        rf.inject_error("fail_isolate", True)
        with pytest.raises(HardwareError):
            rf.isolate(True)

    def test_multiple_channels_independent(self) -> None:
        rf = SimRFAttenuator()
        rf.set_attenuation_db(1, 10.0)
        rf.set_attenuation_db(2, 20.0)
        assert rf.get_attenuation(1) == pytest.approx(10.0)
        assert rf.get_attenuation(2) == pytest.approx(20.0)


# ===========================================================================
# SimUSBRelay
# ===========================================================================


@pytest.mark.headless
class TestSimUSBRelay:
    def test_set_channel_true(self) -> None:
        relay = SimUSBRelay()
        relay.set_channel(1, True)
        assert relay.channels[1] is True

    def test_set_channel_false(self) -> None:
        relay = SimUSBRelay()
        relay.set_channel(1, True)
        relay.set_channel(1, False)
        assert relay.channels[1] is False

    def test_pulse_logged(self) -> None:
        relay = SimUSBRelay()
        relay.pulse(2, 0.3)
        assert len(relay.pulse_log) == 1
        assert relay.pulse_log[0] == (2, 0.3)

    def test_pulse_default_duration(self) -> None:
        relay = SimUSBRelay()
        relay.pulse(3)
        assert relay.pulse_log[0][1] == pytest.approx(0.5)

    def test_pulse_multiple_channels(self) -> None:
        relay = SimUSBRelay()
        relay.pulse(1, 0.1)
        relay.pulse(2, 0.2)
        assert len(relay.pulse_log) == 2

    def test_error_injection_set_channel(self) -> None:
        relay = SimUSBRelay()
        relay.inject_error("fail_set_channel", True)
        with pytest.raises(HardwareError):
            relay.set_channel(1, True)

    def test_error_injection_pulse(self) -> None:
        relay = SimUSBRelay()
        relay.inject_error("fail_pulse", True)
        with pytest.raises(HardwareError):
            relay.pulse(1, 0.5)

    def test_channels_start_empty(self) -> None:
        relay = SimUSBRelay()
        assert relay.channels == {}

    def test_pulse_log_starts_empty(self) -> None:
        relay = SimUSBRelay()
        assert relay.pulse_log == []
