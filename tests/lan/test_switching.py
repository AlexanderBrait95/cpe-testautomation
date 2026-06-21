"""T24 — LAN switching / VLAN / mirror tests (headless)."""
from __future__ import annotations

import pytest

from cpe_ta.hal.sim.sim_switch import SimSwitch

pytestmark = pytest.mark.headless


def test_vlan_isolation(sim_switch: SimSwitch) -> None:
    """Two ports placed in different VLANs must have distinct VLAN IDs."""
    sim_switch.set_vlan("port1", vlan_id=10)
    sim_switch.set_vlan("port2", vlan_id=20)

    vlan1 = sim_switch.ports["port1"]["vlan"]
    vlan2 = sim_switch.ports["port2"]["vlan"]
    assert vlan1 != vlan2


def test_broadcast_vlan(sim_switch: SimSwitch) -> None:
    """Configure a port in a dedicated broadcast VLAN (VLAN 4095)."""
    sim_switch.set_vlan("port3", vlan_id=4095, tagged=False)
    assert sim_switch.ports["port3"]["vlan"] == 4095


def test_port_mirror(sim_switch: SimSwitch) -> None:
    """set_mirror must register the source→dest mapping."""
    sim_switch.set_mirror("port1", "port4", enabled=True)
    assert sim_switch.mirrors.get("port1") == "port4"


def test_mac_learning_counter(sim_switch: SimSwitch) -> None:
    """After enabling a port the tx_frames counter must be accessible (≥ 0)."""
    sim_switch.port_enable("port2")
    # In the sim, counters start at 0; the important thing is they're present
    stats = sim_switch.get_port_stats("port2")
    assert stats.tx_frames >= 0
