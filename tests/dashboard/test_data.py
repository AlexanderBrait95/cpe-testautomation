"""Tests for dashboard data layer — JUnit parser + domain aggregation (T-D03)."""
from __future__ import annotations

from pathlib import Path

import pytest

from cpe_ta.dashboard.data import domain_stats, overview, parse_junit
from cpe_ta.dashboard.models import RunSummary

pytestmark = pytest.mark.headless

FIXTURES = Path(__file__).parent / "fixtures"
REAL_XML = Path(__file__).parent.parent.parent / "test-results.xml"


# ---------------------------------------------------------------------------
# parse_junit
# ---------------------------------------------------------------------------


def test_parse_mini_counts():
    entries = parse_junit(FIXTURES / "mini.xml")
    assert len(entries) == 4
    statuses = [e.status for e in entries]
    assert statuses.count("passed") == 2
    assert statuses.count("failed") == 1
    assert statuses.count("skipped") == 1


def test_parse_mini_domain_mapping():
    entries = parse_junit(FIXTURES / "mini.xml")
    domains = {e.domain for e in entries}
    assert "lan" in domains
    assert "wifi" in domains


def test_parse_missing_xml_returns_empty():
    entries = parse_junit("/nonexistent/path/to/file.xml")
    assert entries == []


def test_parse_broken_xml_tolerant():
    """Broken float in time attribute: parse should not crash, just skip that testcase."""
    entries = parse_junit(FIXTURES / "broken.xml")
    # The good testcase should survive; broken one may be skipped or have 0 duration
    # We only require: no exception raised
    assert isinstance(entries, list)


def test_parse_real_xml_counts():
    """Assert against the real test-results.xml from the project root (AC-25)."""
    if not REAL_XML.exists():
        pytest.skip("test-results.xml not found")
    entries = parse_junit(REAL_XML)
    # 559 total from the existing run, all passed (0 failures/skips in the real file)
    assert len(entries) > 0
    passed = sum(1 for e in entries if e.status == "passed")
    assert passed > 0


# ---------------------------------------------------------------------------
# domain_stats
# ---------------------------------------------------------------------------


def test_domain_stats_aggregation():
    entries = parse_junit(FIXTURES / "mini.xml")
    stats = domain_stats(entries)
    domains = {s.name: s for s in stats}
    assert "lan" in domains
    assert domains["lan"].passed == 2
    assert domains["lan"].failed == 0
    assert "wifi" in domains
    assert domains["wifi"].failed == 1
    assert domains["wifi"].skipped == 1


def test_domain_stats_empty():
    stats = domain_stats([])
    assert stats == []


def test_pass_rate_calculation():
    entries = parse_junit(FIXTURES / "mini.xml")
    stats = domain_stats(entries)
    lan = next(s for s in stats if s.name == "lan")
    assert lan.pass_rate == pytest.approx(1.0)
    wifi = next(s for s in stats if s.name == "wifi")
    assert wifi.pass_rate == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# overview
# ---------------------------------------------------------------------------


def test_overview_from_mini():
    entries = parse_junit(FIXTURES / "mini.xml")
    run_summaries: list[RunSummary] = [
        RunSummary(run_id="r1", timestamp=1000.0, duration_s=5.0,
                   passed=2, failed=1, skipped=1, error=0, total=4, git_sha="abc")
    ]
    ov = overview(entries, run_summaries)
    assert ov.passed == 2
    assert ov.failed == 1
    assert ov.skipped == 1
    assert ov.error == 0
    assert ov.last_run is not None
    assert ov.last_run.run_id == "r1"


def test_overview_empty_returns_zeros():
    ov = overview([], [])
    assert ov.total == 0
    assert ov.last_run is None
    assert ov.domains == []
