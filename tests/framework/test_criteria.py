"""Tests for cpe_ta.core.criteria — pass/fail methodology."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cpe_ta.core.criteria import (
    RFC2544_PROFILE,
    RFC6349_PROFILE,
    Aggregate,
    PerfCriterion,
    Transport,
    compute_aggregate,
    evaluate_criterion,
)

# ---------------------------------------------------------------------------
# compute_aggregate
# ---------------------------------------------------------------------------


class TestComputeAggregate:
    VALUES = [10.0, 20.0, 30.0, 40.0, 50.0]

    def test_median_odd(self) -> None:
        assert compute_aggregate(self.VALUES, Aggregate.MEDIAN) == 30.0

    def test_median_even(self) -> None:
        result = compute_aggregate([10.0, 20.0, 30.0, 40.0], Aggregate.MEDIAN)
        assert result == 25.0

    def test_min(self) -> None:
        assert compute_aggregate(self.VALUES, Aggregate.MIN) == 10.0

    def test_min_single(self) -> None:
        assert compute_aggregate([42.0], Aggregate.MIN) == 42.0

    def test_p95_five_values(self) -> None:
        # sorted=[10,20,30,40,50], idx=int(5*0.95)=4, clamped=4 → 50.0
        result = compute_aggregate(self.VALUES, Aggregate.P95)
        assert result == 50.0

    def test_p95_single_value(self) -> None:
        assert compute_aggregate([99.0], Aggregate.P95) == 99.0

    def test_p95_ten_values(self) -> None:
        # sorted=[1..10], idx=int(10*0.95)=9, clamped=9 → 10.0
        values = [float(i) for i in range(1, 11)]
        result = compute_aggregate(values, Aggregate.P95)
        assert result == 10.0

    def test_empty_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            compute_aggregate([], Aggregate.MEDIAN)

    def test_median_single(self) -> None:
        assert compute_aggregate([7.5], Aggregate.MEDIAN) == 7.5

    def test_deterministic(self) -> None:
        """Two calls with the same input must return the same result."""
        v = [1.1, 2.2, 3.3, 4.4, 5.5]
        assert compute_aggregate(v, Aggregate.P95) == compute_aggregate(v, Aggregate.P95)


# ---------------------------------------------------------------------------
# evaluate_criterion — pass case
# ---------------------------------------------------------------------------


class TestEvaluateCriterionPass:
    def _criterion(self, threshold: float, agg: Aggregate = Aggregate.MEDIAN) -> PerfCriterion:
        return PerfCriterion(threshold=threshold, aggregate=agg, transport=Transport.UDP, repetitions=3)

    def test_median_above_threshold_passes(self) -> None:
        crit = self._criterion(threshold=50.0, agg=Aggregate.MEDIAN)
        passed, reason = evaluate_criterion(crit, [60.0, 70.0, 80.0])
        assert passed is True
        assert "median" in reason.lower() or "MEDIAN" in reason

    def test_min_above_threshold_passes(self) -> None:
        crit = self._criterion(threshold=10.0, agg=Aggregate.MIN)
        passed, _reason = evaluate_criterion(crit, [15.0, 20.0, 25.0])
        assert passed is True

    def test_p95_above_threshold_passes(self) -> None:
        crit = self._criterion(threshold=40.0, agg=Aggregate.P95)
        passed, _reason = evaluate_criterion(crit, [50.0, 60.0, 70.0, 80.0, 90.0])
        assert passed is True

    def test_exactly_at_threshold_passes(self) -> None:
        crit = self._criterion(threshold=30.0, agg=Aggregate.MEDIAN)
        passed, _reason = evaluate_criterion(crit, [30.0, 30.0, 30.0])
        assert passed is True

    def test_reason_contains_threshold(self) -> None:
        crit = self._criterion(threshold=100.0)
        _passed, reason = evaluate_criterion(crit, [150.0, 160.0, 170.0])
        assert "100" in reason


# ---------------------------------------------------------------------------
# evaluate_criterion — fail case
# ---------------------------------------------------------------------------


class TestEvaluateCriterionFail:
    def test_median_below_threshold_fails(self) -> None:
        crit = PerfCriterion(threshold=100.0, aggregate=Aggregate.MEDIAN, repetitions=3)
        passed, reason = evaluate_criterion(crit, [40.0, 50.0, 60.0])
        assert passed is False
        assert "50" in reason or "threshold" in reason.lower()

    def test_min_below_threshold_fails(self) -> None:
        crit = PerfCriterion(threshold=20.0, aggregate=Aggregate.MIN, repetitions=3)
        passed, _reason = evaluate_criterion(crit, [5.0, 30.0, 40.0])
        assert passed is False

    def test_no_values_fails(self) -> None:
        crit = PerfCriterion(threshold=10.0, aggregate=Aggregate.MEDIAN, repetitions=1)
        passed, reason = evaluate_criterion(crit, [])
        assert passed is False
        assert "No measurement" in reason or "values" in reason.lower()

    def test_reason_not_empty_on_fail(self) -> None:
        crit = PerfCriterion(threshold=999.0, aggregate=Aggregate.MEDIAN, repetitions=1)
        passed, reason = evaluate_criterion(crit, [1.0])
        assert passed is False
        assert len(reason) > 0


# ---------------------------------------------------------------------------
# evaluate_criterion — missing threshold → pytest.skip
# ---------------------------------------------------------------------------


class TestEvaluateCriterionSkip:
    def test_none_threshold_triggers_skip(self) -> None:
        """A criterion with threshold=None must call pytest.skip()."""
        crit = PerfCriterion(threshold=None, aggregate=Aggregate.MEDIAN, repetitions=3)
        with pytest.raises(pytest.skip.Exception):
            evaluate_criterion(crit, [100.0, 200.0, 300.0])

    def test_rfc2544_profile_skips_without_threshold(self) -> None:
        """The RFC2544 base profile has threshold=None → skip."""
        assert RFC2544_PROFILE.threshold is None
        with pytest.raises(pytest.skip.Exception):
            evaluate_criterion(RFC2544_PROFILE, [900.0, 910.0, 920.0])

    def test_rfc6349_profile_skips_without_threshold(self) -> None:
        """The RFC6349 base profile has threshold=None → skip."""
        assert RFC6349_PROFILE.threshold is None
        with pytest.raises(pytest.skip.Exception):
            evaluate_criterion(RFC6349_PROFILE, [800.0, 820.0, 830.0])

    def test_skip_message_mentions_threshold(self) -> None:
        crit = PerfCriterion(threshold=None, aggregate=Aggregate.P95, repetitions=1)
        with pytest.raises(pytest.skip.Exception) as exc_info:
            evaluate_criterion(crit, [50.0])
        assert "threshold" in str(exc_info.value).lower() or "No threshold" in str(exc_info.value)


# ---------------------------------------------------------------------------
# RFC preset profiles — structural checks
# ---------------------------------------------------------------------------


class TestRFCProfiles:
    def test_rfc2544_transport_is_udp(self) -> None:
        assert RFC2544_PROFILE.transport is Transport.UDP

    def test_rfc2544_aggregate_is_min(self) -> None:
        assert RFC2544_PROFILE.aggregate is Aggregate.MIN

    def test_rfc2544_duration(self) -> None:
        assert RFC2544_PROFILE.duration_s == 60

    def test_rfc2544_repetitions(self) -> None:
        assert RFC2544_PROFILE.repetitions == 3

    def test_rfc6349_transport_is_tcp(self) -> None:
        assert RFC6349_PROFILE.transport is Transport.TCP

    def test_rfc6349_aggregate_is_median(self) -> None:
        assert RFC6349_PROFILE.aggregate is Aggregate.MEDIAN

    def test_rfc6349_duration(self) -> None:
        assert RFC6349_PROFILE.duration_s == 30

    def test_rfc6349_repetitions(self) -> None:
        assert RFC6349_PROFILE.repetitions == 5

    def test_profiles_are_perf_criterion(self) -> None:
        assert isinstance(RFC2544_PROFILE, PerfCriterion)
        assert isinstance(RFC6349_PROFILE, PerfCriterion)


# ---------------------------------------------------------------------------
# PerfCriterion model validation
# ---------------------------------------------------------------------------


class TestPerfCriterionModel:
    def test_tolerance_default(self) -> None:
        c = PerfCriterion()
        assert c.tolerance == 0.0

    def test_transport_enum(self) -> None:
        c = PerfCriterion(transport=Transport.TCP)
        assert c.transport is Transport.TCP

    def test_aggregate_enum(self) -> None:
        c = PerfCriterion(aggregate=Aggregate.P95)
        assert c.aggregate is Aggregate.P95

    def test_threshold_none_by_default(self) -> None:
        c = PerfCriterion()
        assert c.threshold is None

    def test_threshold_set(self) -> None:
        c = PerfCriterion(threshold=500.0)
        assert c.threshold == 500.0

    def test_invalid_tolerance_raises(self) -> None:
        with pytest.raises(ValidationError):
            PerfCriterion(tolerance=1.5)  # > 1.0

    def test_zero_duration_raises(self) -> None:
        with pytest.raises(ValidationError):
            PerfCriterion(duration_s=0)

    def test_zero_repetitions_raises(self) -> None:
        with pytest.raises(ValidationError):
            PerfCriterion(repetitions=0)
