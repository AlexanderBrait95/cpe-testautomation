"""T20 — ResultsDB: SQLite persistence, migrations, trend queries."""
from __future__ import annotations

import time

import pytest

from cpe_ta.core.results import ResultsDB, RunMetadata, TestResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_run(run_id: str = "run-001", fw: str = "1.0.0") -> RunMetadata:
    return RunMetadata(
        run_id=run_id,
        dut_id="dut-sim",
        firmware_version=fw,
        timestamp=time.time(),
        git_sha="abc1234",
        marker_expr="headless",
        total_tests=3,
        passed=2,
        failed=1,
        errors=0,
        skipped=0,
    )


def _make_result(
    test_id: str = "t-001",
    run_id: str = "run-001",
    fw: str = "1.0.0",
    domain: str = "lan",
    outcome: str = "passed",
) -> TestResult:
    return TestResult(
        test_id=test_id,
        run_id=run_id,
        dut_id="dut-sim",
        firmware_version=fw,
        timestamp=time.time(),
        git_sha="abc1234",
        domain=domain,
        test_name=f"test_{test_id}",
        outcome=outcome,
        duration_s=0.5,
        details={"msg": "ok"},
    )


# ---------------------------------------------------------------------------
# connect / close / schema
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_connect_and_close_in_memory():
    """connect() must succeed for an in-memory DB and close() must not raise."""
    db = ResultsDB()
    db.connect()
    db.close()


@pytest.mark.headless
def test_schema_version_set_after_migrate():
    """After connect() the schema_version table must contain version 1."""
    db = ResultsDB()
    db.connect()
    conn = db._require_conn()
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    assert row is not None
    assert row[0] == 1
    db.close()


@pytest.mark.headless
def test_require_conn_raises_when_not_connected():
    """_require_conn must raise RuntimeError when called before connect()."""
    db = ResultsDB()
    with pytest.raises(RuntimeError, match="not connected"):
        db._require_conn()


# ---------------------------------------------------------------------------
# save_run / get_runs
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_save_and_get_runs():
    """save_run followed by get_runs must return the persisted run."""
    with ResultsDB() as db:
        run = _make_run("r-save-get")
        db.save_run(run)
        runs = db.get_runs()
    assert len(runs) == 1
    assert runs[0].run_id == "r-save-get"
    assert runs[0].firmware_version == "1.0.0"


@pytest.mark.headless
def test_multiple_runs_ordered_by_timestamp():
    """get_runs must return rows ordered by timestamp (ascending)."""
    with ResultsDB() as db:
        run_a = RunMetadata(
            run_id="r-a",
            dut_id="d",
            firmware_version="1.0",
            timestamp=1000.0,
            git_sha="sha1",
            marker_expr="",
            total_tests=1,
            passed=1,
            failed=0,
            errors=0,
            skipped=0,
        )
        run_b = RunMetadata(
            run_id="r-b",
            dut_id="d",
            firmware_version="2.0",
            timestamp=2000.0,
            git_sha="sha2",
            marker_expr="",
            total_tests=1,
            passed=1,
            failed=0,
            errors=0,
            skipped=0,
        )
        db.save_run(run_b)
        db.save_run(run_a)
        runs = db.get_runs()

    assert runs[0].run_id == "r-a"
    assert runs[1].run_id == "r-b"


# ---------------------------------------------------------------------------
# save_result / query
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_save_result_and_query():
    """save_result must persist a result retrievable via get_results_for_run."""
    with ResultsDB() as db:
        run = _make_run("r-res")
        db.save_run(run)
        result = _make_result(test_id="t-r-res", run_id="r-res")
        db.save_result(result)
        results = db.get_results_for_run("r-res")

    assert len(results) == 1
    assert results[0].test_id == "t-r-res"
    assert results[0].details == {"msg": "ok"}


# ---------------------------------------------------------------------------
# Trend query
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_trend_query_two_firmware_versions():
    """get_trend must aggregate outcomes per firmware version."""
    with ResultsDB() as db:
        # Two firmware versions, both in domain "lan"
        for fw in ("1.0.0", "2.0.0"):
            run_id = f"r-{fw}"
            db.save_run(_make_run(run_id=run_id, fw=fw))
            db.save_result(_make_result(test_id=f"t-{fw}-pass", run_id=run_id, fw=fw, domain="lan", outcome="passed"))
            db.save_result(_make_result(test_id=f"t-{fw}-fail", run_id=run_id, fw=fw, domain="lan", outcome="failed"))

        trend = db.get_trend("lan")

    assert len(trend) >= 2, f"Expected at least 2 trend rows, got: {trend}"
    fw_versions = {row["firmware_version"] for row in trend}
    assert "1.0.0" in fw_versions
    assert "2.0.0" in fw_versions


@pytest.mark.headless
def test_trend_query_empty_for_unknown_domain():
    """get_trend on an unknown domain must return an empty list."""
    with ResultsDB() as db:
        trend = db.get_trend("nonexistent_domain")
    assert trend == []


# ---------------------------------------------------------------------------
# Transactional safety — duplicate test_id → replace, no duplicates
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_duplicate_test_id_is_replaced():
    """Saving a result with the same test_id twice must replace, not duplicate."""
    with ResultsDB() as db:
        run = _make_run("r-dedup")
        db.save_run(run)

        r1 = _make_result(test_id="t-dup", run_id="r-dedup", outcome="passed")
        r2 = _make_result(test_id="t-dup", run_id="r-dedup", outcome="failed")
        db.save_result(r1)
        db.save_result(r2)  # must replace r1

        results = db.get_results_for_run("r-dedup")

    assert len(results) == 1, "Duplicate test_id must be replaced, not duplicated"
    assert results[0].outcome == "failed", "Latest value must win"


@pytest.mark.headless
def test_duplicate_run_id_is_replaced():
    """Saving a RunMetadata with the same run_id twice must replace, not duplicate."""
    with ResultsDB() as db:
        run_v1 = _make_run("r-replace")
        run_v2 = RunMetadata(
            run_id="r-replace",
            dut_id="dut-sim",
            firmware_version="9.9.9",
            timestamp=time.time(),
            git_sha="newsha",
            marker_expr="smoke",
            total_tests=10,
            passed=10,
            failed=0,
            errors=0,
            skipped=0,
        )
        db.save_run(run_v1)
        db.save_run(run_v2)
        runs = db.get_runs()

    assert len(runs) == 1
    assert runs[0].firmware_version == "9.9.9"


# ---------------------------------------------------------------------------
# Context-manager interface
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_context_manager_usage(tmp_path):
    """ResultsDB must work as a context manager (connect on enter, close on exit)."""
    db_file = str(tmp_path / "ctx_test.db")
    with ResultsDB(db_path=db_file) as db:
        run = _make_run("r-ctx")
        db.save_run(run)
        runs = db.get_runs()
    assert len(runs) == 1
    # After __exit__ the connection must be closed
    assert db._conn is None


@pytest.mark.headless
def test_persistent_db_survives_reconnect(tmp_path):
    """Data written in one connection must be readable after reconnect."""
    db_file = str(tmp_path / "persist.db")

    with ResultsDB(db_path=db_file) as db:
        db.save_run(_make_run("r-persist"))

    with ResultsDB(db_path=db_file) as db:
        runs = db.get_runs()

    assert len(runs) == 1
    assert runs[0].run_id == "r-persist"
