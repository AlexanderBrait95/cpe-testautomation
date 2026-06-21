"""Tests for Run-Start flow + security (T-D07, AC-27, AC-28)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import DEFAULT_HOST, create_app
from cpe_ta.dashboard.runner import DashboardRunner

pytestmark = pytest.mark.headless

MINI_XML = str(Path(__file__).parent / "fixtures" / "mini.xml")


def _fake_runner_factory(mini_xml: str):
    """Returns a DashboardRunner that immediately writes a mini JUnit XML."""

    def factory(markers: str, xml_path: str) -> list[str]:
        return [
            sys.executable,
            "-c",
            (
                f"content = open(r'{mini_xml}').read(); "
                f"open(r'{xml_path}', 'w').write(content)"
            ),
        ]

    return DashboardRunner(command_factory=factory)


def _wait_for_finished(runner: DashboardRunner, timeout: float = 5.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = runner.progress().status
        if status != "running":
            return status
        time.sleep(0.05)
    return "timeout"


# ---------------------------------------------------------------------------
# AC-27: run lifecycle through API
# ---------------------------------------------------------------------------


def test_start_run_returns_run_id():
    runner = _fake_runner_factory(MINI_XML)
    app = create_app(results_path=MINI_XML, runner=runner)
    client = TestClient(app)
    r = client.post("/api/runs", json={"markers": "headless"})
    assert r.status_code == 202
    d = r.json()
    assert "run_id" in d
    assert d["status"] == "running"


def test_progress_transitions_to_finished():
    runner = _fake_runner_factory(MINI_XML)
    app = create_app(results_path=MINI_XML, runner=runner)
    client = TestClient(app)
    client.post("/api/runs", json={"markers": "headless"})
    final_status = _wait_for_finished(runner)
    assert final_status == "finished"

    r = client.get("/api/runs/active/progress")
    assert r.status_code == 200
    assert r.json()["status"] == "finished"


def test_second_start_returns_409():

    def slow_factory(markers: str, xml_path: str) -> list[str]:
        return [sys.executable, "-c", "import time; time.sleep(3)"]

    runner = DashboardRunner(command_factory=slow_factory)
    app = create_app(results_path=MINI_XML, runner=runner)
    client = TestClient(app)
    r1 = client.post("/api/runs", json={"markers": "headless"})
    assert r1.status_code == 202
    r2 = client.post("/api/runs", json={"markers": "smoke"})
    assert r2.status_code == 409
    # Cleanup
    if runner._process:
        runner._process.terminate()


# ---------------------------------------------------------------------------
# AC-28: security — bad marker → 422, no subprocess
# ---------------------------------------------------------------------------


def test_invalid_marker_returns_4xx():
    called: list[bool] = []

    def factory(markers: str, xml_path: str) -> list[str]:
        called.append(True)
        return [sys.executable, "-c", "pass"]

    runner = DashboardRunner(command_factory=factory)
    app = create_app(results_path=MINI_XML, runner=runner)
    client = TestClient(app)
    r = client.post("/api/runs", json={"markers": "headless; rm -rf /"})
    assert r.status_code in (422, 400)
    assert called == []


def test_shell_injection_no_subprocess():
    called: list[bool] = []

    def factory(markers: str, xml_path: str) -> list[str]:
        called.append(True)
        return [sys.executable, "-c", "pass"]

    runner = DashboardRunner(command_factory=factory)
    app = create_app(results_path=MINI_XML, runner=runner)
    client = TestClient(app)
    r = client.post("/api/runs", json={"markers": "$(whoami)"})
    assert r.status_code in (422, 400)
    assert called == []


# ---------------------------------------------------------------------------
# AC-28: default host is 127.0.0.1
# ---------------------------------------------------------------------------


def test_default_host_is_loopback():
    assert DEFAULT_HOST == "127.0.0.1"
