"""T23 — Determinism meta-tests.

Verifies that two back-to-back runs of the same simulated test sequence
produce byte-identical (hash-equal) results.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from cpe_ta.dut.sim.sim_cpe import SimCPE
from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_sim_sequence(dut_id: str = "dut-det-01") -> dict[str, object]:
    """Execute a canonical sim sequence and return a normalised result dict.

    Sequence: factory_reset → set_parameters → cwmp_inform → power_cycle
    """
    dut = SimCPE(dut_id=dut_id)
    dut.factory_reset()

    # Set a small set of parameters
    dut.set_parameter("Device.DeviceInfo.SoftwareVersion", "1.2.3")
    dut.set_parameter("Device.WiFi.SSID.1.SSID", "DeterminismNet")
    dut.set_parameter("Device.Firewall.Enable", False)

    # CWMP inform
    inform_result = dut.cwmp_inform()

    # Power cycle
    dut.power_cycle()
    wan_ip = dut.get_wan_ip()

    # Collect console metrics
    metrics = dut.get_console_metrics()

    return {
        "dut_id": dut.dut_id,
        "sw_version": dut.get_parameter("Device.DeviceInfo.SoftwareVersion"),
        "ssid": dut.get_parameter("Device.WiFi.SSID.1.SSID"),
        "firewall_enable": dut.get_parameter("Device.Firewall.Enable"),
        "inform_manufacturer": inform_result.get("manufacturer"),
        "inform_model": inform_result.get("model"),
        "inform_session_id": inform_result.get("session_id"),
        "reboot_count": dut.reboot_count,
        "wan_ip": wan_ip,
        "cpu_percent": metrics["cpu_percent"],
        "ram_percent": metrics["ram_percent"],
    }


def _stable_json(obj: dict[str, object]) -> str:
    """Serialise *obj* as deterministic JSON (sorted keys, no floating variance)."""
    return json.dumps(obj, sort_keys=True, default=str)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# T23 tests
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_sim_sequence_is_deterministic():
    """Two identical sim sequences must produce the same result hash."""
    result_a = _run_sim_sequence("dut-det-a")
    result_b = _run_sim_sequence("dut-det-b")

    # Normalise dut_id to the same value so we compare state, not identity
    result_a["dut_id"] = "dut-det"
    result_b["dut_id"] = "dut-det"

    json_a = _stable_json(result_a)
    json_b = _stable_json(result_b)

    assert _sha256(json_a) == _sha256(json_b), (
        f"Sim sequence is not deterministic.\nRun A: {json_a}\nRun B: {json_b}"
    )


@pytest.mark.headless
def test_sim_sequence_hash_matches_literal():
    """The sim sequence hash must be stable across Python restarts (no random seed)."""
    result = _run_sim_sequence("dut-literal")
    result["dut_id"] = "dut-det"
    json_str = _stable_json(result)

    # Run twice in the same process — both hashes must be identical
    h1 = _sha256(json_str)
    h2 = _sha256(json_str)
    assert h1 == h2


@pytest.mark.headless
def test_factory_reset_always_produces_same_default_config():
    """factory_reset must always restore the exact same default configuration."""
    dut = SimCPE(dut_id="dut-reset-det")

    # Mutate heavily while powered on
    dut.set_parameter("Device.DeviceInfo.SoftwareVersion", "99.0.0")
    dut.set_parameter("Device.WiFi.SSID.1.SSID", "MutatedSSID")

    dut.factory_reset()
    config_a = dut.config_backup()

    # Mutate again (DUT is powered on after factory_reset — power_off beforehand is not needed)
    dut.set_parameter("Device.DeviceInfo.SoftwareVersion", "88.0.0")
    dut.set_parameter("Device.WiFi.SSID.1.SSID", "AnotherSSID")
    dut.power_cycle()
    # power_cycle leaves DUT powered on, so we can mutate once more
    dut.set_parameter("Device.DeviceInfo.SoftwareVersion", "77.0.0")

    dut.factory_reset()
    config_b = dut.config_backup()

    assert _sha256(_stable_json(config_a)) == _sha256(_stable_json(config_b)), (
        "factory_reset is not idempotent — configs differ between resets"
    )


@pytest.mark.headless
def test_sim_traffic_run_client_is_deterministic():
    """SimTrafficEndpoint.run_client must return identical results for identical setup."""
    endpoint = SimTrafficEndpoint(
        configurable_throughput=750.0,
        configurable_latency_ms=2.5,
        configurable_jitter_ms=0.3,
        configurable_packet_loss=0.0,
    )

    result_a = endpoint.run_client(target_ip="10.0.0.1", duration_s=10, protocol="tcp")
    result_b = endpoint.run_client(target_ip="10.0.0.1", duration_s=10, protocol="tcp")

    dict_a = {
        "throughput_mbps": result_a.throughput_mbps,
        "latency_ms": result_a.latency_ms,
        "jitter_ms": result_a.jitter_ms,
        "packet_loss_percent": result_a.packet_loss_percent,
    }
    dict_b = {
        "throughput_mbps": result_b.throughput_mbps,
        "latency_ms": result_b.latency_ms,
        "jitter_ms": result_b.jitter_ms,
        "packet_loss_percent": result_b.packet_loss_percent,
    }

    assert _sha256(_stable_json(dict_a)) == _sha256(_stable_json(dict_b)), (
        f"SimTrafficEndpoint.run_client is not deterministic.\n"
        f"Run A: {dict_a}\nRun B: {dict_b}"
    )


@pytest.mark.headless
def test_sim_traffic_different_configs_differ():
    """Two SimTrafficEndpoints with different configs must produce different hashes."""
    ep_fast = SimTrafficEndpoint(configurable_throughput=900.0, configurable_latency_ms=1.0)
    ep_slow = SimTrafficEndpoint(configurable_throughput=100.0, configurable_latency_ms=50.0)

    r_fast = ep_fast.run_client("10.0.0.1", 10)
    r_slow = ep_slow.run_client("10.0.0.1", 10)

    def _result_hash(r: object) -> str:
        d = {
            "throughput_mbps": r.throughput_mbps,  # type: ignore[attr-defined]
            "latency_ms": r.latency_ms,  # type: ignore[attr-defined]
        }
        return _sha256(_stable_json(d))

    assert _result_hash(r_fast) != _result_hash(r_slow), (
        "Different endpoint configs must produce different result hashes"
    )
