"""Tests for dashboard DB-backed data layer (T-D04)."""
from __future__ import annotations

import pytest

from cpe_ta.core.results import ResultsDB, RunMetadata, TestResult
from cpe_ta.dashboard.data import get_run_detail, get_run_summaries

pytestmark = pytest.mark.headless


def _make_db(tmp_path, runs: list[RunMetadata], results: list[TestResult]) -> str:
    db_path = str(tmp_path / "test.db")
    with ResultsDB(db_path=db_path) as db:
        for r in runs:
            db.save_run(r)
        for res in results:
            db.save_result(res)
    return db_path


def _run(run_id: str = "r1") -> RunMetadata:
    return RunMetadata(
        run_id=run_id, dut_id="dut1", firmware_version="v1.0",
        timestamp=1000.0, git_sha="abc123", marker_expr="headless",
        total_tests=3, passed=2, failed=1, errors=0, skipped=0,
    )


def _result(run_id: str, test_name: str, outcome: str = "passed") -> TestResult:
    return TestResult(
        test_id=f"{run_id}-{test_name}", run_id=run_id, dut_id="dut1",
        firmware_version="v1.0", timestamp=1000.0, git_sha="abc123",
        domain="lan", test_name=test_name, outcome=outcome,
        duration_s=0.1, details={},
    )


# ---------------------------------------------------------------------------
# get_run_summaries
# ---------------------------------------------------------------------------


def test_get_run_summaries_empty_db(tmp_path):
    db_path = str(tmp_path / "empty.db")
    with ResultsDB(db_path=db_path) as _:
        pass
    summaries = get_run_summaries(db_path)
    assert summaries == []


def test_get_run_summaries_with_runs(tmp_path):
    db_path = _make_db(tmp_path, [_run("r1"), _run("r2")], [])
    summaries = get_run_summaries(db_path)
    assert len(summaries) == 2
    ids = {s.run_id for s in summaries}
    assert ids == {"r1", "r2"}


def test_get_run_summaries_missing_file():
    summaries = get_run_summaries("/nonexistent/path.db")
    assert summaries == []


def test_get_run_summaries_none_path():
    assert get_run_summaries(None) == []


# ---------------------------------------------------------------------------
# get_run_detail
# ---------------------------------------------------------------------------


def test_get_run_detail_found(tmp_path):
    db_path = _make_db(
        tmp_path,
        [_run("r1")],
        [_result("r1", "test_foo"), _result("r1", "test_bar", "failed")],
    )
    detail = get_run_detail(db_path, "r1")
    assert detail is not None
    assert detail.run_id == "r1"
    assert len(detail.tests) == 2


def test_get_run_detail_not_found(tmp_path):
    db_path = _make_db(tmp_path, [_run("r1")], [])
    detail = get_run_detail(db_path, "nonexistent")
    assert detail is None


def test_get_run_detail_missing_db():
    detail = get_run_detail("/nonexistent/path.db", "r1")
    assert detail is None


def test_get_run_detail_none_path():
    assert get_run_detail(None, "r1") is None
