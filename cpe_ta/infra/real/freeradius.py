"""FreeRADIUS adapter stub — real RADIUS implementation."""
from __future__ import annotations


class FreeRADIUSAdapter:
    """Adapter for FreeRADIUS. All methods raise NotImplementedError until connected."""

    def __init__(self, host: str, secret: str, port: int = 1812) -> None:
        self._host = host
        self._secret = secret
        self._port = port

    def add_user(self, username: str, password: str, attributes: dict[str, str] | None = None) -> None:
        raise NotImplementedError("Connect to FreeRADIUS")

    def remove_user(self, username: str) -> None:
        raise NotImplementedError("Connect to FreeRADIUS")

    def authenticate(self, username: str, password: str) -> bool:
        raise NotImplementedError("Connect to FreeRADIUS")
