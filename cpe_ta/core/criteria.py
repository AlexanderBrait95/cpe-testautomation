"""Pass/Fail methodology for performance tests.

Key concepts
------------
PerfCriterion
    Defines how a performance measurement should be aggregated and
    compared against a threshold.  A ``threshold=None`` means "no
    threshold configured for this criterion" → the test is skipped
    (REQ-CRIT-03: silent pass is forbidden).

compute_aggregate(values, agg)
    Pure, deterministic function — no side-effects, unit-testable.

evaluate_criterion(criterion, values) -> (passed, reason)
    Aggregates *values* per the criterion, then compares against
    the threshold.  Calls ``pytest.skip()`` when threshold is None.

RFC Presets
-----------
RFC2544_PROFILE — Layer 2/3 throughput (UDP, min aggregate).
RFC6349_PROFILE — TCP goodput (TCP, median aggregate).
"""

from __future__ import annotations

import statistics
from enum import StrEnum
from typing import NamedTuple

import pytest
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Transport(StrEnum):
    """IP transport protocol for the traffic tool."""

    TCP = "tcp"
    UDP = "udp"


class Aggregate(StrEnum):
    """Statistical aggregation method applied to repeated measurements."""

    MEDIAN = "median"
    MIN = "min"
    P95 = "p95"


# ---------------------------------------------------------------------------
# PerfCriterion model
# ---------------------------------------------------------------------------


class PerfCriterion(BaseModel):
    """Performance measurement criterion.

    Attributes
    ----------
    tolerance:
        Acceptable deviation ratio (e.g. 0.05 = 5 %).  Reserved for
        future use (round-trip jitter compensation).
    duration_s:
        Duration of each measurement run in seconds.
    transport:
        IP transport protocol (TCP or UDP).
    tool:
        Traffic tool identifier (e.g. ``"iperf3"``, ``"scapy"``).
    repetitions:
        Number of measurement repetitions to collect before aggregating.
    aggregate:
        Statistical aggregation method applied to the *repetitions* values.
    threshold:
        Minimum acceptable value (e.g. Mbit/s).  ``None`` means no
        threshold is configured — the test will be skipped.
    """

    tolerance: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_s: int = Field(default=30, gt=0)
    transport: Transport = Transport.TCP
    tool: str = "iperf3"
    repetitions: int = Field(default=3, ge=1)
    aggregate: Aggregate = Aggregate.MEDIAN
    threshold: float | None = None


# ---------------------------------------------------------------------------
# Result namedtuple (for internal use)
# ---------------------------------------------------------------------------


class _EvalResult(NamedTuple):
    passed: bool
    reason: str


# ---------------------------------------------------------------------------
# Pure aggregation function
# ---------------------------------------------------------------------------


def compute_aggregate(values: list[float], agg: Aggregate) -> float:
    """Compute the statistical aggregate of *values*.

    Parameters
    ----------
    values:
        Non-empty list of measured values (e.g. throughput in Mbit/s).
    agg:
        Aggregation method to apply.

    Returns
    -------
    float
        The aggregated value.

    Raises
    ------
    ValueError
        When *values* is empty.
    """
    if not values:
        raise ValueError("compute_aggregate requires at least one value")

    if agg is Aggregate.MEDIAN:
        return statistics.median(values)
    if agg is Aggregate.MIN:
        return min(values)
    if agg is Aggregate.P95:
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * 0.95)
        # Clamp to last element
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    # Exhaustive enum — should never reach here
    raise ValueError(f"Unknown aggregate: {agg!r}")  # pragma: no cover


# ---------------------------------------------------------------------------
# Evaluation function
# ---------------------------------------------------------------------------


def evaluate_criterion(
    criterion: PerfCriterion,
    values: list[float],
) -> tuple[bool, str]:
    """Evaluate whether *values* satisfy *criterion*.

    Parameters
    ----------
    criterion:
        The performance criterion to apply.
    values:
        Measured samples (length must match ``criterion.repetitions``).

    Returns
    -------
    (passed, reason)
        ``passed`` is True when the aggregate meets or exceeds the
        threshold.  ``reason`` is a human-readable explanation.

    Side effects
    ------------
    Calls ``pytest.skip()`` when ``criterion.threshold is None``.
    This is intentional: a missing threshold must never silently pass
    (REQ-CRIT-03).
    """
    if criterion.threshold is None:
        pytest.skip(
            f"No threshold configured for criterion "
            f"(tool={criterion.tool!r}, transport={criterion.transport.value}, "
            f"aggregate={criterion.aggregate.value}) — skipping instead of silent pass"
        )

    if not values:
        return False, "No measurement values provided"

    agg_value = compute_aggregate(values, criterion.aggregate)
    passed = agg_value >= criterion.threshold
    direction = ">=" if passed else "<"
    reason = (
        f"{criterion.aggregate.value}({values}) = {agg_value:.4f} "
        f"{direction} threshold={criterion.threshold:.4f} "
        f"[tool={criterion.tool}, transport={criterion.transport.value}, "
        f"duration={criterion.duration_s}s, reps={criterion.repetitions}]"
    )
    return passed, reason


# ---------------------------------------------------------------------------
# RFC preset profiles
# ---------------------------------------------------------------------------

RFC2544_PROFILE = PerfCriterion(
    tolerance=0.0,
    duration_s=60,
    transport=Transport.UDP,
    tool="iperf3",
    repetitions=3,
    aggregate=Aggregate.MIN,
    threshold=None,  # Line-rate threshold must be set per-interface in profiles/
)
"""RFC 2544 (Layer 2/3 throughput, UDP, minimum aggregate).

The threshold is left as ``None`` because line-rate depends on the
physical interface speed.  Override in ``profiles/rfc2544.yaml``.
"""

RFC6349_PROFILE = PerfCriterion(
    tolerance=0.05,
    duration_s=30,
    transport=Transport.TCP,
    tool="iperf3",
    repetitions=5,
    aggregate=Aggregate.MEDIAN,
    threshold=None,  # Goodput threshold set per-link in profiles/
)
"""RFC 6349 (TCP goodput, median aggregate).

The threshold is left as ``None`` because goodput depends on the
access technology and provisioned speed.  Override in ``profiles/rfc6349.yaml``.
"""
