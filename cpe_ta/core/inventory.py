"""Wiring-Map resolution: logical role → physical switch port.

Public API
----------
resolve_role(wiring_map, role) -> PortRef
    Resolve a logical role to its physical port.  Raises InventoryError
    when the role is not found in the wiring map.

validate_wiring_map(wiring_map) -> list[str]
    Return a list of human-readable validation error strings.
    An empty list means the wiring map is consistent.
"""

from __future__ import annotations

from cpe_ta.core.config import PortRef, WiringMap
from cpe_ta.core.errors import InventoryError


def resolve_role(wiring_map: WiringMap, role: str) -> PortRef:
    """Resolve a logical wiring role to a physical port reference.

    Parameters
    ----------
    wiring_map:
        The WiringMap from the loaded testbed configuration.
    role:
        The logical role name (e.g. ``"DUT-LAN-1"``).

    Returns
    -------
    PortRef
        The physical switch port assigned to *role*.

    Raises
    ------
    InventoryError
        When *role* is not present in the wiring map.
    """
    port = wiring_map.get_role(role)
    if port is None:
        available = sorted(wiring_map.roles())
        raise InventoryError(
            f"Role {role!r} is not wired in the testbed. "
            f"Available roles: {available}"
        )
    return port


def validate_wiring_map(wiring_map: WiringMap) -> list[str]:
    """Validate the wiring map and return a list of error messages.

    Checks performed
    ----------------
    1. Duplicate physical ports (one port used by multiple roles).
    2. Empty role names.
    3. Empty switch_id or port_id strings in PortRef.

    Note: duplicate-port detection also happens at model-construction time
    (Pydantic validator), so this function is primarily used for CLI
    reporting where the model may have been created without that path,
    or to surface multiple errors at once rather than stopping at the first.

    Parameters
    ----------
    wiring_map:
        The WiringMap to check.

    Returns
    -------
    list[str]
        Zero or more human-readable error strings.  An empty list means
        the map is valid.
    """
    errors: list[str] = []
    seen_ports: dict[str, str] = {}  # str(port) -> role

    for entry in wiring_map.entries:
        # Check for empty role names
        if not entry.role.strip():
            errors.append("Found a wiring entry with an empty role name")

        # Check for empty switch_id / port_id
        if not entry.port.switch_id.strip():
            errors.append(
                f"Wiring entry role={entry.role!r}: switch_id is empty"
            )
        if not entry.port.port_id.strip():
            errors.append(
                f"Wiring entry role={entry.role!r}: port_id is empty"
            )

        # Duplicate port detection
        key = str(entry.port)
        if key in seen_ports:
            errors.append(
                f"Duplicate port {key!r}: used by both "
                f"role {seen_ports[key]!r} and role {entry.role!r}"
            )
        else:
            seen_ports[key] = entry.role

    return errors
