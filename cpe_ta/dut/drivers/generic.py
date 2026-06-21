"""Generic CPE Driver skeleton (Adapter Pattern)."""
from typing import Any

from cpe_ta.dut.base import CPE  # noqa: F401
from cpe_ta.dut.capabilities import CapabilitySet


class GenericCPEDriver:
    """Base vendor driver. Subclass and override per-vendor methods."""

    def __init__(self, dut_id: str, host: str, caps: CapabilitySet):
        self._dut_id = dut_id
        self._host = host
        self._caps = caps

    @property
    def dut_id(self) -> str:
        return self._dut_id

    @property
    def capabilities(self) -> CapabilitySet:
        return self._caps

    def factory_reset(self, wait_s: float = 120.0) -> None:
        raise NotImplementedError("Implement in vendor subclass")

    def power_off(self) -> None:
        raise NotImplementedError

    def power_on(self) -> None:
        raise NotImplementedError

    def power_cycle(self, delay_s: float = 5.0) -> None:
        raise NotImplementedError

    def config_backup(self) -> dict[str, Any]:
        raise NotImplementedError

    def config_restore(self, config: dict[str, Any]) -> None:
        raise NotImplementedError

    def fw_flash(self, firmware_path: str, bank: str = "primary") -> None:
        raise NotImplementedError

    def fw_rollback(self) -> None:
        raise NotImplementedError

    def get_console_metrics(self) -> dict[str, float]:
        raise NotImplementedError

    def get_wan_ip(self) -> str | None:
        raise NotImplementedError

    def get_parameter(self, path: str) -> Any:
        raise NotImplementedError

    def set_parameter(self, path: str, value: Any) -> None:
        raise NotImplementedError
