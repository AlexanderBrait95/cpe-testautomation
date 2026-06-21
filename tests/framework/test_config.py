"""Tests for cpe_ta.core.config (Pydantic v2 testbed models)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from pydantic import ValidationError

from cpe_ta.core.config import (
    ConfigError,
    DUTInventory,
    PDUInventory,
    PortRef,
    SwitchInventory,
    Testbed,
    WiringEntry,
    WiringMap,
    load_testbed,
)

# ---------------------------------------------------------------------------
# PortRef
# ---------------------------------------------------------------------------


class TestPortRef:
    def test_str(self) -> None:
        p = PortRef(switch_id="sw1", port_id="gi0/1")
        assert str(p) == "sw1:gi0/1"

    def test_equality(self) -> None:
        a = PortRef(switch_id="sw1", port_id="gi0/1")
        b = PortRef(switch_id="sw1", port_id="gi0/1")
        assert a == b

    def test_hashable(self) -> None:
        p = PortRef(switch_id="sw1", port_id="gi0/1")
        s = {p}
        assert p in s


# ---------------------------------------------------------------------------
# WiringMap validation
# ---------------------------------------------------------------------------


class TestWiringMap:
    def test_valid_wiring_map(self) -> None:
        wm = WiringMap(
            entries=[
                WiringEntry(role="DUT-LAN-1", port=PortRef(switch_id="sw1", port_id="gi0/1")),
                WiringEntry(role="DUT-WAN", port=PortRef(switch_id="sw1", port_id="gi0/2")),
            ]
        )
        assert len(wm.entries) == 2

    def test_duplicate_port_raises_config_error(self) -> None:
        with pytest.raises((ConfigError, Exception)) as exc_info:
            WiringMap(
                entries=[
                    WiringEntry(role="DUT-LAN-1", port=PortRef(switch_id="sw1", port_id="gi0/1")),
                    WiringEntry(role="DUT-WAN", port=PortRef(switch_id="sw1", port_id="gi0/1")),
                ]
            )
        assert "Duplicate port" in str(exc_info.value) or "gi0/1" in str(exc_info.value)

    def test_get_role_found(self) -> None:
        wm = WiringMap(
            entries=[
                WiringEntry(role="DUT-LAN-1", port=PortRef(switch_id="sw1", port_id="gi0/1")),
            ]
        )
        port = wm.get_role("DUT-LAN-1")
        assert port is not None
        assert port.port_id == "gi0/1"

    def test_get_role_not_found(self) -> None:
        wm = WiringMap(entries=[])
        assert wm.get_role("NONEXISTENT") is None

    def test_roles_list(self) -> None:
        wm = WiringMap(
            entries=[
                WiringEntry(role="DUT-LAN-1", port=PortRef(switch_id="sw1", port_id="gi0/1")),
                WiringEntry(role="DUT-WAN", port=PortRef(switch_id="sw1", port_id="gi0/2")),
            ]
        )
        assert set(wm.roles()) == {"DUT-LAN-1", "DUT-WAN"}


# ---------------------------------------------------------------------------
# SwitchInventory
# ---------------------------------------------------------------------------


class TestSwitchInventory:
    def test_valid_snmp_switch(self) -> None:
        s = SwitchInventory(switch_id="sw1", host="10.0.0.1", protocol="snmp")
        assert s.protocol == "snmp"

    def test_invalid_protocol_raises(self) -> None:
        with pytest.raises(ValidationError):
            SwitchInventory(switch_id="sw1", host="10.0.0.1", protocol="telnet")


# ---------------------------------------------------------------------------
# PDUInventory
# ---------------------------------------------------------------------------


class TestPDUInventory:
    def test_valid_http_pdu(self) -> None:
        p = PDUInventory(pdu_id="pdu1", host="10.0.0.2", protocol="http")
        assert p.pdu_id == "pdu1"

    def test_invalid_protocol(self) -> None:
        with pytest.raises(ValidationError):
            PDUInventory(pdu_id="pdu1", host="10.0.0.2", protocol="ssh")


# ---------------------------------------------------------------------------
# Testbed
# ---------------------------------------------------------------------------


class TestTestbed:
    def _make_minimal_testbed(self) -> Testbed:
        return Testbed(id="test-tb")

    def test_minimal_testbed(self) -> None:
        tb = self._make_minimal_testbed()
        assert tb.id == "test-tb"
        assert tb.switches == []
        assert tb.pdus == []
        assert tb.duts == []

    def test_duplicate_switch_id_raises(self) -> None:
        sw = SwitchInventory(switch_id="sw1", host="10.0.0.1", protocol="snmp")
        with pytest.raises(ConfigError):
            Testbed(id="tb", switches=[sw, sw])

    def test_duplicate_dut_id_raises(self) -> None:
        dut = DUTInventory(dut_id="dut1", model="X500", vendor="Acme")
        with pytest.raises(ConfigError):
            Testbed(id="tb", duts=[dut, dut])


# ---------------------------------------------------------------------------
# load_testbed
# ---------------------------------------------------------------------------


class TestLoadTestbed:
    def test_load_example_yaml(self) -> None:
        """The shipped example file must load without errors."""
        example = Path(__file__).parents[2] / "testbed.example.yaml"
        tb = load_testbed(str(example))
        assert tb.id == "lab-testbed-01"
        assert len(tb.switches) == 1
        assert len(tb.pdus) == 1
        assert len(tb.duts) == 1
        assert len(tb.wiring_map.entries) == 4

    def test_load_nonexistent_file_raises_config_error(self) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_testbed("/nonexistent/path/testbed.yaml")

    def test_load_invalid_yaml_raises_config_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text(": invalid: yaml: [\n", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_testbed(str(bad))

    def test_load_not_a_mapping_raises_config_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "list.yaml"
        bad.write_text("- one\n- two\n", encoding="utf-8")
        with pytest.raises(ConfigError, match="mapping"):
            load_testbed(str(bad))

    def test_load_missing_required_field_raises_config_error(self, tmp_path: Path) -> None:
        """Testbed without 'id' field should raise ConfigError."""
        yaml_content = textwrap.dedent("""\
            switches: []
            pdus: []
            duts: []
            wiring_map:
              entries: []
        """)
        bad = tmp_path / "noid.yaml"
        bad.write_text(yaml_content, encoding="utf-8")
        with pytest.raises(ConfigError):
            load_testbed(str(bad))

    def test_load_duplicate_port_raises_config_error(self, tmp_path: Path) -> None:
        """A wiring_map with two entries on the same port should fail."""
        yaml_content = textwrap.dedent("""\
            id: "tb-dup"
            wiring_map:
              entries:
                - role: "DUT-LAN-1"
                  port:
                    switch_id: "sw1"
                    port_id: "gi0/1"
                - role: "DUT-WAN"
                  port:
                    switch_id: "sw1"
                    port_id: "gi0/1"
        """)
        dup = tmp_path / "dup.yaml"
        dup.write_text(yaml_content, encoding="utf-8")
        with pytest.raises(ConfigError):
            load_testbed(str(dup))

    def test_load_valid_full_testbed(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            id: "lab-01"
            switches:
              - switch_id: "sw1"
                host: "10.0.0.1"
                protocol: "snmp"
            pdus:
              - pdu_id: "pdu1"
                host: "10.0.0.2"
                protocol: "http"
            duts:
              - dut_id: "dut1"
                model: "CPE-X"
                vendor: "Acme"
            wiring_map:
              entries:
                - role: "DUT-LAN-1"
                  port:
                    switch_id: "sw1"
                    port_id: "gi0/1"
                - role: "DUT-WAN"
                  port:
                    switch_id: "sw1"
                    port_id: "gi0/2"
        """)
        valid = tmp_path / "valid.yaml"
        valid.write_text(yaml_content, encoding="utf-8")
        tb = load_testbed(str(valid))
        assert tb.id == "lab-01"
        assert tb.switches[0].switch_id == "sw1"
        assert tb.pdus[0].pdu_id == "pdu1"
        assert tb.duts[0].dut_id == "dut1"
        assert len(tb.wiring_map.entries) == 2
