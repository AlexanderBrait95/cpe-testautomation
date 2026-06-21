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
