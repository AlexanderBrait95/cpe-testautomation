"""Background subprocess runner for dashboard-triggered test runs."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from cpe_ta.dashboard.models import RunProgress

# Whitelist for marker expressions — no shell metacharacters allowed.
_MARKER_RE = re.compile(r"^[a-zA-Z0-9_ ()\-andort]+$")

CommandFactory = Callable[[str, str], list[str]]


def _default_command_factory(markers: str, output_xml: str) -> list[str]:
    return [sys.executable, "-m", "pytest", "-m", markers, f"--junitxml={output_xml}"]


def validate_marker(markers: str) -> None:
    """Raise ValueError when markers contain disallowed characters."""
    if not _MARKER_RE.match(markers):
        raise ValueError(f"Invalid marker expression: {markers!r}")


class DashboardRunner:
    """Manages a single background pytest subprocess."""

    def __init__(self, command_factory: CommandFactory | None = None) -> None:
        self._factory: CommandFactory = command_factory or _default_command_factory
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._run_id: str | None = None
        self._started: float | None = None
        self._output_xml: str | None = None
        self._tmp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._lines: list[str] = []
        self._status: str = "idle"
        self._counts: dict[str, int] = {}
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, markers: str) -> str:
        """Start a run. Returns run_id. Raises RuntimeError when busy."""
        validate_marker(markers)
        with self._lock:
            if self._status == "running":
                raise RuntimeError("busy")
            tmp = tempfile.TemporaryDirectory()
            self._tmp_dir = tmp
            xml_path = str(Path(tmp.name) / "results.xml")
            cmd: list[str] = self._factory(markers, xml_path)
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False,
            )
            import uuid  # noqa: PLC0415

            self._run_id = str(uuid.uuid4())[:8]
            self._started = time.monotonic()
            self._output_xml = xml_path
            self._lines = []
            self._status = "running"
            self._counts = {}
            t = threading.Thread(target=self._monitor, daemon=True)
            self._thread = t
            t.start()
        return self._run_id

    def progress(self) -> RunProgress:
        with self._lock:
            return RunProgress(
                status=self._status,
                run_id=self._run_id,
                started=self._started,
                lines_tail=self._lines[-20:],
                counts=dict(self._counts),
            )

    def result_xml(self) -> str | None:
        """Return path to JUnit XML once finished, else None."""
        with self._lock:
            if self._status in ("finished", "failed"):
                return self._output_xml
            return None

    def is_busy(self) -> bool:
        with self._lock:
            return self._status == "running"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _monitor(self) -> None:
        proc = self._process
        if proc is None:
            return
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            with self._lock:
                self._lines.append(line)
                self._update_counts(line)
        proc.wait()
        with self._lock:
            self._status = "finished" if proc.returncode == 0 else "failed"
            if self._tmp_dir and proc.returncode != 0:
                # Keep tmp dir for inspection; it's cleaned eventually by GC.
                pass

    def _update_counts(self, line: str) -> None:
        # Naively parse pytest summary lines like "3 passed, 1 failed"
        for keyword in ("passed", "failed", "error", "skipped"):
            m = re.search(rf"(\d+) {keyword}", line)
            if m:
                self._counts[keyword] = int(m.group(1))

    def get_run_id(self) -> str | None:
        with self._lock:
            return self._run_id


# ---------------------------------------------------------------------------
# Singleton per app instance (injected via app.py dependency)
# ---------------------------------------------------------------------------

_SENTINEL: dict[str, Any] = {}
