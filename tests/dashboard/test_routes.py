"""Tests for FastAPI routes with real JUnit XML (T-D06, AC-24, AC-25)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app

pytestmark = pytest.mark.headless

MINI_XML = str(Path(__file__).parent / "fixtures" / "mini.xml")

# Stabile Fixture für AC-25 — nie von make verify überschrieben
SAMPLE_XML = str(Path(__file__).parent / "fixtures" / "sample-results.xml")

# Soll-Werte aus sample-results.xml (Kommentar-Header in der Fixture)
EXPECTED_TOTAL = 10
EXPECTED_PASSED = 6
EXPECTED_FAILED = 1
EXPECTED_SKIPPED = 2
EXPECTED_ERROR = 1


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
# AC-25: stabile Fixture — Zähler korrekt + Domain-Aggregation
# ---------------------------------------------------------------------------


def test_overview_real_xml_counts():
    """AC-25: Overview-Zähler aus stabiler Fixture; Domain-Aggregation mitgeprüft."""
    app = create_app(results_path=SAMPLE_XML)
    tc = TestClient(app)

    r = tc.get("/api/overview")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == EXPECTED_TOTAL
    assert d["passed"] == EXPECTED_PASSED
    assert d["failed"] == EXPECTED_FAILED
    assert d["skipped"] == EXPECTED_SKIPPED
    assert d["error"] == EXPECTED_ERROR

    # Domain-Aggregation: 3 Domains erwartet (lan, wan, wifi)
    r2 = tc.get("/api/domains")
    assert r2.status_code == 200
    domains = {item["name"]: item for item in r2.json()}
    assert set(domains.keys()) == {"lan", "wan", "wifi"}
    assert domains["lan"]["passed"] == 2
    assert domains["lan"]["failed"] == 1
    assert domains["wan"]["skipped"] == 1
    assert domains["wifi"]["error"] == 1


# ---------------------------------------------------------------------------
# Unknown run_id → 404
# ---------------------------------------------------------------------------


def test_unknown_run_id_404(client):
    r = client.get("/api/runs/nonexistent-run-id-xyz")
    assert r.status_code == 404
