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


# ---------------------------------------------------------------------------
# AC-47: XSS prevention in HTML export (TS-02)
# ---------------------------------------------------------------------------

def _make_xss_xml(tmp_path: Path) -> str:
    """Write a JUnit XML with an XSS payload in test name and message."""
    content = '''<?xml version="1.0"?>
<testsuites>
  <testsuite name="xss" tests="1">
    <testcase classname="tests.lan.xss" name="&lt;script&gt;alert(1)&lt;/script&gt;" time="0.1">
      <failure message="&lt;img src=x onerror=alert(2)&gt;">stack</failure>
    </testcase>
  </testsuite>
</testsuites>'''
    p = tmp_path / "xss.xml"
    p.write_text(content)
    return str(p)


def test_export_html_no_raw_script_tag(tmp_path):
    """HTML export must not contain unescaped <script> from test names."""
    xss_xml = _make_xss_xml(tmp_path)
    app = create_app(results_path=xss_xml)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=html")
    assert r.status_code == 200
    body = r.content.decode("utf-8")
    # Raw <script> tag must NOT appear in the output
    assert "<script>" not in body, "Unescaped <script> found — XSS vulnerability"
    # Escaped version must appear
    assert "&lt;script&gt;" in body, "Expected HTML-escaped &lt;script&gt; not found"


def test_export_html_no_raw_img_onerror(tmp_path):
    """HTML export must not contain unescaped <img onerror= from failure messages."""
    xss_xml = _make_xss_xml(tmp_path)
    app = create_app(results_path=xss_xml)
    client = TestClient(app)
    run_id = _get_any_run_id(client)
    r = client.get(f"/api/runs/{run_id}/export?format=html")
    assert r.status_code == 200
    body = r.content.decode("utf-8")
    assert "<img" not in body.lower() or "onerror" not in body.lower(), \
        "Unescaped <img onerror= found in HTML export — XSS vulnerability"
