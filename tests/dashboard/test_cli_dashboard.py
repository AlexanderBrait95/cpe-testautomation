"""Tests for CLI 'cpe-ta dashboard' command (T-D08, AC-23)."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from cpe_ta.cli import app

pytestmark = pytest.mark.headless


def test_dashboard_help_shows_command():
    runner = CliRunner()
    result = runner.invoke(app, ["dashboard", "--help"])
    assert result.exit_code == 0
    output = result.output
    assert "dashboard" in output.lower() or "Dashboard" in output


def test_dashboard_help_shows_host_default():
    runner = CliRunner()
    result = runner.invoke(app, ["dashboard", "--help"])
    assert result.exit_code == 0
    assert "127.0.0.1" in result.output


def test_dashboard_help_shows_port_default():
    runner = CliRunner()
    result = runner.invoke(app, ["dashboard", "--help"])
    assert result.exit_code == 0
    assert "8080" in result.output


def test_dashboard_appears_in_main_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "dashboard" in result.output


def test_port_in_use_exits_nonzero(tmp_path):
    """Simulate port-in-use by binding before invoking CLI."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        # Keep socket open so the port appears busy to the next bind attempt
        runner = CliRunner()
        result = runner.invoke(app, ["dashboard", "--port", str(port), "--results", str(tmp_path / "missing.xml")])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# AC-50: Security warning when binding to non-loopback host (TS-05)
# ---------------------------------------------------------------------------


def _loopback_set() -> frozenset[str]:
    from cpe_ta.cli import _LOOPBACK_HOSTS
    return _LOOPBACK_HOSTS


def test_loopback_constant_covers_standard_addresses():
    hosts = _loopback_set()
    assert "127.0.0.1" in hosts
    assert "localhost" in hosts
    assert "::1" in hosts


def test_non_loopback_host_emits_warning(tmp_path):
    """--host 0.0.0.0 must print a security warning before starting."""
    import unittest.mock as mock

    # We mock uvicorn.run so the server doesn't actually start
    with mock.patch("uvicorn.run"):
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["dashboard", "--host", "0.0.0.0", "--port", "19999",
             "--results", str(tmp_path / "missing.xml")],
        )
    output = result.output or ""
    assert "WARNING" in output or "warning" in output.lower(), \
        f"Expected WARNING in output for --host 0.0.0.0, got: {output[:400]}"
    assert "0.0.0.0" in output or "non-loopback" in output, \
        "Warning must mention the non-loopback host"


def test_loopback_host_no_warning(tmp_path):
    """--host 127.0.0.1 (default) must NOT emit a security warning."""
    import unittest.mock as mock

    with mock.patch("uvicorn.run"):
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["dashboard", "--host", "127.0.0.1", "--port", "19998",
             "--results", str(tmp_path / "missing.xml")],
        )
    output = result.output or ""
    assert "WARNING" not in output, \
        f"Unexpected WARNING for loopback host: {output[:400]}"
