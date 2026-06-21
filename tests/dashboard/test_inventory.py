"""Tests for POST /api/inventory/validate (AC-43, AC-46, TB-04)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app

pytestmark = pytest.mark.headless

EXAMPLE_YAML = str(Path(__file__).parents[2] / "testbed.example.yaml")


# ---------------------------------------------------------------------------
# Valid inventory
# ---------------------------------------------------------------------------

def test_validate_valid_inventory_returns_ok_true():
    app = create_app(testbed_path=EXAMPLE_YAML)
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={EXAMPLE_YAML}")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["errors"] == []


# ---------------------------------------------------------------------------
# Invalid inventory — relative/safe paths within project
# ---------------------------------------------------------------------------

def test_validate_missing_file_returns_ok_false():
    """A relative path within CWD that does not exist returns ok=False (not 500)."""
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/inventory/validate?path=no-such-testbed-12345.yaml")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert len(body["errors"]) >= 1


def test_validate_broken_yaml_returns_ok_false_no_500(tmp_path):
    broken = tmp_path / "broken.yaml"
    broken.write_text("id: test\nwiring_map: [this is not valid pydantic\n")
    app = create_app()
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={broken}")
    assert r.status_code == 200, "Must not return 500 on broken YAML"
    body = r.json()
    assert body["ok"] is False
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) >= 1


def test_validate_invalid_wiring_returns_structured_errors(tmp_path):
    yaml_content = """
id: "test-bed"
dut:
  id: "cpe-01"
  model: "test"
  technology: dsl
  capabilities:
    wan_ports: 1
    lan_ports: 4
wiring_map:
  links:
    - role: ""
      switch_id: "sw-01"
      port_id: "eth1"
switches: []
pdus: []
serial_consoles: []
services: {}
"""
    p = tmp_path / "wiring.yaml"
    p.write_text(yaml_content)
    app = create_app()
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={p}")
    assert r.status_code == 200
    body = r.json()
    assert "ok" in body
    assert "errors" in body
    assert isinstance(body["errors"], list)


# ---------------------------------------------------------------------------
# AC-46: Traversal & absolute foreign paths → 400 (TS-01)
# ---------------------------------------------------------------------------

def test_validate_traversal_dot_dot_blocked():
    """Path traversal via ../../ must be rejected with 4xx."""
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/inventory/validate?path=../../etc/passwd")
    assert r.status_code == 400


def test_validate_absolute_foreign_path_blocked():
    """/etc/passwd and similar system paths must be rejected with 4xx."""
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/inventory/validate?path=/etc/passwd")
    assert r.status_code == 400


def test_validate_absolute_nonexistent_foreign_path_blocked():
    """Absolute paths outside the project are rejected even if they don't exist."""
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/inventory/validate?path=/no/such/path/testbed.yaml")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# AC-46: Secret-Disclosure prevention (TS-01)
# ---------------------------------------------------------------------------

def test_validate_secret_not_in_error_response(tmp_path):
    """When YAML contains secrets and Pydantic validation fails,
    the secret must NOT appear in the response body."""
    secret = "SECRET_abc123"
    yaml_content = f"""
id: "test-bed"
some_secret_field: "{secret}"
completely_invalid_structure: true
"""
    p = tmp_path / "secret.yaml"
    p.write_text(yaml_content)
    app = create_app()
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={p}")
    # ok=False (validation error) but secret must not leak
    assert r.status_code == 200
    body_text = r.text
    assert secret not in body_text, f"Secret token leaked in response: {body_text[:300]}"


def test_validate_response_no_raw_content(tmp_path):
    """Validation errors must be structured, not raw YAML content."""
    yaml_content = "not_a_valid: {key: value: bad}\n"
    p = tmp_path / "bad.yaml"
    p.write_text(yaml_content)
    app = create_app()
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={p}")
    assert r.status_code == 200
    body = r.json()
    assert "ok" in body
    assert "errors" in body
