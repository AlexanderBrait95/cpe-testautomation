"""Deterministic Simulated CPE for headless testing."""
from __future__ import annotations

from typing import Any

from cpe_ta.dut.base import CPE  # noqa: F401
from cpe_ta.dut.capabilities import CapabilitySet, Technology, WiFiBand


class SimCPE:
    """Fully simulated CPE with CWMP-agent state, config-state, counters, WiFi state."""

    DEFAULT_CAPS = CapabilitySet(
        lan_ports=4,
        wan_ports=1,
        wifi_bands=[WiFiBand.BAND_2_4, WiFiBand.BAND_5],
        max_linkspeed_mbps=1000,
        has_voip=False,
        has_usb=True,
        technologies=[Technology.DSL, Technology.FWA],
        supports_wpa3=True,
    )

    def __init__(self, dut_id: str = "sim-cpe-01", caps: CapabilitySet | None = None):
        self._dut_id = dut_id
        self._caps = caps or self.DEFAULT_CAPS
        self._powered = True
        self._config: dict[str, Any] = self._default_config()
        self._lan_counters: dict[str, dict[str, int]] = {}
        self._wifi_state: dict[str, Any] = self._default_wifi()
        self._wan_ip: str | None = "100.64.0.1"
        self._cpu_percent: float = 5.0
        self._ram_percent: float = 20.0
        self._reboot_count: int = 0
        self._cwmp_session_count: int = 0
        # CWMP inform parameters
        self._inform_interval: int = 3600
        self._acs_url: str = "https://acs.example.com/cwmp"

    def _default_config(self) -> dict[str, Any]:
        return {
            "Device.DeviceInfo.SoftwareVersion": "1.0.0",
            "Device.DeviceInfo.HardwareVersion": "1.0",
            "Device.DeviceInfo.Manufacturer": "SimVendor",
            "Device.DeviceInfo.ModelName": "SimCPE-1000",
            "Device.DeviceInfo.SerialNumber": "SIM000001",
            "Device.DeviceInfo.UpTime": 0,
            "Device.ManagementServer.URL": "https://acs.example.com/cwmp",
            "Device.ManagementServer.Username": "cpe-sim",
            "Device.IP.Interface.1.IPv4Address.1.IPAddress": "100.64.0.1",
            "Device.WiFi.SSID.1.SSID": "SimNet",
            "Device.WiFi.AccessPoint.1.Security.ModeEnabled": "WPA2-Personal",
            "Device.WiFi.AccessPoint.1.Security.KeyPassphrase": "SimPass123",
            "Device.WiFi.Radio.1.Enable": True,
            "Device.WiFi.Radio.1.Channel": 6,
            "Device.WiFi.Radio.1.OperatingFrequencyBand": "2.4GHz",
            "Device.WiFi.Radio.2.Enable": True,
            "Device.WiFi.Radio.2.Channel": 36,
            "Device.WiFi.Radio.2.OperatingFrequencyBand": "5GHz",
            "Device.DHCPv4.Server.Pool.1.MinAddress": "192.168.1.100",
            "Device.DHCPv4.Server.Pool.1.MaxAddress": "192.168.1.200",
            "Device.DHCPv4.Server.Pool.1.SubnetMask": "255.255.255.0",
            "Device.Firewall.Enable": True,
        }

    def _default_wifi(self) -> dict[str, Any]:
        return {
            "ssid": "SimNet",
            "security_mode": "WPA2-Personal",
            "passphrase": "SimPass123",
            "hidden": False,
            "guest_ssid": None,
            "band_steering": False,
            "connected_clients": [],
        }

    @property
    def dut_id(self) -> str:
        return self._dut_id

    @property
    def capabilities(self) -> CapabilitySet:
        return self._caps

    def factory_reset(self, wait_s: float = 0.0) -> None:
        self._config = self._default_config()
        self._wifi_state = self._default_wifi()
        self._wan_ip = "100.64.0.1"
        self._reboot_count += 1
        self._cpu_percent = 5.0
        self._ram_percent = 20.0

    def power_off(self) -> None:
        self._powered = False
        self._wan_ip = None

    def power_on(self) -> None:
        self._powered = True
        self._wan_ip = "100.64.0.1"

    def power_cycle(self, delay_s: float = 0.0) -> None:
        self.power_off()
        self.power_on()
        self._reboot_count += 1

    def config_backup(self) -> dict[str, Any]:
        return dict(self._config)

    def config_restore(self, config: dict[str, Any]) -> None:
        self._config = dict(config)

    def fw_flash(self, firmware_path: str, bank: str = "primary") -> None:
        parts = firmware_path.split("/")
        version = parts[-1].replace(".bin", "") if parts else "2.0.0"
        self._config["Device.DeviceInfo.SoftwareVersion"] = version
        self._reboot_count += 1

    def fw_rollback(self) -> None:
        self._config["Device.DeviceInfo.SoftwareVersion"] = "1.0.0"
        self._reboot_count += 1

    def get_console_metrics(self) -> dict[str, float]:
        return {"cpu_percent": self._cpu_percent, "ram_percent": self._ram_percent}

    def get_wan_ip(self) -> str | None:
        return self._wan_ip if self._powered else None

    def get_parameter(self, path: str) -> Any:
        if not self._powered:
            from cpe_ta.core.errors import DUTError

            raise DUTError(f"DUT {self._dut_id} is powered off")
        return self._config.get(path)

    def set_parameter(self, path: str, value: Any) -> None:
        if not self._powered:
            from cpe_ta.core.errors import DUTError

            raise DUTError(f"DUT {self._dut_id} is powered off")
        self._config[path] = value

    # CWMP-sim helpers (for ACS tests)
    def cwmp_inform(self) -> dict[str, Any]:
        """Simulate a CWMP Inform message."""
        self._cwmp_session_count += 1
        return {
            "manufacturer": self._config.get("Device.DeviceInfo.Manufacturer"),
            "model": self._config.get("Device.DeviceInfo.ModelName"),
            "serial": self._config.get("Device.DeviceInfo.SerialNumber"),
            "sw_version": self._config.get("Device.DeviceInfo.SoftwareVersion"),
            "session_id": self._cwmp_session_count,
        }

    def simulate_memory_leak(self, ram_increment: float = 5.0) -> None:
        """Inject memory growth for stress tests."""
        self._ram_percent = min(100.0, self._ram_percent + ram_increment)

    def simulate_cpu_spike(self, cpu_percent: float = 95.0) -> None:
        self._cpu_percent = min(100.0, cpu_percent)

    @property
    def reboot_count(self) -> int:
        return self._reboot_count
