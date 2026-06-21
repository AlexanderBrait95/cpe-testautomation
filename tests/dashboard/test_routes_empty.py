"""Tests for dashboard routes with empty state (T-D06, AC-26)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app

pytestmark = pytest.mark.headless


@pytest.fixture()
def empty_client(tmp_path):
    """Client with no XML file and no DB."""
    app = create_app(results_path=str(tmp_path / "missing.xml"), db_path=None)
    return TestClient(app)


def test_overview_empty_200(empty_client):
    r = empty_client.get("/api/overview")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 0
    assert d["passed"] == 0
    assert d["last_run"] is None


def test_domains_empty_200(empty_client):
    r = empty_client.get("/api/domains")
    assert r.status_code == 200
    assert r.json() == []


def test_runs_empty_200(empty_client):
    r = empty_client.get("/api/runs")
    assert r.status_code == 200
    assert r.json() == []


def test_testbed_empty_200(empty_client):
    r = empty_client.get("/api/testbed")
    assert r.status_code == 200
    d = r.json()
    assert d["source"] == "missing"


def test_progress_idle_200(empty_client):
    r = empty_client.get("/api/runs/active/progress")
    assert r.status_code == 200
    assert r.json()["status"] == "idle"
