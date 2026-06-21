"""Data aggregation layer: JUnit-XML parser + ResultsDB reader."""
from __future__ import annotations

import html as _html
import logging
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as _defused_ET

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
        tree = _defused_ET.parse(str(p))
        root = tree.getroot()
    except ET.ParseError as exc:
        logger.warning("JUnit XML parse error (%s): %s — returning empty list", p, exc)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("JUnit XML blocked/parse error (%s): %s — returning empty list", p, exc)
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
# Filter / Sort helpers (AC-34)
# ---------------------------------------------------------------------------

_VALID_STATUSES = frozenset({"passed", "failed", "skipped", "error"})
_VALID_SORT_FIELDS = frozenset({"time", "duration", "status"})


def filter_runs(
    runs: list[RunSummary],
    q: str | None = None,
) -> list[RunSummary]:
    """Filter run summaries by free-text query (run_id / git_sha)."""
    if not q:
        return list(runs)
    q_lower = q.lower()
    return [
        r for r in runs
        if q_lower in r.run_id.lower() or q_lower in (r.git_sha or "").lower()
    ]


def sort_runs(
    runs: list[RunSummary],
    sort: str | None = None,
) -> list[RunSummary]:
    """Sort run summaries. Prefix '-' for descending. Ignores unknown keys."""
    if not sort:
        return list(runs)
    desc = sort.startswith("-")
    key = sort.lstrip("-")
    if key not in _VALID_SORT_FIELDS:
        return list(runs)
    if key == "time":
        return sorted(runs, key=lambda r: r.timestamp, reverse=desc)
    if key == "duration":
        return sorted(runs, key=lambda r: r.duration_s, reverse=desc)
    if key == "status":
        # Status sort: rank by failed > error > skipped > passed
        _rank = {"failed": 0, "error": 1, "skipped": 2, "passed": 3}

        def _status_key(r: RunSummary) -> int:
            if r.failed:
                return _rank["failed"]
            if r.error:
                return _rank["error"]
            if r.skipped:
                return _rank["skipped"]
            return _rank["passed"]

        return sorted(runs, key=_status_key, reverse=desc)
    return list(runs)


def filter_entries(
    entries: list[TestEntry],
    status: str | None = None,
    domain: str | None = None,
    q: str | None = None,
) -> list[TestEntry]:
    """Filter test entries by status, domain and/or free-text query."""
    result = entries
    if status and status in _VALID_STATUSES:
        result = [e for e in result if e.status == status]
    if domain:
        d_lower = domain.lower()
        result = [e for e in result if e.domain.lower() == d_lower]
    if q:
        q_lower = q.lower()
        result = [e for e in result if q_lower in e.name.lower() or q_lower in e.domain.lower()]
    return result


# ---------------------------------------------------------------------------
# Export helpers (AC-35)
# ---------------------------------------------------------------------------


def run_junit_bytes(run_detail: RunDetail) -> bytes:
    """Render a RunDetail as minimal JUnit XML bytes."""
    import xml.etree.ElementTree as ET  # noqa: PLC0415

    root = ET.Element(
        "testsuite",
        name=run_detail.run_id,
        tests=str(len(run_detail.tests)),
        timestamp=str(run_detail.timestamp),
    )
    for t in run_detail.tests:
        tc = ET.SubElement(root, "testcase", name=t.name, classname=t.domain, time=str(t.duration_s))
        if t.status == "failed":
            fail_el = ET.SubElement(tc, "failure")
            fail_el.set("message", t.message or "")
            fail_el.text = t.stacktrace or ""
        elif t.status == "error":
            err_el = ET.SubElement(tc, "error")
            err_el.set("message", t.message or "")
            err_el.text = t.stacktrace or ""
        elif t.status == "skipped":
            ET.SubElement(tc, "skipped")
    return ET.tostring(root, encoding="unicode").encode("utf-8")


def render_run_html(run_detail: RunDetail) -> str:
    """Render a RunDetail as a minimal standalone HTML report (XSS-safe via html.escape)."""
    from datetime import datetime  # noqa: PLC0415

    ts_str = datetime.utcfromtimestamp(run_detail.timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
    safe_run_id = _html.escape(run_detail.run_id)
    safe_git_sha = _html.escape(run_detail.git_sha or "")
    rows = []
    for t in run_detail.tests:
        color = {"passed": "#4ade80", "failed": "#f87171", "skipped": "#fbbf24", "error": "#fb923c"}.get(
            t.status, "#94a3b8"
        )
        safe_status = _html.escape(t.status)
        safe_name = _html.escape(t.name)
        safe_domain = _html.escape(t.domain)
        msg = ""
        if t.message:
            safe_msg = _html.escape(t.message[:200])
            msg = f"<br><small style='color:#94a3b8'>{safe_msg}</small>"
        rows.append(
            f"<tr><td style='color:{color}'>{safe_status}</td>"
            f"<td>{safe_name}{msg}</td>"
            f"<td>{safe_domain}</td>"
            f"<td>{t.duration_s:.3f}s</td></tr>"
        )
    rows_html = "\n".join(rows) if rows else "<tr><td colspan='4'>No tests</td></tr>"
    passed = sum(1 for t in run_detail.tests if t.status == "passed")
    failed = sum(1 for t in run_detail.tests if t.status == "failed")
    sha_display = safe_git_sha or "—"
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Run {safe_run_id}</title>
<style>body{{font-family:system-ui;background:#0f172a;color:#e2e8f0;padding:2rem}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:.5rem .75rem;border-bottom:1px solid #334155;text-align:left}}
th{{color:#64748b;text-transform:uppercase;font-size:.8rem}}</style></head>
<body>
<h1>Run {safe_run_id}</h1>
<p>{ts_str} &nbsp;|&nbsp; {passed} passed &nbsp;|&nbsp; {failed} failed &nbsp;|&nbsp; SHA: {sha_display}</p>
<table>
<thead><tr><th>Status</th><th>Test</th><th>Domain</th><th>Duration</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""


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
