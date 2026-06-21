"""T26 — QoS / Performance engine tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.core.criteria import (
    RFC2544_PROFILE,
    Aggregate,
    PerfCriterion,
    Transport,
    compute_aggregate,
    evaluate_criterion,
)
from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint

pytestmark = [pytest.mark.headless, pytest.mark.smoke]


# ---------------------------------------------------------------------------
# compute_aggregate tests
# ---------------------------------------------------------------------------


def test_compute_aggregate_median() -> None:
    """Median of [1,2,3,4,5] must equal 3.0."""
    result = compute_aggregate([1.0, 2.0, 3.0, 4.0, 5.0], Aggregate.MEDIAN)
    assert result == 3.0


def test_compute_aggregate_min() -> None:
    """Min of [5,3,1,4,2] must equal 1.0."""
    result = compute_aggregate([5.0, 3.0, 1.0, 4.0, 2.0], Aggregate.MIN)
    assert result == 1.0


def test_compute_aggregate_p95() -> None:
    """P95 of [1..20] — 95th percentile index = int(20*0.95)=19 → value 20.0."""
    values = [float(i) for i in range(1, 21)]
    result = compute_aggregate(values, Aggregate.P95)
    # sorted: 1..20; idx=int(20*0.95)=19 → sorted_vals[19]=20.0
    assert result == 20.0


# ---------------------------------------------------------------------------
# evaluate_criterion tests
# ---------------------------------------------------------------------------


def test_criterion_pass() -> None:
    """Values [900, 950, 880] with threshold=800 (median) → passed=True."""
    criterion = PerfCriterion(threshold=800.0, aggregate=Aggregate.MEDIAN)
    passed, reason = evaluate_criterion(criterion, [900.0, 950.0, 880.0])
    assert passed is True
    assert ">=>" not in reason


def test_criterion_fail() -> None:
    """Values [900, 950, 880] with threshold=1000 (median) → passed=False."""
    criterion = PerfCriterion(threshold=1000.0, aggregate=Aggregate.MEDIAN)
    passed, reason = evaluate_criterion(criterion, [900.0, 950.0, 880.0])
    assert passed is False


def test_missing_threshold_skip() -> None:
    """PerfCriterion with threshold=None must trigger pytest.skip."""
    criterion = PerfCriterion(threshold=None)
    with pytest.raises(pytest.skip.Exception):
        evaluate_criterion(criterion, [100.0, 200.0])


def test_rfc2544_profile_exists() -> None:
    """RFC2544_PROFILE must be importable and have a non-None transport field."""
    assert RFC2544_PROFILE.transport == Transport.UDP
    assert RFC2544_PROFILE.aggregate == Aggregate.MIN
    # threshold is intentionally None (set per-interface in profiles/)
    # but the profile object must exist
    assert RFC2544_PROFILE is not None


# ---------------------------------------------------------------------------
# SimTrafficEndpoint tests
# ---------------------------------------------------------------------------


def test_traffic_sim_throughput(sim_traffic: SimTrafficEndpoint) -> None:
    """run_client must return a TrafficResult with throughput_mbps > 0."""
    result = sim_traffic.run_client(target_ip="192.168.1.1", duration_s=1)
    assert result.throughput_mbps > 0


def test_traffic_deterministic(sim_traffic: SimTrafficEndpoint) -> None:
    """Two consecutive runs on the same endpoint must return identical throughput."""
    result1 = sim_traffic.run_client(target_ip="192.168.1.1", duration_s=1)
    result2 = sim_traffic.run_client(target_ip="192.168.1.1", duration_s=1)
    assert result1.throughput_mbps == result2.throughput_mbps


def test_parallel_lan_wifi() -> None:
    """Two independent SimTrafficEndpoints both return valid results."""
    lan_ep = SimTrafficEndpoint(configurable_throughput=900.0)
    wifi_ep = SimTrafficEndpoint(configurable_throughput=450.0)

    lan_result = lan_ep.run_client(target_ip="192.168.1.2", duration_s=1)
    wifi_result = wifi_ep.run_client(target_ip="192.168.1.3", duration_s=1)

    assert lan_result.throughput_mbps > 0
    assert wifi_result.throughput_mbps > 0
