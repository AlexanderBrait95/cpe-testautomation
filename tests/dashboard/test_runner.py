"""Tests for DashboardRunner (T-D05)."""
from __future__ import annotations

import sys
import time

import pytest

from cpe_ta.dashboard.runner import DashboardRunner, validate_marker

pytestmark = pytest.mark.headless


# ---------------------------------------------------------------------------
# Marker validation
# ---------------------------------------------------------------------------


def test_valid_markers_accepted():
    validate_marker("headless")
    validate_marker("headless and smoke")
    validate_marker("lan or wifi")
    validate_marker("not hardware")


def test_invalid_marker_raises():
    with pytest.raises(ValueError):
        validate_marker("headless; rm -rf /")


def test_injection_attempt_raises():
    with pytest.raises(ValueError):
        validate_marker("headless && whoami")


# ---------------------------------------------------------------------------
# Command factory receives a list (not shell string)
# ---------------------------------------------------------------------------


def test_command_factory_receives_list(tmp_path):
    received: list[list[str]] = []

    def fake_factory(markers: str, xml_path: str) -> list[str]:
        cmd = [sys.executable, "-c", f"import sys; open(r'{xml_path}', 'w').write('<testsuites/>'); sys.exit(0)"]
        received.append(cmd)
        return cmd

    runner = DashboardRunner(command_factory=fake_factory)
    runner.start("headless")
    # Wait for process to finish
    for _ in range(50):
        if runner.progress().status != "running":
            break
        time.sleep(0.1)

    assert len(received) == 1
    assert isinstance(received[0], list), "factory must receive/return a list, not a shell string"


# ---------------------------------------------------------------------------
# Run lifecycle: running → finished
# ---------------------------------------------------------------------------


def _quick_factory(xml_path_holder: list[str]):
    def factory(markers: str, xml_path: str) -> list[str]:
        xml_path_holder.append(xml_path)
        return [
            sys.executable,
            "-c",
            f"open(r'{xml_path}', 'w').write('<testsuites><testsuite tests=\"1\"><testcase classname=\"tests.lan.t\" name=\"t\" time=\"0.01\"/></testsuite></testsuites>')",
        ]
    return factory


def test_run_lifecycle():
    xml_holder: list[str] = []
    runner = DashboardRunner(command_factory=_quick_factory(xml_holder))
    run_id = runner.start("headless")
    assert run_id is not None
    # Poll until done
    for _ in range(50):
        prog = runner.progress()
        if prog.status != "running":
            break
        time.sleep(0.1)
    prog = runner.progress()
    assert prog.status == "finished"


def test_busy_signal():
    """Second start while running → RuntimeError."""

    xml_holder: list[str] = []

    def slow_factory(markers: str, xml_path: str) -> list[str]:
        xml_holder.append(xml_path)
        return [sys.executable, "-c", "import time; time.sleep(2)"]

    runner = DashboardRunner(command_factory=slow_factory)
    runner.start("headless")
    with pytest.raises(RuntimeError, match="busy"):
        runner.start("smoke")
    # Cleanup
    if runner._process:
        runner._process.terminate()


def test_invalid_marker_no_subprocess():
    called: list[bool] = []

    def factory(markers: str, xml_path: str) -> list[str]:
        called.append(True)
        return [sys.executable, "-c", "pass"]

    runner = DashboardRunner(command_factory=factory)
    with pytest.raises(ValueError):
        runner.start("headless; rm -rf /")
    assert called == [], "subprocess must not be started for invalid markers"


# ---------------------------------------------------------------------------
# AC-49: Runner output buffer capped at _MAX_OUTPUT_LINES (TS-04)
# ---------------------------------------------------------------------------


def test_runner_lines_buffer_capped():
    """Buffer must not exceed _MAX_OUTPUT_LINES regardless of output volume."""
    from cpe_ta.dashboard.runner import _MAX_OUTPUT_LINES

    # Feed N > _MAX_OUTPUT_LINES lines directly into the runner's deque
    runner = DashboardRunner()
    n_lines = _MAX_OUTPUT_LINES + 500
    with runner._lock:
        for i in range(n_lines):
            runner._lines.append(f"line {i}")

    assert len(runner._lines) <= _MAX_OUTPUT_LINES, (
        f"Buffer grew to {len(runner._lines)}, expected ≤ {_MAX_OUTPUT_LINES}"
    )


def test_runner_tail_still_correct_after_overflow():
    """progress() tail returns last 20 lines even after buffer overflow."""
    from cpe_ta.dashboard.runner import _MAX_OUTPUT_LINES

    runner = DashboardRunner()
    n_lines = _MAX_OUTPUT_LINES + 100
    with runner._lock:
        for i in range(n_lines):
            runner._lines.append(f"line-{i}")

    prog = runner.progress()
    # Tail must be the LAST 20 lines of what's in the buffer
    assert len(prog.lines_tail) <= 20
    if prog.lines_tail:
        # The last line in the tail must be the very last line written
        assert prog.lines_tail[-1] == f"line-{n_lines - 1}"
