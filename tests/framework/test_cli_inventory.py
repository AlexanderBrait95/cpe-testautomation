"""Tests for the 'inventory-validate' CLI command.

Uses Click's CliRunner so no subprocess or real I/O is needed.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from cpe_ta.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def example_yaml() -> Path:
    return Path(__file__).parents[2] / "testbed.example.yaml"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestInventoryValidateOk:
    def test_example_yaml_exits_zero(self, runner: CliRunner, example_yaml: Path) -> None:
        result = runner.invoke(app, ["inventory-validate", str(example_yaml)])
        assert result.exit_code == 0, result.output

    def test_valid_yaml_prints_ok(self, runner: CliRunner, example_yaml: Path) -> None:
        result = runner.invoke(app, ["inventory-validate", str(example_yaml)])
        assert "OK" in result.output

    def test_valid_yaml_shows_testbed_id(self, runner: CliRunner, example_yaml: Path) -> None:
        result = runner.invoke(app, ["inventory-validate", str(example_yaml)])
        assert "lab-testbed-01" in result.output

    def test_minimal_valid_yaml(self, runner: CliRunner, tmp_path: Path) -> None:
        minimal = tmp_path / "min.yaml"
        minimal.write_text('id: "minimal-tb"\n', encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(minimal)])
        assert result.exit_code == 0

    def test_full_valid_yaml(self, runner: CliRunner, tmp_path: Path) -> None:
        content = textwrap.dedent("""\
            id: "tb-full"
            switches:
              - switch_id: "sw1"
                host: "10.0.0.1"
                protocol: "snmp"
            pdus:
              - pdu_id: "pdu1"
                host: "10.0.0.2"
                protocol: "http"
            duts:
              - dut_id: "dut1"
                model: "X500"
                vendor: "Acme"
            wiring_map:
              entries:
                - role: "DUT-LAN-1"
                  port: {switch_id: "sw1", port_id: "gi0/1"}
                - role: "DUT-WAN"
                  port: {switch_id: "sw1", port_id: "gi0/2"}
        """)
        valid = tmp_path / "valid.yaml"
        valid.write_text(content, encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(valid)])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Error paths — must exit non-zero with clear message, no traceback
# ---------------------------------------------------------------------------


class TestInventoryValidateErrors:
    def test_duplicate_port_exits_nonzero(self, runner: CliRunner, tmp_path: Path) -> None:
        content = textwrap.dedent("""\
            id: "tb-dup"
            wiring_map:
              entries:
                - role: "DUT-LAN-1"
                  port: {switch_id: "sw1", port_id: "gi0/1"}
                - role: "DUT-WAN"
                  port: {switch_id: "sw1", port_id: "gi0/1"}
        """)
        bad = tmp_path / "dup.yaml"
        bad.write_text(content, encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(bad)])
        assert result.exit_code != 0

    def test_duplicate_port_shows_error_message(self, runner: CliRunner, tmp_path: Path) -> None:
        content = textwrap.dedent("""\
            id: "tb-dup"
            wiring_map:
              entries:
                - role: "DUT-LAN-1"
                  port: {switch_id: "sw1", port_id: "gi0/1"}
                - role: "DUT-WAN"
                  port: {switch_id: "sw1", port_id: "gi0/1"}
        """)
        bad = tmp_path / "dup.yaml"
        bad.write_text(content, encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(bad)])
        output = result.output + (result.stderr if hasattr(result, "stderr") else "")
        # The error should mention something descriptive — no raw traceback
        assert "Traceback" not in output
        assert result.exit_code != 0

    def test_missing_id_field_exits_nonzero(self, runner: CliRunner, tmp_path: Path) -> None:
        content = "switches: []\n"
        bad = tmp_path / "noid.yaml"
        bad.write_text(content, encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(bad)])
        assert result.exit_code != 0

    def test_invalid_yaml_syntax_exits_nonzero(self, runner: CliRunner, tmp_path: Path) -> None:
        bad = tmp_path / "broken.yaml"
        bad.write_text(": broken: [\n", encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(bad)])
        assert result.exit_code != 0

    def test_invalid_yaml_no_traceback(self, runner: CliRunner, tmp_path: Path) -> None:
        bad = tmp_path / "broken.yaml"
        bad.write_text(": broken: [\n", encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(bad)])
        assert "Traceback" not in result.output

    def test_nonexistent_file_click_error(self, runner: CliRunner) -> None:
        """Click's Path(exists=True) should catch missing files."""
        result = runner.invoke(app, ["inventory-validate", "/nonexistent/testbed.yaml"])
        assert result.exit_code != 0

    def test_invalid_switch_protocol_exits_nonzero(self, runner: CliRunner, tmp_path: Path) -> None:
        content = textwrap.dedent("""\
            id: "tb-bad-proto"
            switches:
              - switch_id: "sw1"
                host: "10.0.0.1"
                protocol: "telnet"
        """)
        bad = tmp_path / "badproto.yaml"
        bad.write_text(content, encoding="utf-8")
        result = runner.invoke(app, ["inventory-validate", str(bad)])
        assert result.exit_code != 0
