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


# ---------------------------------------------------------------------------
# TV-02: YAML-Snippet-Leak prevention — tab-indent line must not leak (redteam #1)
# ---------------------------------------------------------------------------


def test_validate_yaml_tab_indent_no_snippet_leak(tmp_path):
    """A YAML scanner error caused by a tab indent must not leak the faulty line."""
    secret_token = "TABSECRET_xyz987"
    # YAML does not allow tabs for indentation → scanner error with line context
    yaml_content = f"id: test\nwiring_map:\n\t{secret_token}: value\n"
    p = tmp_path / "tab_secret.yaml"
    p.write_text(yaml_content, encoding="utf-8")
    app = create_app()
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={p}")
    assert r.status_code == 200, "Must return 200 even on YAML scanner error"
    body_text = r.text
    assert secret_token not in body_text, (
        f"TV-02: YAML snippet leaked in response — secret token found: {body_text[:300]}"
    )
    body = r.json()
    assert body["ok"] is False
    assert len(body["errors"]) >= 1


def test_validate_oracle_neutral_not_found_vs_parse_fail(tmp_path):
    """TV-02: not-found and parse-fail must return the same neutral error text (no oracle)."""
    app = create_app()
    client = TestClient(app)

    # not-found
    r_nf = client.post("/api/inventory/validate?path=definitely_not_here_xyz.yaml")
    assert r_nf.status_code == 200
    body_nf = r_nf.json()
    assert body_nf["ok"] is False

    # parse-fail (broken YAML in tmp)
    broken = tmp_path / "broken_oracle.yaml"
    broken.write_text("id: test\nwiring_map:\n\tBAD_INDENT_SECRET\n", encoding="utf-8")
    r_pf = client.post(f"/api/inventory/validate?path={broken}")
    assert r_pf.status_code == 200
    body_pf = r_pf.json()
    assert body_pf["ok"] is False

    # both must return the same error message (no oracle to distinguish)
    assert body_nf["errors"] == body_pf["errors"], (
        f"TV-02: existence oracle — not-found={body_nf['errors']} vs "
        f"parse-fail={body_pf['errors']}"
    )


def test_validate_yaml_error_no_500(tmp_path):
    """TV-02: YAML scanner/parser errors must return 200, not 500."""
    p = tmp_path / "bad_yaml.yaml"
    p.write_text("key:\n\ttab_is_invalid: true\n", encoding="utf-8")
    app = create_app()
    client = TestClient(app)
    r = client.post(f"/api/inventory/validate?path={p}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
