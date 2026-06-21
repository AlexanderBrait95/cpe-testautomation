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


# ---------------------------------------------------------------------------
# TV-05: validate_marker — trailing newline must be rejected (\A...\Z regex)
# ---------------------------------------------------------------------------


def test_trailing_newline_marker_rejected():
    """TV-05: 'smoke\\n' must be rejected — $ matches before \\n, \\Z does not."""
    with pytest.raises(ValueError):
        validate_marker("smoke\n")


def test_trailing_newline_multiline_still_rejected():
    """Multiline payload with newline must be rejected."""
    with pytest.raises(ValueError):
        validate_marker("smoke\ninjected")


# ---------------------------------------------------------------------------
# TV-04: validate_marker — whitespace-only markers rejected
# ---------------------------------------------------------------------------


def test_whitespace_only_marker_rejected():
    """TV-04: '   ' (whitespace-only) must be rejected, not start the full suite."""
    with pytest.raises(ValueError):
        validate_marker("   ")


def test_empty_marker_rejected():
    """TV-04: empty string must be rejected."""
    with pytest.raises(ValueError):
        validate_marker("")


# ---------------------------------------------------------------------------
# TV-03: Cancel/Start race — epoch guard prevents old monitor overwrite
# ---------------------------------------------------------------------------


def test_cancel_start_race_new_run_stays_running():
    """TV-03: cancel() immediately followed by start() must leave new run running."""
    def blocking_factory(markers: str, xml_path: str) -> list[str]:
        # Blocks until cancel_event is set, then exits
        return [
            sys.executable,
            "-c",
            "import time; time.sleep(5)",
        ]

    runner = DashboardRunner(command_factory=blocking_factory)

    # Start first run (slow)
    runner.start("smoke")
    assert runner.progress().status == "running"

    # Cancel immediately, then start a new quick run
    runner.cancel()

    xml_holder: list[str] = []

    def quick_factory(markers: str, xml_path: str) -> list[str]:
        xml_holder.append(xml_path)
        return [sys.executable, "-c", f"open(r'{xml_path}', 'w').write('<testsuites/>')"]

    runner._factory = quick_factory
    runner.start("headless")

    # The NEW run must be running (not overwritten by old monitor's finalize)
    assert runner.progress().status == "running", (
        "TV-03: old monitor overwrote new run status immediately after cancel+start"
    )

    # Wait for new run to finish
    for _ in range(50):
        if runner.progress().status != "running":
            break
        time.sleep(0.1)

    final_status = runner.progress().status
    assert final_status in ("finished", "failed"), (
        f"TV-03: new run did not complete cleanly, status={final_status}"
    )


def test_old_monitor_does_not_write_to_new_deque():
    """TV-03: old monitor must not append lines to the new run's deque."""
    def slow_output_factory(markers: str, xml_path: str) -> list[str]:
        # Writes many lines slowly so monitor keeps running after cancel
        return [
            sys.executable,
            "-c",
            (
                "import sys, time\n"
                "for i in range(20):\n"
                "    print(f'old-line-{i}', flush=True)\n"
                "    time.sleep(0.05)\n"
            ),
        ]

    runner = DashboardRunner(command_factory=slow_output_factory)
    runner.start("smoke")
    time.sleep(0.05)  # let old monitor start reading

    # Cancel and immediately start a new idle run
    runner.cancel()

    new_lines_before: list[str] = []

    def instant_factory(markers: str, xml_path: str) -> list[str]:
        new_lines_before.extend(list(runner._lines))  # snapshot new deque contents
        return [sys.executable, "-c", f"open(r'{xml_path}', 'w').write('<testsuites/>')"]

    runner._factory = instant_factory
    runner.start("headless")
    time.sleep(0.3)  # allow old monitor to finish (max 20*50ms = 1s)

    new_deque_contents = list(runner._lines)
    stale = [line for line in new_deque_contents if line.startswith("old-line-")]
    assert not stale, (
        f"TV-03: old monitor wrote {len(stale)} stale lines into new deque: {stale[:5]}"
    )
