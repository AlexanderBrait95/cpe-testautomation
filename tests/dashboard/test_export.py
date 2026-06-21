"""Tests for GET /api/runs/{id}/export (AC-35, TB-03)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app

pytestmark = pytest.mark.headless

SAMPLE_XML = str(Path(__file__).parent / "fixtures" / "sample-results.xml")


def _get_any_run_id(client: TestClient) -> str:
    runs = client.get("/api/runs").json()
    assert runs, "Need at least one run for export tests"
    return runs[0]["run_id"]


# ---------------------------------------------------------------------------
# JUnit XML export
# ---------------------------------------------------------------------------

def test_export_junit_200_and_content_type():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=junit")
    assert r.status_code == 200
    assert "application/xml" in r.headers["content-type"]


def test_export_junit_content_disposition():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=junit")
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".xml" in cd


def test_export_junit_body_is_xml():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=junit")
    assert r.status_code == 200
    body = r.content.decode("utf-8")
    assert "<testsuite" in body


# ---------------------------------------------------------------------------
# HTML export
# ---------------------------------------------------------------------------

def test_export_html_200_and_content_type():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_export_html_content_disposition():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=html")
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".html" in cd


def test_export_html_body_is_html():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=html")
    body = r.content.decode("utf-8")
    assert "<!DOCTYPE html" in body or "<html" in body


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_export_unknown_run_id_returns_404():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    r = client.get("/api/runs/no-such-run-id/export?format=junit")
    assert r.status_code == 404


def test_export_unknown_format_returns_422():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=pdf")
    assert r.status_code == 422


def test_export_default_format_is_junit():
    app = create_app(results_path=SAMPLE_XML)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    # No ?format= → default is junit
    r = client.get(f"/api/runs/{run_id}/export")
    assert r.status_code == 200
    assert "application/xml" in r.headers["content-type"]
