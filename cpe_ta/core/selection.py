"""Tag-based test selection and capability-driven skip logic.

Design
------
- ``Technology`` enum represents the access technology of the CPE.
- ``CapabilitySet`` describes what a DUT is capable of.
- ``skip_if_missing`` compares a required capability set against the
  DUT's actual capabilities and calls ``pytest.skip()`` on any mismatch.
- ``MARKERS`` is the canonical list of all custom pytest markers used
  in the framework; it is consumed by ``conftest.py`` to register them.
"""

from __future__ import annotations

from enum import StrEnum

import pytest
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Technology(StrEnum):
    """CPE access technology type."""

    DSL = "dsl"
    DOCSIS = "docsis"
    PON = "pon"
    FWA = "fwa"


# ---------------------------------------------------------------------------
# Capability set
# ---------------------------------------------------------------------------


class CapabilitySet(BaseModel):
    """Describes the capabilities of a DUT or the requirements of a test.

    All fields are optional with safe defaults so that partial capability
    specifications are possible.

    Fields
    ------
    ports:
        Number of LAN ports.
    wifi_bands:
        Set of supported WiFi frequency bands (e.g. ``{"2.4GHz", "5GHz"}``).
    max_linkspeed_mbps:
        Maximum LAN port speed in Mbit/s.
    has_voip:
        Whether the device has a VoIP / SIP ATA port.
    has_usb:
        Whether the device has at least one USB host port.
    technologies:
        Set of supported access technologies.
    """

    ports: int = 0
    wifi_bands: set[str] = set()
    max_linkspeed_mbps: int = 0
    has_voip: bool = False
    has_usb: bool = False
    technologies: set[Technology] = set()


# ---------------------------------------------------------------------------
# Skip logic
# ---------------------------------------------------------------------------


def skip_if_missing(
    dut_capabilities: CapabilitySet,
    required: CapabilitySet,
    reason: str = "",
) -> None:
    """Call ``pytest.skip()`` when the DUT lacks a required capability.

    Checks performed (in order)
    ---------------------------
    1. Required ports > DUT ports
    2. Required WiFi bands not a subset of DUT WiFi bands
    3. Required max_linkspeed_mbps > DUT max_linkspeed_mbps
    4. Required has_voip but DUT has none
    5. Required has_usb but DUT has none
    6. Required technologies not a subset of DUT technologies

    Parameters
    ----------
    dut_capabilities:
        The actual capabilities of the DUT under test.
    required:
        The minimum capabilities required by the current test.
    reason:
        Optional additional context appended to the skip message.

    Side effects
    ------------
    Calls ``pytest.skip()`` on any capability mismatch.  Does nothing
    when all required capabilities are met.
    """
    missing: list[str] = []

    if required.ports > dut_capabilities.ports:
        missing.append(
            f"ports: need {required.ports}, DUT has {dut_capabilities.ports}"
        )

    if required.wifi_bands and not required.wifi_bands.issubset(dut_capabilities.wifi_bands):
        lacking = required.wifi_bands - dut_capabilities.wifi_bands
        missing.append(f"wifi_bands: {sorted(lacking)} not supported by DUT")

    if required.max_linkspeed_mbps > dut_capabilities.max_linkspeed_mbps:
        missing.append(
            f"max_linkspeed_mbps: need {required.max_linkspeed_mbps}, "
            f"DUT supports {dut_capabilities.max_linkspeed_mbps}"
        )

    if required.has_voip and not dut_capabilities.has_voip:
        missing.append("has_voip: DUT has no VoIP capability")

    if required.has_usb and not dut_capabilities.has_usb:
        missing.append("has_usb: DUT has no USB port")

    if required.technologies and not required.technologies.issubset(dut_capabilities.technologies):
        lacking_tech = required.technologies - dut_capabilities.technologies
        missing.append(
            f"technologies: {sorted(t.value for t in lacking_tech)} not supported by DUT"
        )

    if missing:
        details = "; ".join(missing)
        skip_msg = f"Capability mismatch — {details}"
        if reason:
            skip_msg = f"{skip_msg} ({reason})"
        pytest.skip(skip_msg)


# ---------------------------------------------------------------------------
# Marker registry
# ---------------------------------------------------------------------------

MARKERS: list[str] = [
    "smoke",
    "full",
    "regression",
    "tech_dsl",
    "tech_docsis",
    "tech_pon",
    "tech_fwa",
    "headless",
    "hardware",
]
"""Canonical list of all custom pytest markers used in cpe-ta.

Registered in ``conftest.py`` via ``pytest_configure``.
"""
