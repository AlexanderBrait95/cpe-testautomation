"""Simulated ACS (Auto-Configuration Server) for headless testing."""
from __future__ import annotations

from typing import Any


class SimACSService:
    """In-memory ACS that manages CPE state dictionaries keyed by serial number."""

    def __init__(self) -> None:
        # serial → parameter dict
        self._cpe_state: dict[str, dict[str, Any]] = {}
        # serial → list of notifications
        self._notifications: dict[str, list[dict[str, Any]]] = {}
        # serial → pending reboot flag
        self._reboot_flags: dict[str, bool] = {}
        # serial → list of download log entries
        self._download_log: dict[str, list[dict[str, Any]]] = {}
        # serial → scheduled inform delays
        self._inform_schedule: dict[str, list[int]] = {}
        # serial → object instance counters (path → next_index)
        self._object_counters: dict[str, dict[str, int]] = {}

    def bootstrap_cpe(self, cpe_serial: str) -> dict[str, Any]:
        """Register a CPE and return a simulated Inform response."""
        if cpe_serial not in self._cpe_state:
            self._cpe_state[cpe_serial] = {
                "Device.DeviceInfo.SerialNumber": cpe_serial,
                "Device.DeviceInfo.SoftwareVersion": "1.0.0",
                "Device.ManagementServer.URL": "https://acs.example.com/cwmp",
            }
            self._notifications[cpe_serial] = []
            self._reboot_flags[cpe_serial] = False
            self._download_log[cpe_serial] = []
            self._inform_schedule[cpe_serial] = []
            self._object_counters[cpe_serial] = {}
        return {
            "status": "bootstrapped",
            "serial": cpe_serial,
            "acs_url": "https://acs.example.com/cwmp",
        }

    def get_parameter_values(self, cpe_serial: str, paths: list[str]) -> dict[str, Any]:
        """Return a dict of path → value for the requested paths."""
        self._ensure_registered(cpe_serial)
        state = self._cpe_state[cpe_serial]
        return {p: state.get(p) for p in paths}

    def set_parameter_values(self, cpe_serial: str, params: dict[str, Any]) -> None:
        """Write parameter values into CPE state and append notifications."""
        self._ensure_registered(cpe_serial)
        state = self._cpe_state[cpe_serial]
        for path, value in params.items():
            old = state.get(path)
            state[path] = value
            if old != value:
                self._notifications[cpe_serial].append(
                    {"type": "ValueChange", "path": path, "old": old, "new": value}
                )

    def add_object(self, cpe_serial: str, path: str) -> int:
        """Simulate TR-069 AddObject — returns the new instance index."""
        self._ensure_registered(cpe_serial)
        counters = self._object_counters[cpe_serial]
        next_idx = counters.get(path, 0) + 1
        counters[path] = next_idx
        self._cpe_state[cpe_serial][f"{path}.{next_idx}._exists"] = True
        return next_idx

    def delete_object(self, cpe_serial: str, path: str) -> None:
        """Simulate TR-069 DeleteObject — removes matching keys from state."""
        self._ensure_registered(cpe_serial)
        state = self._cpe_state[cpe_serial]
        keys_to_delete = [k for k in state if k.startswith(path)]
        for k in keys_to_delete:
            del state[k]

    def reboot(self, cpe_serial: str) -> None:
        """Set reboot flag for the CPE."""
        self._ensure_registered(cpe_serial)
        self._reboot_flags[cpe_serial] = True

    def download(self, cpe_serial: str, url: str, file_type: str) -> None:
        """Log a firmware/config download request."""
        self._ensure_registered(cpe_serial)
        self._download_log[cpe_serial].append({"url": url, "file_type": file_type})

    def schedule_inform(self, cpe_serial: str, delay_s: int) -> None:
        """Log a scheduled Inform request."""
        self._ensure_registered(cpe_serial)
        self._inform_schedule[cpe_serial].append(delay_s)

    def get_notifications(self, cpe_serial: str) -> list[dict[str, Any]]:
        """Return and flush accumulated notifications for the CPE."""
        self._ensure_registered(cpe_serial)
        notes = list(self._notifications[cpe_serial])
        self._notifications[cpe_serial] = []
        return notes

    def run_diagnostics(
        self, cpe_serial: str, diag_type: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Return pre-canned diagnostic results."""
        self._ensure_registered(cpe_serial)
        if diag_type == "IPPing":
            host = params.get("host", "8.8.8.8")
            return {
                "diag_type": "IPPing",
                "host": host,
                "packets_sent": 4,
                "packets_received": 4,
                "average_response_time_ms": 5.0,
                "min_response_time_ms": 4.0,
                "max_response_time_ms": 7.0,
            }
        if diag_type == "TraceRoute":
            return {"diag_type": "TraceRoute", "hops": 5, "success": True}
        return {"diag_type": diag_type, "success": True}

    # ---------------------------------------------------------------------------
    # Test-helper accessors
    # ---------------------------------------------------------------------------

    def is_rebooted(self, cpe_serial: str) -> bool:
        return self._reboot_flags.get(cpe_serial, False)

    def get_download_log(self, cpe_serial: str) -> list[dict[str, Any]]:
        return list(self._download_log.get(cpe_serial, []))

    def get_inform_schedule(self, cpe_serial: str) -> list[int]:
        return list(self._inform_schedule.get(cpe_serial, []))

    def get_cpe_state(self, cpe_serial: str) -> dict[str, Any]:
        return dict(self._cpe_state.get(cpe_serial, {}))

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _ensure_registered(self, cpe_serial: str) -> None:
        if cpe_serial not in self._cpe_state:
            self.bootstrap_cpe(cpe_serial)
