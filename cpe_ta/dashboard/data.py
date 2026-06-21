"""Data aggregation layer: JUnit-XML parser + ResultsDB reader."""
from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from cpe_ta.dashboard.models import (
    DeviceStatus,
    DomainStat,
    LastRun,
    OverviewModel,
    RunDetail,
    RunSummary,
    TestbedStatus,
    TestEntry,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATUS_MAP = {"failure": "failed", "error": "error", "skipped": "skipped"}


def _domain_from_classname(classname: str) -> str:
    """Extract domain from JUnit classname or pytest node path.

    Strategy: split on '.' and look for the segment after 'tests'.
    Falls back to the first classname segment.
    """
    parts = classname.replace("::", ".").split(".")
    for i, part in enumerate(parts):
        if part == "tests" and i + 1 < len(parts):
            return parts[i + 1]
    return parts[0] if parts else "unknown"


def _tc_status(tc: ET.Element) -> tuple[str, str | None, str | None]:
    """Return (status, message, stacktrace) for a testcase element."""
    for tag, mapped in _STATUS_MAP.items():
        child = tc.find(tag)
        if child is not None:
            return mapped, child.get("message"), child.text
    return "passed", None, None


# ---------------------------------------------------------------------------
# JUnit XML parser
# ---------------------------------------------------------------------------


def parse_junit(path: str | Path) -> list[TestEntry]:
    """Parse a JUnit XML file into a flat list of TestEntry objects.

    Tolerant: skips malformed testcase nodes with a warning; never raises.
    Returns [] when file is missing or unreadable.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        tree = ET.parse(str(p))
        root = tree.getroot()
    except ET.ParseError as exc:
        logger.warning("JUnit XML parse error (%s): %s — returning empty list", p, exc)
        return []

    entries: list[TestEntry] = []
    # Support both <testsuite> and <testsuites><testsuite>
    suites = root.findall(".//testcase")
    for tc in suites:
        try:
            classname = tc.get("classname", "unknown")
            name = tc.get("name", "unnamed")
            duration = float(tc.get("time", "0.0"))
            domain = _domain_from_classname(classname)
            status, msg, trace = _tc_status(tc)
            entries.append(
                TestEntry(
                    name=name,
                    domain=domain,
                    status=status,
                    duration_s=duration,
                    message=msg,
                    stacktrace=trace,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping malformed testcase node: %s", exc)
    return entries


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------


def _domain_stats(entries: list[TestEntry]) -> list[DomainStat]:
    domains: dict[str, dict[str, int]] = {}
    for e in entries:
        d = domains.setdefault(e.domain, {"passed": 0, "failed": 0, "skipped": 0, "error": 0})
        key = e.status if e.status in d else "error"
        d[key] += 1
    result: list[DomainStat] = []
    for name, counts in sorted(domains.items()):
        total = sum(counts.values())
        result.append(
            DomainStat(
                name=name,
                passed=counts["passed"],
                failed=counts["failed"],
                skipped=counts["skipped"],
                error=counts["error"],
                total=total,
                pass_rate=counts["passed"] / total if total else 0.0,
            )
        )
    return result


def overview(entries: list[TestEntry], run_summaries: list[RunSummary]) -> OverviewModel:
    """Build OverviewModel from flat TestEntry list and run history."""
    passed = sum(1 for e in entries if e.status == "passed")
    failed = sum(1 for e in entries if e.status == "failed")
    skipped = sum(1 for e in entries if e.status == "skipped")
    error = sum(1 for e in entries if e.status == "error")

    last_run: LastRun | None = None
    if run_summaries:
        latest = max(run_summaries, key=lambda r: r.timestamp)
        last_run = LastRun(
            run_id=latest.run_id,
            timestamp=latest.timestamp,
            duration_s=latest.duration_s,
            git_sha=latest.git_sha,
        )

    return OverviewModel(
        passed=passed,
        failed=failed,
        skipped=skipped,
        error=error,
        total=len(entries),
        last_run=last_run,
        domains=_domain_stats(entries),
    )


def domain_stats(entries: list[TestEntry]) -> list[DomainStat]:
    return _domain_stats(entries)


# ---------------------------------------------------------------------------
# DB reader (ResultsDB bridge)
# ---------------------------------------------------------------------------


def _try_import_results_db() -> Any:
    """Lazy import to avoid hard dependency in test isolation."""
    from cpe_ta.core.results import ResultsDB  # noqa: PLC0415

    return ResultsDB


def get_run_summaries(db_path: str | None) -> list[RunSummary]:
    """Read RunSummary list from SQLite ResultsDB. Returns [] on any error."""
    if not db_path:
        return []
    p = Path(db_path)
    if not p.exists():
        return []
    try:
        ResultsDB = _try_import_results_db()
        with ResultsDB(db_path=str(p)) as db:
            runs = db.get_runs()
        summaries: list[RunSummary] = []
        for r in runs:
            summaries.append(
                RunSummary(
                    run_id=r.run_id,
                    timestamp=r.timestamp,
                    duration_s=0.0,
                    passed=r.passed,
                    failed=r.failed,
                    skipped=r.skipped,
                    error=r.errors,
                    total=r.total_tests,
                    git_sha=r.git_sha,
                )
            )
        return summaries
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB read error (%s): %s", db_path, exc)
        return []


def get_run_detail(db_path: str | None, run_id: str) -> RunDetail | None:
    """Fetch RunDetail from DB. Returns None when run_id not found."""
    if not db_path:
        return None
    p = Path(db_path)
    if not p.exists():
        return None
    try:
        ResultsDB = _try_import_results_db()
        with ResultsDB(db_path=str(p)) as db:
            runs = {r.run_id: r for r in db.get_runs()}
            if run_id not in runs:
                return None
            results = db.get_results_for_run(run_id)
            meta = runs[run_id]
        entries = [
            TestEntry(
                name=r.test_name,
                domain=r.domain,
                status=r.outcome,
                duration_s=r.duration_s,
            )
            for r in results
        ]
        return RunDetail(
            run_id=run_id,
            timestamp=meta.timestamp,
            duration_s=0.0,
            git_sha=meta.git_sha,
            tests=entries,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB run detail error (%s, %s): %s", db_path, run_id, exc)
        return None


# ---------------------------------------------------------------------------
# Testbed reader
# ---------------------------------------------------------------------------


def get_testbed_status(testbed_path: str | None) -> TestbedStatus:
    """Read testbed.yaml and return status model. Returns 'missing' status on error."""
    if not testbed_path:
        return TestbedStatus(dut="unknown", hal_devices=[], services=[], source="missing")
    p = Path(testbed_path)
    if not p.exists():
        return TestbedStatus(dut="unknown", hal_devices=[], services=[], source="missing")
    try:
        import yaml  # noqa: PLC0415

        raw = yaml.safe_load(p.read_text())
        dut = raw.get("id", "unknown")
        hal: list[DeviceStatus] = []
        for dev in raw.get("wiring_map", {}).get("links", []):
            hal.append(DeviceStatus(name=str(dev.get("switch", "?")), type="switch", connected=True))
        services = list(raw.get("services", {}).keys()) if raw.get("services") else []
        return TestbedStatus(dut=dut, hal_devices=hal, services=services, source="sim")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Testbed YAML read error (%s): %s", testbed_path, exc)
        return TestbedStatus(dut="unknown", hal_devices=[], services=[], source="missing")


# ---------------------------------------------------------------------------
# Combined loader — main source of truth for results_path
# ---------------------------------------------------------------------------


def load_results(results_path: str) -> tuple[list[TestEntry], list[RunSummary]]:
    """Load TestEntry list from JUnit XML + run summaries placeholder.

    The run summaries from XML are synthesized from the single-run content.
    DB summaries are merged by the caller if db_path is provided.
    """
    entries = parse_junit(results_path)
    summaries: list[RunSummary] = []
    if entries:
        passed = sum(1 for e in entries if e.status == "passed")
        failed = sum(1 for e in entries if e.status == "failed")
        skipped = sum(1 for e in entries if e.status == "skipped")
        error = sum(1 for e in entries if e.status == "error")
        duration = sum(e.duration_s for e in entries)
        summaries.append(
            RunSummary(
                run_id="xml-import",
                timestamp=time.time(),
                duration_s=duration,
                passed=passed,
                failed=failed,
                skipped=skipped,
                error=error,
                total=len(entries),
                git_sha="",
            )
        )
    return entries, summaries
