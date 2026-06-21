"""Tests for FastAPI routes with real JUnit XML (T-D06, AC-24, AC-25)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app

pytestmark = pytest.mark.headless

REAL_XML = str(Path(__file__).parent.parent.parent / "test-results.xml")
MINI_XML = str(Path(__file__).parent / "fixtures" / "mini.xml")


@pytest.fixture()
def client():
    app = create_app(results_path=MINI_XML)
    return TestClient(app)


# ---------------------------------------------------------------------------
# All 6 routes → 200 + valid schema
# ---------------------------------------------------------------------------


def test_overview_200(client):
    r = client.get("/api/overview")
    assert r.status_code == 200
    d = r.json()
    assert "passed" in d
    assert "failed" in d
    assert "skipped" in d
    assert "error" in d
    assert "total" in d
    assert "domains" in d


def test_domains_200(client):
    r = client.get("/api/domains")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    if items:
        assert "name" in items[0]
        assert "pass_rate" in items[0]


def test_runs_200(client):
    r = client.get("/api/runs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_progress_200(client):
    r = client.get("/api/runs/active/progress")
    assert r.status_code == 200
    d = r.json()
    assert "status" in d


def test_testbed_200(client):
    r = client.get("/api/testbed")
    assert r.status_code == 200
    d = r.json()
    assert "dut" in d
    assert "source" in d


def test_post_runs_endpoint_exists(client):
    """POST /api/runs endpoint must exist (route registered)."""
    r = client.post("/api/runs", json={"markers": "headless"})
    # May be 202 (started) or 409 (busy) — route must exist
    assert r.status_code in (202, 409)


# ---------------------------------------------------------------------------
# AC-25: real test-results.xml — counters correct
# ---------------------------------------------------------------------------


def test_overview_real_xml_counts():
    if not Path(REAL_XML).exists():
        pytest.skip("test-results.xml not found")
    app = create_app(results_path=REAL_XML)
    client = TestClient(app)
    r = client.get("/api/overview")
    assert r.status_code == 200
    d = r.json()
    # 559 tests, all passed per the existing run
    assert d["total"] == 559
    assert d["passed"] == 559
    assert d["failed"] == 0


# ---------------------------------------------------------------------------
# Unknown run_id → 404
# ---------------------------------------------------------------------------


def test_unknown_run_id_404(client):
    r = client.get("/api/runs/nonexistent-run-id-xyz")
    assert r.status_code == 404
