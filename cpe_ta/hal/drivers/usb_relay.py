"""USB Relay driver skeleton — no hardware library import needed at skeleton level."""

from __future__ import annotations

# Note: real implementation would import hidapi or a vendor-specific USB library.
# These are not included in base requirements and are not imported here.
# HAS_HIDAPI = False (placeholder — add lazy import when implementing)


class USBRelayDriver:
    """Real USB Relay driver using HID API (hidapi/usb).

    Connect this to USB relay boards (e.g. LCUS-1, HID-compliant relay modules)
    for controlling power or signal paths in the test lab.

    Raises
    ------
    NotImplementedError
        All methods — connect to real hardware to implement.
    """

    def __init__(
        self,
        vendor_id: int = 0x16C0,
        product_id: int = 0x05DF,
    ) -> None:
        self._vendor_id = vendor_id
        self._product_id = product_id

    def set_channel(self, channel: int, state: bool) -> None:
        # TODO: open HID device and send channel enable/disable command
        raise NotImplementedError("USB Relay driver: connect to real hardware")

    def pulse(self, channel: int, duration_s: float = 0.5) -> None:
        # TODO: set_channel(channel, True), sleep(duration_s), set_channel(channel, False)
        raise NotImplementedError("USB Relay driver: connect to real hardware")
