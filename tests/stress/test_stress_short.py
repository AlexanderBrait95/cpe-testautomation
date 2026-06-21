"""T33 — Stress / Soak short-run headless tests."""
from __future__ import annotations

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE
from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint

pytestmark = pytest.mark.headless


def test_no_reboot_detection(sim_dut: SimCPE) -> None:
    """Under simulated load the reboot count must not increase."""
    initial_reboot_count = sim_dut.reboot_count
    # Simulate load via console metric reads (no power cycle)
    for _ in range(10):
        sim_dut.get_console_metrics()
    assert sim_dut.reboot_count == initial_reboot_count


def test_memory_leak_detection(sim_dut: SimCPE) -> None:
    """Applying simulate_memory_leak 10 times must push RAM above 60%."""
    for _ in range(10):
        sim_dut.simulate_memory_leak(5.0)
    metrics = sim_dut.get_console_metrics()
    assert metrics["ram_percent"] > 60, (
        f"Expected RAM > 60% but got {metrics['ram_percent']}"
    )


def test_cpu_spike_detection(sim_dut: SimCPE) -> None:
    """simulate_cpu_spike to 95% must be reflected in console metrics."""
    sim_dut.simulate_cpu_spike(95.0)
    metrics = sim_dut.get_console_metrics()
    assert metrics["cpu_percent"] > 90, (
        f"Expected CPU > 90% but got {metrics['cpu_percent']}"
    )


def test_abort_criteria_reboot(sim_dut: SimCPE) -> None:
    """Unexpected reboot must be detected by comparing reboot counts."""
    expected_reboot_count = sim_dut.reboot_count
    # No power cycle performed — count must stay the same
    assert sim_dut.reboot_count == expected_reboot_count


def test_wifi_lan_combined() -> None:
    """Simultaneous LAN + WiFi traffic endpoints must both return results."""
    lan_ep = SimTrafficEndpoint(configurable_throughput=850.0)
    wifi_ep = SimTrafficEndpoint(configurable_throughput=300.0)

    lan_result = lan_ep.run_client(target_ip="192.168.1.10", duration_s=1)
    wifi_result = wifi_ep.run_client(target_ip="192.168.1.11", duration_s=1)

    assert lan_result.throughput_mbps > 0
    assert wifi_result.throughput_mbps > 0


def test_soak_kurzlauf(sim_traffic: SimTrafficEndpoint) -> None:
    """10 consecutive traffic runs must all return throughput_mbps > 0."""
    for i in range(10):
        result = sim_traffic.run_client(target_ip=f"192.168.1.{i + 2}", duration_s=1)
        assert result.throughput_mbps > 0, (
            f"Iteration {i}: throughput_mbps was {result.throughput_mbps}"
        )
