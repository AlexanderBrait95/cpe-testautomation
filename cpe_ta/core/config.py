"""Pydantic v2 configuration models for testbed, inventory and wiring-map.

Design rules
------------
- All models use strict Pydantic v2 validation.
- Secrets (SNMP community strings, credentials) are accepted as plain
  strings here but should be populated from environment variables or
  secret files — never hard-coded in YAML committed to the repository.
- ``load_testbed`` converts any load/parse/validation error into a
  typed ``ConfigError`` so callers never see raw Pydantic tracebacks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, model_validator

from cpe_ta.core.errors import ConfigError

# ---------------------------------------------------------------------------
# Primitive building blocks
# ---------------------------------------------------------------------------


class PortRef(BaseModel):
    """Reference to a physical port on a managed switch."""

    switch_id: str
    port_id: str

    def __hash__(self) -> int:
        return hash((self.switch_id, self.port_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortRef):
            return NotImplemented
        return self.switch_id == other.switch_id and self.port_id == other.port_id

    def __str__(self) -> str:
        return f"{self.switch_id}:{self.port_id}"


class WiringEntry(BaseModel):
    """Maps a logical wiring role to a physical switch port."""

    role: str
    port: PortRef


# ---------------------------------------------------------------------------
# WiringMap — with duplicate-port validation
# ---------------------------------------------------------------------------


class WiringMap(BaseModel):
    """Collection of wiring entries.

    Validation ensures:
    - No two entries share the same physical port (a port can only fulfil
      one logical role at a time).
    """

    entries: list[WiringEntry] = []

    @model_validator(mode="after")
    def _check_no_duplicate_ports(self) -> WiringMap:
        seen: dict[str, str] = {}  # str(port) -> role
        for entry in self.entries:
            key = str(entry.port)
            if key in seen:
                raise ConfigError(
                    f"Duplicate port assignment: {key} is used by both "
                    f"role '{seen[key]}' and role '{entry.role}'"
                )
            seen[key] = entry.role
        return self

    def get_role(self, role: str) -> PortRef | None:
        """Return the PortRef for a logical role, or None if not present."""
        for entry in self.entries:
            if entry.role == role:
                return entry.port
        return None

    def roles(self) -> list[str]:
        """Return all configured logical role names."""
        return [e.role for e in self.entries]


# ---------------------------------------------------------------------------
# Inventory models
# ---------------------------------------------------------------------------


class SwitchInventory(BaseModel):
    """Managed switch accessible via SNMP, NETCONF or REST."""

    switch_id: str
    host: str
    protocol: str  # "snmp" | "netconf" | "rest"
    # Secrets: populated from env/secret files at runtime, not from YAML values
    community: str | None = None       # SNMP community (read from env at runtime)
    credentials: dict[str, str] | None = None  # username/password dict

    @field_validator("protocol")
    @classmethod
    def _validate_protocol(cls, v: str) -> str:
        allowed = {"snmp", "netconf", "rest"}
        if v not in allowed:
            raise ValueError(f"protocol must be one of {sorted(allowed)}, got {v!r}")
        return v


class PDUInventory(BaseModel):
    """Power Distribution Unit."""

    pdu_id: str
    host: str
    protocol: str  # "snmp" | "http" | "modbus"

    @field_validator("protocol")
    @classmethod
    def _validate_protocol(cls, v: str) -> str:
        allowed = {"snmp", "http", "modbus"}
        if v not in allowed:
            raise ValueError(f"PDU protocol must be one of {sorted(allowed)}, got {v!r}")
        return v


class DUTInventory(BaseModel):
    """Device-Under-Test (CPE) inventory entry."""

    dut_id: str
    model: str
    vendor: str
    capabilities_file: str | None = None   # path to capabilities YAML (optional)
    wiring: list[str] = []                 # list of wiring roles this DUT uses


# ---------------------------------------------------------------------------
# Top-level testbed
# ---------------------------------------------------------------------------


class Testbed(BaseModel):
    """Complete testbed configuration."""

    id: str
    switches: list[SwitchInventory] = []
    pdus: list[PDUInventory] = []
    duts: list[DUTInventory] = []
    wiring_map: WiringMap = WiringMap()

    @model_validator(mode="after")
    def _check_switch_ids_unique(self) -> Testbed:
        ids = [s.switch_id for s in self.switches]
        if len(ids) != len(set(ids)):
            raise ConfigError("Duplicate switch_id entries in testbed")
        return self

    @model_validator(mode="after")
    def _check_pdu_ids_unique(self) -> Testbed:
        ids = [p.pdu_id for p in self.pdus]
        if len(ids) != len(set(ids)):
            raise ConfigError("Duplicate pdu_id entries in testbed")
        return self

    @model_validator(mode="after")
    def _check_dut_ids_unique(self) -> Testbed:
        ids = [d.dut_id for d in self.duts]
        if len(ids) != len(set(ids)):
            raise ConfigError("Duplicate dut_id entries in testbed")
        return self


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_testbed(path: str) -> Testbed:
    """Load and validate a testbed YAML file.

    Parameters
    ----------
    path:
        Filesystem path to the YAML file.

    Returns
    -------
    Testbed
        Validated testbed model instance.

    Raises
    ------
    ConfigError
        On any file-not-found, YAML parse error, or Pydantic validation
        failure.  Raw library exceptions are wrapped so callers always
        receive a typed ``ConfigError``.
    """
    file = Path(path)
    if not file.exists():
        raise ConfigError(f"Testbed file not found: {path}")

    try:
        raw: Any = yaml.safe_load(file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Testbed YAML must be a mapping, got {type(raw).__name__}")

    try:
        return Testbed.model_validate(raw)
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"Testbed validation failed for {path}: {exc}") from exc
