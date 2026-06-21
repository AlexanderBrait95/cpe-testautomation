"""P2 stub — VoIP tests — require SIP phone + IMS infrastructure (hardware-deferred)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.hardware


def test_voip_mtc() -> None:
    """VoIP MTC (Media Test Call) on SIP phone with IMS infrastructure."""
    pytest.skip("Requires SIP phone, IMS infrastructure")


def test_voip_t38() -> None:
    """T.38 fax-over-IP test with real fax machine and T.38 gateway."""
    pytest.skip("Requires fax machine, T.38 gateway")
