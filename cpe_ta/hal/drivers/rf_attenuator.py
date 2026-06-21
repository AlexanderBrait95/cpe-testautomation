"""RF Attenuator driver skeleton — uses SSH via paramiko (not in base requirements)."""

from __future__ import annotations

# Lazy import: paramiko is optional hardware-specific dependency
try:
    import paramiko  # type: ignore[import-untyped]  # noqa: F401

    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class RFAttenuatorDriver:
    """Real RF Attenuator driver using SSH (paramiko).

    Connect this to programmable RF attenuators that accept commands over
    SSH (e.g. Mini-Circuits, Vaunix, Rohde & Schwarz SCPI over SSH).

    Raises
    ------
    NotImplementedError
        All methods — connect to real hardware to implement.
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "admin",
        password: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    def set_attenuation_db(self, channel: int, db: float) -> None:
        # TODO: SSH connect and send SCPI command e.g. "CHAN {channel}:ATT {db}"
        raise NotImplementedError("RF Attenuator driver: connect to real hardware")

    def get_attenuation(self, channel: int) -> float:
        # TODO: SSH connect and query e.g. "CHAN {channel}:ATT?"
        raise NotImplementedError("RF Attenuator driver: connect to real hardware")

    def isolate(self, enabled: bool) -> None:
        # TODO: SSH connect and send isolation command
        raise NotImplementedError("RF Attenuator driver: connect to real hardware")
