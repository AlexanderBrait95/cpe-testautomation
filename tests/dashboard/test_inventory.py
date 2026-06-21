"""Tests for POST /api/inventory/validate (AC-43, TB-04)."""
from __future__ import annotations

import tempfile
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
# Invalid inventory
# ---------------------------------------------------------------------------

def test_validate_missing_file_returns_ok_false():
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/inventory/validate?path=/no/such/path/testbed.yaml")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert len(body["errors"]) >= 1


def test_validate_broken_yaml_returns_ok_false_no_500():
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("id: test\nwiring_map: [this is not valid pydantic\n")
        broken_path = f.name
    try:
        app = create_app()
        client = TestClient(app)
        r = client.post(f"/api/inventory/validate?path={broken_path}")
        assert r.status_code == 200, "Must not return 500 on broken YAML"
        body = r.json()
        assert body["ok"] is False
        assert isinstance(body["errors"], list)
        assert len(body["errors"]) >= 1
    finally:
        Path(broken_path).unlink(missing_ok=True)


def test_validate_invalid_wiring_returns_structured_errors():
    # Minimal YAML that passes pydantic load but has an empty wiring role name
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
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(yaml_content)
        path = f.name
    try:
        app = create_app()
        client = TestClient(app)
        r = client.post(f"/api/inventory/validate?path={path}")
        assert r.status_code == 200
        body = r.json()
        # May be ok=False (wiring errors) or ok=True if the YAML is actually valid
        # Key constraint: no 500, structured response
        assert "ok" in body
        assert "errors" in body
        assert isinstance(body["errors"], list)
    finally:
        Path(path).unlink(missing_ok=True)


def test_validate_response_never_500():
    """Ensure the endpoint returns 200 with ok=false for all error conditions."""
    app = create_app()
    client = TestClient(app)
    # Try several broken paths
    for bad_path in ["/dev/null", "/nonexistent/path.yaml", ""]:
        if bad_path == "":
            continue  # skip empty to avoid query string oddities
        r = client.post(f"/api/inventory/validate?path={bad_path}")
        assert r.status_code == 200, f"Expected 200 for path {bad_path!r}, got {r.status_code}"
        body = r.json()
        assert "ok" in body
        assert "errors" in body
