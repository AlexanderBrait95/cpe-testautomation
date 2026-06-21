"""CLI entry-point for the CPE Test-Automation framework.

Entry-point: cpe-ta (configured in pyproject.toml)
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from cpe_ta.core.config import ConfigError, load_testbed
from cpe_ta.core.inventory import validate_wiring_map


@click.group()
@click.version_option(package_name="cpe-ta")
def app() -> None:
    """CPE Test-Automation Framework CLI."""


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


@app.command("run")
@click.option("-m", "--markers", default="headless", show_default=True, help="pytest marker expression")
@click.option("--testbed", "testbed_path", default="testbed.yaml", show_default=True, help="Testbed YAML file")
@click.option("-n", "--workers", default="auto", show_default=True, help="Number of parallel workers (xdist -n)")
@click.option("--junitxml", "junit_path", default="test-results.xml", show_default=True, help="JUnit XML output path")
@click.option("--cov/--no-cov", default=False, help="Enable coverage measurement")
def run_cmd(markers: str, testbed_path: str, workers: str, junit_path: str, cov: bool) -> None:
    """Run test-suite against testbed (real or simulator)."""
    import subprocess

    testbed_file = Path(testbed_path)
    if not testbed_file.exists():
        click.echo(f"ERROR: Testbed file not found: {testbed_path}", err=True)
        sys.exit(1)

    # Validate testbed before running tests
    try:
        load_testbed(str(testbed_file))
    except ConfigError as exc:
        click.echo(f"ERROR: Invalid testbed: {exc}", err=True)
        sys.exit(1)

    cmd: list[str] = [
        sys.executable,
        "-m",
        "pytest",
        "-m",
        markers,
        "-n",
        workers,
        f"--junitxml={junit_path}",
    ]
    if cov:
        cmd += ["--cov=cpe_ta", "--cov-report=term"]

    click.echo(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@app.command("list")
@click.option("-m", "--markers", default="", help="Filter by marker expression")
def list_cmd(markers: str) -> None:
    """List available tests (stub — uses pytest --collect-only)."""
    import subprocess

    cmd: list[str] = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    if markers:
        cmd += ["-m", markers]
    result = subprocess.run(cmd, check=False)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# inventory-validate
# ---------------------------------------------------------------------------


@app.command("inventory-validate")
@click.argument("testbed_yaml", type=click.Path(exists=True, dir_okay=False))
def inventory_validate_cmd(testbed_yaml: str) -> None:
    """Validate a testbed YAML inventory file.

    Exits 0 when the inventory is valid, non-zero on any error.
    No Python tracebacks are shown to the user.
    """
    try:
        testbed = load_testbed(testbed_yaml)
    except ConfigError as exc:
        click.echo(f"INVALID: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"INVALID: Unexpected error — {exc}", err=True)
        sys.exit(2)

    # Additional wiring validation
    errors = validate_wiring_map(testbed.wiring_map)
    if errors:
        for err in errors:
            click.echo(f"WIRING ERROR: {err}", err=True)
        sys.exit(1)

    click.echo(f"OK: {testbed_yaml} is valid (testbed id={testbed.id!r})")
    sys.exit(0)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


@app.command("report")
@click.option("--input", "input_path", default=None, help="JUnit XML input file (generates HTML from XML)")
@click.option("--output", "output_path", default=None, help="HTML report output path")
@click.option("--db", "db_path", default="cpe_ta_results.db", show_default=True, help="SQLite results database")
@click.option("--out", "out_dir", default="reports", show_default=True, help="Output directory (used with --db)")
@click.option("--run-id", "run_id", default=None, help="Specific run_id to report (default: latest)")
def report_cmd(
    input_path: str | None,
    output_path: str | None,
    db_path: str,
    out_dir: str,
    run_id: str | None,
) -> None:
    """Generate HTML report from JUnit XML input or from the results database."""
    import time
    import xml.etree.ElementTree as ET

    from cpe_ta.core.results import RunMetadata, TestResult
    from cpe_ta.report.html import write_html_report

    if input_path is not None:
        # Generate HTML from JUnit XML file
        xml_file = Path(input_path)
        if not xml_file.exists():
            click.echo(f"ERROR: Input file not found: {input_path}", err=True)
            sys.exit(1)
        try:
            tree = ET.parse(str(xml_file))
            root = tree.getroot()
        except ET.ParseError as exc:
            click.echo(f"ERROR: Failed to parse JUnit XML: {exc}", err=True)
            sys.exit(1)

        # Build RunMetadata from XML attributes
        run = RunMetadata(
            run_id=root.get("name", "imported-run"),
            dut_id="imported",
            firmware_version=root.get("version", "unknown"),
            timestamp=time.time(),
            git_sha="imported",
            marker_expr="",
            total_tests=int(root.get("tests", "0")),
            passed=0,
            failed=int(root.get("failures", "0")),
            errors=int(root.get("errors", "0")),
            skipped=int(root.get("skipped", "0")),
        )

        results: list[TestResult] = []
        for i, tc in enumerate(root.findall("testcase")):
            if tc.find("failure") is not None:
                outcome = "failed"
            elif tc.find("error") is not None:
                outcome = "error"
            elif tc.find("skipped") is not None:
                outcome = "skipped"
            else:
                outcome = "passed"
            results.append(
                TestResult(
                    test_id=f"imported-{i}",
                    run_id=run.run_id,
                    dut_id="imported",
                    firmware_version=run.firmware_version,
                    timestamp=time.time(),
                    git_sha="imported",
                    domain=tc.get("classname", "unknown"),
                    test_name=tc.get("name", f"test_{i}"),
                    outcome=outcome,
                    duration_s=float(tc.get("time", "0.0")),
                    details={},
                )
            )
        run.passed = sum(1 for r in results if r.outcome == "passed")

        out_file = output_path or "report.html"
        write_html_report(run, results, out_file)
        click.echo(f"OK: HTML report written to {out_file!r}")
        sys.exit(0)

    # Fallback: report from database (original behaviour)
    click.echo(f"[DB] report: db={db_path}, out={out_dir}, run_id={run_id}")
    click.echo("NOTE: Use --input <junit.xml> --output <report.html> for XML-based reporting.")


# ---------------------------------------------------------------------------
# db-migrate
# ---------------------------------------------------------------------------


@app.command("db-migrate")
@click.option("--db", "db_path", default="cpe_ta_results.db", show_default=True, help="SQLite results database")
def db_migrate_cmd(db_path: str) -> None:
    """Apply pending database schema migrations."""
    from cpe_ta.core.results import ResultsDB

    with ResultsDB(db_path=db_path) as db:
        # connect() already calls _migrate(); just confirm success
        _ = db
    click.echo(f"OK: schema migrations applied to {db_path!r}")
    sys.exit(0)


# ---------------------------------------------------------------------------
# dashboard
# ---------------------------------------------------------------------------


_LOOPBACK_HOSTS: frozenset[str] = frozenset({"127.0.0.1", "localhost", "::1"})


@app.command("dashboard")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host (default: loopback)")
@click.option("--port", default=8080, show_default=True, help="Bind port")
@click.option("--results", "results_path", default="test-results.xml", show_default=True, help="JUnit XML results file")
@click.option("--db", "db_path", default=None, help="SQLite results database (optional)")
@click.option("--testbed", "testbed_path", default=None, help="Testbed YAML file (optional)")
def dashboard_cmd(host: str, port: int, results_path: str, db_path: str | None, testbed_path: str | None) -> None:
    """Start the CPE Test-Automation Web-Dashboard."""
    import socket

    try:
        import uvicorn  # noqa: PLC0415

        from cpe_ta.dashboard.app import create_app  # noqa: PLC0415
    except ImportError as exc:
        click.echo(f"ERROR: Dashboard dependencies not installed — {exc}", err=True)
        sys.exit(1)

    if host not in _LOOPBACK_HOSTS:
        click.echo(
            f"WARNING: binding to non-loopback host {host!r} exposes the dashboard to all "
            "network clients — there is no authentication. Use --host 127.0.0.1 for local-only access.",
            err=True,
        )

    # Probe port availability before starting uvicorn (avoids silent hang)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            click.echo(f"ERROR: Port {port} is already in use on {host}. Choose a different port.", err=True)
            sys.exit(1)

    dashboard_app = create_app(results_path=results_path, db_path=db_path, testbed_path=testbed_path)
    click.echo(f"Dashboard running at http://{host}:{port}/ — press Ctrl+C to stop")
    uvicorn.run(dashboard_app, host=host, port=port)


if __name__ == "__main__":
    app()
