"""T36 — CLI command tests.

Uses Click's CliRunner — no subprocess or real I/O required.
All tests are headless.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from cpe_ta.cli import app

PROJECT_ROOT = __file__[: __file__.rfind("/tests/")]


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def example_yaml() -> str:
    return f"{PROJECT_ROOT}/testbed.example.yaml"


# ---------------------------------------------------------------------------
# --help
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_help(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "CPE Test-Automation" in result.output


# ---------------------------------------------------------------------------
# inventory-validate
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_inventory_validate_ok(runner: CliRunner, example_yaml: str) -> None:
    """Valid testbed.example.yaml must exit 0."""
    result = runner.invoke(app, ["inventory-validate", example_yaml])
    assert result.exit_code == 0


@pytest.mark.headless
def test_inventory_validate_bad(runner: CliRunner) -> None:
    """Non-existent file must exit non-zero."""
    result = runner.invoke(app, ["inventory-validate", "/nonexistent/testbed.yaml"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# run --help  (full run would execute pytest — --help is safe)
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_run_smoke_headless(runner: CliRunner) -> None:
    """cpe-ta run --help must exit 0."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "markers" in result.output.lower() or "marker" in result.output.lower()


# ---------------------------------------------------------------------------
# list --help
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_list(runner: CliRunner) -> None:
    """cpe-ta list --help must exit 0."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# db-migrate
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_db_migrate(runner: CliRunner) -> None:
    """cpe-ta db-migrate must create the schema and exit 0."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    result = runner.invoke(app, ["db-migrate", "--db", db_path])
    assert result.exit_code == 0, result.output
    assert "OK" in result.output


# ---------------------------------------------------------------------------
# report --help
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_report_help(runner: CliRunner) -> None:
    """cpe-ta report --help must exit 0 and mention --input/--output."""
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output" in result.output
