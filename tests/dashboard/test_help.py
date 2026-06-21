"""Tests for GET /api/help — data layer and anti-drift meta-test (AC-36..AC-39, TA-01..TA-03)."""
from __future__ import annotations

import typing

import pytest
from fastapi.testclient import TestClient

from cpe_ta.dashboard.app import create_app
from cpe_ta.dashboard.help import HAL_DEVICE_NAMES, INFRA_SERVICE_KEYS, get_help_content

pytestmark = pytest.mark.headless


# ---------------------------------------------------------------------------
# TA-01: Unit tests for help.py data layer
# ---------------------------------------------------------------------------


def test_quickstart_is_ordered_and_nonempty():
    content = get_help_content()
    assert len(content.quickstart) >= 4, "Quickstart must have at least 4 steps"
    orders = [s.order for s in content.quickstart]
    assert orders == sorted(orders), "Steps must be in ascending order"
    for step in content.quickstart:
        assert step.title.strip(), "Each step must have a non-empty title"
        assert step.description.strip(), "Each step must have a non-empty description"


def test_hardware_entries_count_and_fields():
    content = get_help_content()
    assert len(content.hardware) == 6, "Must have exactly 6 hardware entries (5 HAL + 1 DUT/CPE)"
    for dev in content.hardware:
        assert dev.name.strip()
        assert dev.purpose.strip()
        assert dev.connection.strip()
        assert isinstance(dev.sim_available, bool)


def test_infrastructure_keys_present():
    content = get_help_content()
    keys = {s.key for s in content.infrastructure}
    for expected_key in INFRA_SERVICE_KEYS:
        assert expected_key in keys, f"Infrastructure key {expected_key!r} missing from help content"
    assert len(content.infrastructure) == 7, "Must have exactly 7 infrastructure entries"


# ---------------------------------------------------------------------------
# TA-02: Route GET /api/help returns 200 + schema-conformant JSON
# ---------------------------------------------------------------------------


def test_api_help_returns_200():
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/help")
    assert r.status_code == 200
    body = r.json()
    assert "quickstart" in body
    assert "hardware" in body
    assert "infrastructure" in body


def test_api_help_quickstart_nonempty():
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/help")
    assert r.status_code == 200
    assert len(r.json()["quickstart"]) >= 4


def test_api_help_hardware_has_6_entries():
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/help")
    assert r.status_code == 200
    assert len(r.json()["hardware"]) == 6


def test_api_help_infrastructure_has_7_entries():
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/help")
    assert r.status_code == 200
    assert len(r.json()["infrastructure"]) == 7


# ---------------------------------------------------------------------------
# TA-03: Anti-drift meta-test — help.py hardware list vs real Protocol definitions
# ---------------------------------------------------------------------------


def _get_protocol_names_from_module(module: object) -> set[str]:
    """Collect all runtime-checkable Protocol names from a module."""
    import inspect  # noqa: PLC0415

    names: set[str] = set()
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if hasattr(obj, "__protocol_attrs__") or (
            hasattr(obj, "_is_protocol") and getattr(obj, "_is_protocol", False)
        ):
            names.add(name)
    return names


def test_help_hardware_names_match_hal_and_dut_interfaces():
    """Ensure HAL_DEVICE_NAMES covers every Protocol in hal/base.py + dut/base.py.

    When a new Protocol is added to hal/base.py or dut/base.py, this test fails
    until help.py is updated — preventing silent documentation drift (AC-37).
    """
    import importlib  # noqa: PLC0415
    import inspect  # noqa: PLC0415

    hal_base = importlib.import_module("cpe_ta.hal.base")
    dut_base = importlib.import_module("cpe_ta.dut.base")

    # Must contain at least the 5 known HAL protocols
    expected_hal = {"Switch", "PDU", "SerialConsole", "RFAttenuator", "USBRelay"}
    expected_dut = {"CPE"}

    hal_true_protocols: set[str] = set()
    for name, obj in inspect.getmembers(hal_base, inspect.isclass):
        if getattr(obj, "_is_protocol", False) and obj is not typing.Protocol:
            hal_true_protocols.add(name)
    dut_true_protocols: set[str] = set()
    for name, obj in inspect.getmembers(dut_base, inspect.isclass):
        if getattr(obj, "_is_protocol", False) and obj is not typing.Protocol:
            dut_true_protocols.add(name)

    real_protocols = hal_true_protocols | dut_true_protocols
    for name in expected_hal | expected_dut:
        assert name in real_protocols, f"Expected protocol {name!r} not found in hal/dut base modules"

    help_names = set(HAL_DEVICE_NAMES)
    missing_from_help = real_protocols - help_names
    assert not missing_from_help, (
        f"Protocols defined in hal/dut base.py but missing from HAL_DEVICE_NAMES in help.py: "
        f"{missing_from_help}. Update cpe_ta/dashboard/help.py to add them."
    )


def test_help_infra_keys_match_infra_base():
    """Ensure INFRA_SERVICE_KEYS covers every Protocol key in infra/base.py (AC-38)."""
    import importlib  # noqa: PLC0415
    import inspect  # noqa: PLC0415

    infra_base = importlib.import_module("cpe_ta.infra.base")
    real_protocols: set[str] = set()
    for name, obj in inspect.getmembers(infra_base, inspect.isclass):
        if getattr(obj, "_is_protocol", False) and obj is not typing.Protocol:
            real_protocols.add(name)

    # Map Protocol class names to expected help keys (lowercased / abbreviated)
    _name_to_key = {
        "ACSService": "acs",
        "RADIUSService": "radius",
        "DHCPService": "dhcp",
        "SIPService": "sip",
        "TrafficEndpoint": "traffic",
        "NTPService": "ntp",
        "FileServer": "fileserver",
    }
    help_keys = set(INFRA_SERVICE_KEYS)
    for proto_name in real_protocols:
        expected_key = _name_to_key.get(proto_name)
        if expected_key is not None:
            assert expected_key in help_keys, (
                f"Infra protocol {proto_name!r} mapped to key {expected_key!r} "
                f"but {expected_key!r} is missing from INFRA_SERVICE_KEYS in help.py"
            )
