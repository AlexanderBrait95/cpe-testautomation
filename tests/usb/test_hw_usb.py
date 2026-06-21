"""P2 stub — USB Media tests — require physical USB drive (hardware-deferred)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.hardware


def test_usb_samba() -> None:
    """Samba file share on USB storage connected to real DUT."""
    pytest.skip("Requires physical USB drive")


def test_usb_dlna() -> None:
    """DLNA media server on USB storage with a real DLNA client."""
    pytest.skip("Requires physical USB drive, DLNA client")
