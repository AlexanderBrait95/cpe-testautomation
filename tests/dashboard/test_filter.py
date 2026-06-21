"""Tests for run/entry filter + sort (AC-34, TB-02)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app
from cpe_ta.dashboard.data import filter_entries, filter_runs, sort_runs
from cpe_ta.dashboard.models import RunSummary, TestEntry

pytestmark = pytest.mark.headless

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BASE_TS = 1_700_000_000.0


def _run(run_id: str, passed: int = 5, failed: int = 0, git_sha: str = "", ts_offset: float = 0.0, dur: float = 10.0) -> RunSummary:
    return RunSummary(
        run_id=run_id,
        timestamp=_BASE_TS + ts_offset,
        duration_s=dur,
        passed=passed,
        failed=failed,
        skipped=0,
        error=0,
        total=passed + failed,
        git_sha=git_sha,
    )


def _entry(name: str, domain: str, status: str, dur: float = 1.0) -> TestEntry:
    return TestEntry(name=name, domain=domain, status=status, duration_s=dur)


RUNS = [
    _run("run-aaa", passed=5, failed=0, ts_offset=0,   dur=5.0,  git_sha="abc123"),
    _run("run-bbb", passed=3, failed=2, ts_offset=10,  dur=30.0, git_sha="def456"),
    _run("run-ccc", passed=0, failed=5, ts_offset=20,  dur=50.0, git_sha="abc789"),
]

ENTRIES = [
    _entry("test_lan_link",       domain="lan",  status="passed",  dur=1.0),
    _entry("test_lan_vlan",       domain="lan",  status="failed",  dur=2.0),
    _entry("test_wifi_sec",       domain="wifi", status="passed",  dur=3.0),
    _entry("test_wifi_ssid",      domain="wifi", status="skipped", dur=0.5),
    _entry("test_qos_throughput", domain="qos",  status="passed",  dur=10.0),
]


# ---------------------------------------------------------------------------
# filter_runs unit tests
# ---------------------------------------------------------------------------

def test_filter_runs_no_filter_returns_all():
    assert filter_runs(RUNS) == RUNS


def test_filter_runs_q_by_run_id():
    result = filter_runs(RUNS, q="bbb")
    assert len(result) == 1
    assert result[0].run_id == "run-bbb"


def test_filter_runs_q_by_git_sha():
    result = filter_runs(RUNS, q="abc")
    assert len(result) == 2  # "abc123" and "abc789"
    ids = {r.run_id for r in result}
    assert "run-aaa" in ids
    assert "run-ccc" in ids


def test_filter_runs_q_no_match_returns_empty():
    result = filter_runs(RUNS, q="zzz-no-match")
    assert result == []


# ---------------------------------------------------------------------------
# sort_runs unit tests
# ---------------------------------------------------------------------------

def test_sort_runs_no_sort_returns_original_order():
    result = sort_runs(RUNS)
    assert [r.run_id for r in result] == [r.run_id for r in RUNS]


def test_sort_runs_by_time_ascending():
    result = sort_runs(RUNS, sort="time")
    assert result[0].run_id == "run-aaa"
    assert result[-1].run_id == "run-ccc"


def test_sort_runs_by_time_descending():
    result = sort_runs(RUNS, sort="-time")
    assert result[0].run_id == "run-ccc"
    assert result[-1].run_id == "run-aaa"


def test_sort_runs_by_duration_ascending():
    result = sort_runs(RUNS, sort="duration")
    assert result[0].run_id == "run-aaa"   # dur=5
    assert result[-1].run_id == "run-ccc"  # dur=50


def test_sort_runs_by_status_fail_first():
    result = sort_runs(RUNS, sort="status")
    # run-aaa is all-passed → must be last; run-bbb and run-ccc both have failures → first two
    failed_ids = {r.run_id for r in result[:2]}
    assert "run-bbb" in failed_ids
    assert "run-ccc" in failed_ids
    assert result[-1].run_id == "run-aaa"


def test_sort_runs_unknown_key_returns_original():
    result = sort_runs(RUNS, sort="totally_invalid")
    assert [r.run_id for r in result] == [r.run_id for r in RUNS]


# ---------------------------------------------------------------------------
# filter_entries unit tests
# ---------------------------------------------------------------------------

def test_filter_entries_no_filter_returns_all():
    assert filter_entries(ENTRIES) == ENTRIES


def test_filter_entries_by_status_failed():
    result = filter_entries(ENTRIES, status="failed")
    assert all(e.status == "failed" for e in result)
    assert len(result) == 1


def test_filter_entries_by_status_passed():
    result = filter_entries(ENTRIES, status="passed")
    assert all(e.status == "passed" for e in result)
    assert len(result) == 3


def test_filter_entries_by_domain_lan():
    result = filter_entries(ENTRIES, domain="lan")
    assert all(e.domain == "lan" for e in result)
    assert len(result) == 2


def test_filter_entries_by_domain_wifi():
    result = filter_entries(ENTRIES, domain="wifi")
    assert len(result) == 2


def test_filter_entries_by_q_name():
    result = filter_entries(ENTRIES, q="vlan")
    assert len(result) == 1
    assert result[0].name == "test_lan_vlan"


def test_filter_entries_combined_status_and_domain():
    result = filter_entries(ENTRIES, status="passed", domain="lan")
    assert len(result) == 1
    assert result[0].name == "test_lan_link"


def test_filter_entries_invalid_status_ignored():
    # Unknown status should not crash — treated as "no filter"
    result = filter_entries(ENTRIES, status="bogus_status")
    assert result == ENTRIES


# ---------------------------------------------------------------------------
# API route tests (AC-34)
# ---------------------------------------------------------------------------

from pathlib import Path  # noqa: E402

SAMPLE_XML = str(Path(__file__).parent / "fixtures" / "sample-results.xml")


def test_api_runs_no_filter_returns_full_list():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    r = client.get("/api/runs")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_api_runs_q_filter_narrows_results():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    r_all = client.get("/api/runs")
    r_filtered = client.get("/api/runs?q=zzz-no-match")
    assert r_filtered.status_code == 200
    assert len(r_filtered.json()) <= len(r_all.json())
    assert r_filtered.json() == []


def test_api_runs_sort_accepted():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    r = client.get("/api/runs?sort=time")
    assert r.status_code == 200


def test_api_run_detail_no_filter_returns_all_tests():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    runs = client.get("/api/runs").json()
    assert runs
    run_id = runs[0]["run_id"]
    r_all = client.get(f"/api/runs/{run_id}")
    r_filtered = client.get(f"/api/runs/{run_id}?status=passed")
    assert r_all.status_code == 200
    assert r_filtered.status_code == 200
    # filtered must be <= full
    assert len(r_filtered.json()["tests"]) <= len(r_all.json()["tests"])


def test_api_run_detail_domain_filter():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    runs = client.get("/api/runs").json()
    run_id = runs[0]["run_id"]
    r = client.get(f"/api/runs/{run_id}?domain=lan")
    assert r.status_code == 200
    tests = r.json()["tests"]
    assert all(t["domain"] == "lan" for t in tests)
