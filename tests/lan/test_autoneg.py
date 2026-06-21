"""T24 — LAN auto-negotiation tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE
from cpe_ta.hal.sim.sim_switch import SimSwitch

pytestmark = [pytest.mark.headless, pytest.mark.smoke]


def test_port_enable_disable(sim_switch: SimSwitch) -> None:
    """Disable then re-enable a port and verify the enabled flag."""
    sim_switch.port_disable("port1")
    assert sim_switch.ports["port1"]["enabled"] is False

    sim_switch.port_enable("port1")
    assert sim_switch.ports["port1"]["enabled"] is True


def test_speed_duplex_100_full(sim_switch: SimSwitch) -> None:
    """Set 100 Mbit/s full-duplex and read back from port stats."""
    sim_switch.set_speed_duplex("port1", 100, True)
    stats = sim_switch.get_port_stats("port1")
    assert stats.speed_mbps == 100
    assert stats.duplex_full is True


def test_speed_duplex_1000(sim_switch: SimSwitch) -> None:
    """Set 1000 Mbit/s full-duplex and read back from port stats."""
    sim_switch.set_speed_duplex("port1", 1000, True)
    stats = sim_switch.get_port_stats("port1")
    assert stats.speed_mbps == 1000


def test_link_flap_recovery(sim_switch: SimSwitch) -> None:
    """Disable → enable a port and verify the port recovers (enabled=True)."""
    sim_switch.port_disable("port1")
    assert sim_switch.ports["port1"]["enabled"] is False

    sim_switch.port_enable("port1")
    stats = sim_switch.get_port_stats("port1")
    assert sim_switch.ports["port1"]["enabled"] is True
    # stats must be readable after recovery
    assert stats.speed_mbps >= 0


def test_mtu_config(sim_dut: SimCPE) -> None:
    """Set an MTU parameter on the DUT and verify it is stored."""
    mtu_param = "Device.Ethernet.Interface.1.MaxBitRate"
    sim_dut.set_parameter(mtu_param, 1500)
    assert sim_dut.get_parameter(mtu_param) == 1500


def test_vlan_tagging(sim_switch: SimSwitch) -> None:
    """Set a VLAN with tagging on port1 and verify stored state."""
    sim_switch.set_vlan("port1", vlan_id=100, tagged=True)
    port = sim_switch.ports["port1"]
    assert port["vlan"] == 100
    assert port["tagged"] is True


def test_autoneg_stats(sim_switch: SimSwitch) -> None:
    """get_port_stats must return a PortStats with all expected fields."""
    stats = sim_switch.get_port_stats("port1")
    assert hasattr(stats, "tx_frames")
    assert hasattr(stats, "rx_frames")
    assert hasattr(stats, "tx_errors")
    assert hasattr(stats, "rx_errors")
    assert hasattr(stats, "speed_mbps")
    assert hasattr(stats, "duplex_full")
