"""Tests for cpe_ta.core.selection — capability-driven skip logic."""

from __future__ import annotations

import pytest

from cpe_ta.core.selection import (
    MARKERS,
    CapabilitySet,
    Technology,
    skip_if_missing,
)

# ---------------------------------------------------------------------------
# CapabilitySet construction
# ---------------------------------------------------------------------------


class TestCapabilitySet:
    def test_defaults_are_empty(self) -> None:
        cs = CapabilitySet()
        assert cs.ports == 0
        assert cs.wifi_bands == set()
        assert cs.max_linkspeed_mbps == 0
        assert cs.has_voip is False
        assert cs.has_usb is False
        assert cs.technologies == set()

    def test_full_construction(self) -> None:
        cs = CapabilitySet(
            ports=4,
            wifi_bands={"2.4GHz", "5GHz"},
            max_linkspeed_mbps=1000,
            has_voip=True,
            has_usb=True,
            technologies={Technology.DSL, Technology.PON},
        )
        assert cs.ports == 4
        assert "5GHz" in cs.wifi_bands
        assert cs.has_voip is True
        assert Technology.DSL in cs.technologies

    def test_technology_enum(self) -> None:
        assert Technology.DSL.value == "dsl"
        assert Technology.DOCSIS.value == "docsis"
        assert Technology.PON.value == "pon"
        assert Technology.FWA.value == "fwa"


# ---------------------------------------------------------------------------
# skip_if_missing — no mismatch (should NOT skip)
# ---------------------------------------------------------------------------


class TestSkipIfMissingNoSkip:
    """All these cases should pass through without calling pytest.skip()."""

    def test_empty_required_never_skips(self) -> None:
        dut = CapabilitySet(ports=4, max_linkspeed_mbps=1000)
        required = CapabilitySet()
        # Should not raise
        skip_if_missing(dut, required)

    def test_sufficient_ports(self) -> None:
        dut = CapabilitySet(ports=4)
        required = CapabilitySet(ports=2)
        skip_if_missing(dut, required)

    def test_exact_ports_match(self) -> None:
        dut = CapabilitySet(ports=2)
        required = CapabilitySet(ports=2)
        skip_if_missing(dut, required)

    def test_wifi_bands_superset(self) -> None:
        dut = CapabilitySet(wifi_bands={"2.4GHz", "5GHz", "6GHz"})
        required = CapabilitySet(wifi_bands={"2.4GHz", "5GHz"})
        skip_if_missing(dut, required)

    def test_linkspeed_sufficient(self) -> None:
        dut = CapabilitySet(max_linkspeed_mbps=2500)
        required = CapabilitySet(max_linkspeed_mbps=1000)
        skip_if_missing(dut, required)

    def test_voip_present(self) -> None:
        dut = CapabilitySet(has_voip=True)
        required = CapabilitySet(has_voip=True)
        skip_if_missing(dut, required)

    def test_voip_not_required(self) -> None:
        dut = CapabilitySet(has_voip=False)
        required = CapabilitySet(has_voip=False)
        skip_if_missing(dut, required)

    def test_usb_present(self) -> None:
        dut = CapabilitySet(has_usb=True)
        required = CapabilitySet(has_usb=True)
        skip_if_missing(dut, required)

    def test_technology_subset(self) -> None:
        dut = CapabilitySet(technologies={Technology.DSL, Technology.FWA})
        required = CapabilitySet(technologies={Technology.DSL})
        skip_if_missing(dut, required)

    def test_full_match(self) -> None:
        caps = CapabilitySet(
            ports=4,
            wifi_bands={"2.4GHz", "5GHz"},
            max_linkspeed_mbps=1000,
            has_voip=True,
            has_usb=True,
            technologies={Technology.PON},
        )
        skip_if_missing(caps, caps)


# ---------------------------------------------------------------------------
# skip_if_missing — mismatch (should trigger pytest.skip)
# ---------------------------------------------------------------------------


class TestSkipIfMissingSkips:
    def test_insufficient_ports_skips(self) -> None:
        dut = CapabilitySet(ports=2)
        required = CapabilitySet(ports=4)
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_missing_wifi_band_skips(self) -> None:
        dut = CapabilitySet(wifi_bands={"2.4GHz"})
        required = CapabilitySet(wifi_bands={"2.4GHz", "5GHz"})
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_low_linkspeed_skips(self) -> None:
        dut = CapabilitySet(max_linkspeed_mbps=100)
        required = CapabilitySet(max_linkspeed_mbps=1000)
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_missing_voip_skips(self) -> None:
        dut = CapabilitySet(has_voip=False)
        required = CapabilitySet(has_voip=True)
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_missing_usb_skips(self) -> None:
        dut = CapabilitySet(has_usb=False)
        required = CapabilitySet(has_usb=True)
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_missing_technology_skips(self) -> None:
        dut = CapabilitySet(technologies={Technology.DSL})
        required = CapabilitySet(technologies={Technology.DOCSIS})
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_no_technologies_vs_required_skips(self) -> None:
        dut = CapabilitySet()
        required = CapabilitySet(technologies={Technology.PON})
        with pytest.raises(pytest.skip.Exception):
            skip_if_missing(dut, required)

    def test_skip_message_mentions_missing_capability(self) -> None:
        dut = CapabilitySet(has_voip=False)
        required = CapabilitySet(has_voip=True)
        with pytest.raises(pytest.skip.Exception) as exc_info:
            skip_if_missing(dut, required, reason="VoIP test suite")
        msg = str(exc_info.value)
        assert "voip" in msg.lower() or "VoIP" in msg

    def test_custom_reason_included_in_skip_message(self) -> None:
        dut = CapabilitySet(ports=1)
        required = CapabilitySet(ports=4)
        with pytest.raises(pytest.skip.Exception) as exc_info:
            skip_if_missing(dut, required, reason="needs 4-port DUT")
        assert "needs 4-port DUT" in str(exc_info.value)

    def test_mismatch_is_skip_not_fail(self) -> None:
        """A capability mismatch must raise pytest.skip, not AssertionError."""
        dut = CapabilitySet(has_usb=False)
        required = CapabilitySet(has_usb=True)
        try:
            skip_if_missing(dut, required)
            pytest.fail("Expected pytest.skip to be called")
        except pytest.skip.Exception:
            pass  # correct


# ---------------------------------------------------------------------------
# Marker list
# ---------------------------------------------------------------------------


class TestMarkers:
    EXPECTED_MARKERS = {
        "smoke",
        "full",
        "regression",
        "tech_dsl",
        "tech_docsis",
        "tech_pon",
        "tech_fwa",
        "headless",
        "hardware",
    }

    def test_markers_list_is_not_empty(self) -> None:
        assert len(MARKERS) > 0

    def test_all_expected_markers_present(self) -> None:
        assert self.EXPECTED_MARKERS.issubset(set(MARKERS))

    def test_markers_is_list_of_strings(self) -> None:
        assert all(isinstance(m, str) for m in MARKERS)

    def test_no_duplicate_markers(self) -> None:
        assert len(MARKERS) == len(set(MARKERS))

    def test_headless_marker_exists(self) -> None:
        assert "headless" in MARKERS

    def test_hardware_marker_exists(self) -> None:
        assert "hardware" in MARKERS

    def test_tech_markers_exist(self) -> None:
        for tech in ["tech_dsl", "tech_docsis", "tech_pon", "tech_fwa"]:
            assert tech in MARKERS, f"Missing marker: {tech}"
