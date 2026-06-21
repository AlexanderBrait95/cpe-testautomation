"""Tests for cpe_ta.core.inventory — wiring-map resolution."""

from __future__ import annotations

import pytest

from cpe_ta.core.config import PortRef, WiringEntry, WiringMap
from cpe_ta.core.errors import InventoryError
from cpe_ta.core.inventory import resolve_role, validate_wiring_map

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def wiring_map() -> WiringMap:
    return WiringMap(
        entries=[
            WiringEntry(role="DUT-LAN-1", port=PortRef(switch_id="sw1", port_id="gi0/1")),
            WiringEntry(role="DUT-LAN-2", port=PortRef(switch_id="sw1", port_id="gi0/2")),
            WiringEntry(role="DUT-WAN", port=PortRef(switch_id="sw1", port_id="gi0/3")),
            WiringEntry(role="TRAFFIC-EP-1", port=PortRef(switch_id="sw1", port_id="gi0/4")),
        ]
    )


# ---------------------------------------------------------------------------
# resolve_role — happy paths
# ---------------------------------------------------------------------------


class TestResolveRole:
    def test_resolve_dut_lan_1(self, wiring_map: WiringMap) -> None:
        port = resolve_role(wiring_map, "DUT-LAN-1")
        assert port.switch_id == "sw1"
        assert port.port_id == "gi0/1"

    def test_resolve_dut_wan(self, wiring_map: WiringMap) -> None:
        port = resolve_role(wiring_map, "DUT-WAN")
        assert port.port_id == "gi0/3"

    def test_resolve_traffic_ep(self, wiring_map: WiringMap) -> None:
        port = resolve_role(wiring_map, "TRAFFIC-EP-1")
        assert port.port_id == "gi0/4"

    def test_resolved_port_is_port_ref(self, wiring_map: WiringMap) -> None:
        port = resolve_role(wiring_map, "DUT-LAN-2")
        assert isinstance(port, PortRef)

    def test_all_roles_resolvable(self, wiring_map: WiringMap) -> None:
        for role in ["DUT-LAN-1", "DUT-LAN-2", "DUT-WAN", "TRAFFIC-EP-1"]:
            port = resolve_role(wiring_map, role)
            assert port is not None


# ---------------------------------------------------------------------------
# resolve_role — error paths
# ---------------------------------------------------------------------------


class TestResolveRoleErrors:
    def test_unknown_role_raises_inventory_error(self, wiring_map: WiringMap) -> None:
        with pytest.raises(InventoryError):
            resolve_role(wiring_map, "DOES-NOT-EXIST")

    def test_error_message_contains_role_name(self, wiring_map: WiringMap) -> None:
        missing = "DUT-UPLINK-UNKNOWN"
        with pytest.raises(InventoryError, match=missing):
            resolve_role(wiring_map, missing)

    def test_error_message_lists_available_roles(self, wiring_map: WiringMap) -> None:
        with pytest.raises(InventoryError, match="DUT-LAN-1"):
            resolve_role(wiring_map, "MISSING")

    def test_empty_wiring_map_raises_inventory_error(self) -> None:
        empty = WiringMap(entries=[])
        with pytest.raises(InventoryError):
            resolve_role(empty, "DUT-LAN-1")

    def test_case_sensitive_role_matching(self, wiring_map: WiringMap) -> None:
        """Role names are case-sensitive."""
        with pytest.raises(InventoryError):
            resolve_role(wiring_map, "dut-lan-1")


# ---------------------------------------------------------------------------
# validate_wiring_map
# ---------------------------------------------------------------------------


class TestValidateWiringMap:
    def test_valid_map_returns_empty_list(self, wiring_map: WiringMap) -> None:
        errors = validate_wiring_map(wiring_map)
        assert errors == []

    def test_empty_map_is_valid(self) -> None:
        errors = validate_wiring_map(WiringMap(entries=[]))
        assert errors == []

    def test_empty_switch_id_is_reported(self) -> None:
        wm = WiringMap.__new__(WiringMap)
        # Bypass pydantic construction to inject invalid data
        entry = WiringEntry.__new__(WiringEntry)
        object.__setattr__(entry, "role", "DUT-LAN-1")
        port = PortRef.__new__(PortRef)
        object.__setattr__(port, "switch_id", "")
        object.__setattr__(port, "port_id", "gi0/1")
        object.__setattr__(entry, "port", port)
        object.__setattr__(wm, "entries", [entry])
        errors = validate_wiring_map(wm)
        assert any("switch_id" in e for e in errors)

    def test_empty_port_id_is_reported(self) -> None:
        wm = WiringMap.__new__(WiringMap)
        entry = WiringEntry.__new__(WiringEntry)
        object.__setattr__(entry, "role", "DUT-LAN-1")
        port = PortRef.__new__(PortRef)
        object.__setattr__(port, "switch_id", "sw1")
        object.__setattr__(port, "port_id", "")
        object.__setattr__(entry, "port", port)
        object.__setattr__(wm, "entries", [entry])
        errors = validate_wiring_map(wm)
        assert any("port_id" in e for e in errors)

    def test_duplicate_port_detected_by_validator(self) -> None:
        """validate_wiring_map catches duplicates independently of Pydantic."""
        wm = WiringMap.__new__(WiringMap)
        e1 = WiringEntry.__new__(WiringEntry)
        e2 = WiringEntry.__new__(WiringEntry)
        port = PortRef(switch_id="sw1", port_id="gi0/1")
        object.__setattr__(e1, "role", "DUT-LAN-1")
        object.__setattr__(e1, "port", port)
        object.__setattr__(e2, "role", "DUT-WAN")
        object.__setattr__(e2, "port", port)
        object.__setattr__(wm, "entries", [e1, e2])

        errors = validate_wiring_map(wm)
        assert len(errors) == 1
        assert "sw1:gi0/1" in errors[0]

    def test_returns_list_type(self, wiring_map: WiringMap) -> None:
        result = validate_wiring_map(wiring_map)
        assert isinstance(result, list)
