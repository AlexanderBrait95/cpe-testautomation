"""GenieACS NBI HTTP Adapter — real ACS implementation stub."""
from __future__ import annotations

from typing import Any


class GenieACSClient:
    """HTTP adapter for GenieACS NBI (North-Bound Interface).

    All methods raise NotImplementedError until connected to a live GenieACS instance.
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password

    def bootstrap_cpe(self, cpe_serial: str) -> dict[str, Any]:
        raise NotImplementedError("Connect to GenieACS")

    def get_parameter_values(self, cpe_serial: str, paths: list[str]) -> dict[str, Any]:
        raise NotImplementedError("Connect to GenieACS")

    def set_parameter_values(self, cpe_serial: str, params: dict[str, Any]) -> None:
        raise NotImplementedError("Connect to GenieACS")

    def add_object(self, cpe_serial: str, path: str) -> int:
        raise NotImplementedError("Connect to GenieACS")

    def delete_object(self, cpe_serial: str, path: str) -> None:
        raise NotImplementedError("Connect to GenieACS")

    def reboot(self, cpe_serial: str) -> None:
        raise NotImplementedError("Connect to GenieACS")

    def download(self, cpe_serial: str, url: str, file_type: str) -> None:
        raise NotImplementedError("Connect to GenieACS")

    def schedule_inform(self, cpe_serial: str, delay_s: int) -> None:
        raise NotImplementedError("Connect to GenieACS")

    def get_notifications(self, cpe_serial: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Connect to GenieACS")

    def run_diagnostics(
        self, cpe_serial: str, diag_type: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError("Connect to GenieACS")
