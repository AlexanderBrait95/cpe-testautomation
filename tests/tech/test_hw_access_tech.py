"""T35 — Access technology tests — require physical hardware (hardware-deferred)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.hardware


def test_dsl_sync() -> None:
    """DSL line sync and parameter read on real ADSL2+/VDSL2 modem with DSLAM."""
    pytest.skip("Requires DSL modem and DSLAM connection")


def test_docsis_channel_lock() -> None:
    """DOCSIS downstream channel lock verification on real CMTS."""
    pytest.skip("Requires CMTS and DOCSIS downstream")


def test_pon_registration() -> None:
    """GPON/XGS-PON ONU registration on a real OLT with fiber connection."""
    pytest.skip("Requires GPON OLT and fiber connection")


def test_fwa_apn_config() -> None:
    """FWA APN configuration on a real LTE/5G modem with SIM card."""
    pytest.skip("Requires LTE/5G modem with SIM")


def test_pon_rx_power() -> None:
    """Measure PON optical RX power level using an optical power meter."""
    pytest.skip("Requires optical power meter, GPON OLT")


def test_pon_dying_gasp() -> None:
    """Verify GPON dying gasp message on power loss event."""
    pytest.skip("Requires UPS power cutoff, OLT logging")
