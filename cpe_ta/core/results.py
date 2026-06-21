"""Test result model, SQLite persistence with schema migrations."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = 1


@dataclass
class TestResult:
    test_id: str
    run_id: str
    dut_id: str
    firmware_version: str
    timestamp: float
    git_sha: str
    domain: str  # lan/wifi/qos/wan/dhcp/multicast/ipv6/security/acs
    test_name: str
    outcome: str  # passed/failed/error/skipped
    duration_s: float
    details: dict[str, Any]


@dataclass
class RunMetadata:
    run_id: str
    dut_id: str
    firmware_version: str
    timestamp: float
    git_sha: str
    marker_expr: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int


class ResultsDB:
    """SQLite-backed test result store — WAL mode, transactional writes."""

    def __init__(self, db_path: str = ":memory:"):
        self._path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _migrate(self) -> None:
        conn = self._require_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        current = row[0] if row else 0
        if current < 1:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    dut_id TEXT NOT NULL,
                    firmware_version TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    git_sha TEXT NOT NULL,
                    marker_expr TEXT DEFAULT '',
                    total_tests INTEGER DEFAULT 0,
                    passed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    skipped INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS test_results (
                    test_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    dut_id TEXT NOT NULL,
                    firmware_version TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    git_sha TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    duration_s REAL NOT NULL,
                    details_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_results_run ON test_results(run_id);
                CREATE INDEX IF NOT EXISTS idx_results_fw ON test_results(firmware_version);
                CREATE INDEX IF NOT EXISTS idx_results_domain ON test_results(domain);
            """)
            conn.execute("INSERT OR REPLACE INTO schema_version VALUES (1)")
            conn.commit()

    def save_run(self, meta: RunMetadata) -> None:
        conn = self._require_conn()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    meta.run_id,
                    meta.dut_id,
                    meta.firmware_version,
                    meta.timestamp,
                    meta.git_sha,
                    meta.marker_expr,
                    meta.total_tests,
                    meta.passed,
                    meta.failed,
                    meta.errors,
                    meta.skipped,
                ),
            )

    def save_result(self, result: TestResult) -> None:
        conn = self._require_conn()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO test_results VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    result.test_id,
                    result.run_id,
                    result.dut_id,
                    result.firmware_version,
                    result.timestamp,
                    result.git_sha,
                    result.domain,
                    result.test_name,
                    result.outcome,
                    result.duration_s,
                    json.dumps(result.details),
                ),
            )

    def get_results_for_run(self, run_id: str) -> list[TestResult]:
        """Return all TestResult rows for a given run_id."""
        conn = self._require_conn()
        rows = conn.execute(
            "SELECT * FROM test_results WHERE run_id = ? ORDER BY timestamp",
            (run_id,),
        ).fetchall()
        return [
            TestResult(
                test_id=r[0],
                run_id=r[1],
                dut_id=r[2],
                firmware_version=r[3],
                timestamp=r[4],
                git_sha=r[5],
                domain=r[6],
                test_name=r[7],
                outcome=r[8],
                duration_s=r[9],
                details=json.loads(r[10]),
            )
            for r in rows
        ]

    def get_trend(self, domain: str, metric: str = "outcome") -> list[dict[str, Any]]:
        """Trend query: results grouped by firmware_version for a domain."""
        conn = self._require_conn()
        rows = conn.execute(
            """SELECT firmware_version, outcome, COUNT(*) as cnt
               FROM test_results WHERE domain = ?
               GROUP BY firmware_version, outcome
               ORDER BY firmware_version""",
            (domain,),
        ).fetchall()
        return [{"firmware_version": r[0], "outcome": r[1], "count": r[2]} for r in rows]

    def get_runs(self) -> list[RunMetadata]:
        conn = self._require_conn()
        rows = conn.execute("SELECT * FROM runs ORDER BY timestamp").fetchall()
        return [RunMetadata(*r) for r in rows]

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("DB not connected — call connect() first")
        return self._conn

    def __enter__(self) -> ResultsDB:
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
