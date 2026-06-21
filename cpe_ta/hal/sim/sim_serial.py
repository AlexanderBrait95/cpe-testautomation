"""In-memory Serial Console simulator — no real hardware required."""

from __future__ import annotations

from cpe_ta.core.errors import HardwareError


class SimSerialConsole:
    """Headless SerialConsole implementation for use in unit/integration tests."""

    def __init__(
        self,
        cpu_percent: float = 10.0,
        ram_percent: float = 30.0,
    ) -> None:
        self.is_open: bool = False
        self.cpu_percent: float = cpu_percent
        self.ram_percent: float = ram_percent
        # Pre-loaded responses returned one-by-one by read_until()
        self.output_buffer: list[str] = []
        # Commands received via send()
        self._sent_commands: list[str] = []
        # error injection flags
        self.error_inject: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # SerialConsole Protocol implementation
    # ------------------------------------------------------------------

    def open(self) -> None:
        if self.error_inject.get("fail_open"):
            raise HardwareError("Injected error: serial open failed")
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def send(self, data: str) -> None:
        """Collect command into sent_commands log."""
        if not self.is_open:
            raise HardwareError("Serial port is not open")
        self._sent_commands.append(data)

    def read_until(self, pattern: str, timeout_s: float = 10.0) -> str:
        """Return next buffered response; empty string when buffer is exhausted."""
        if self.output_buffer:
            return self.output_buffer.pop(0)
        return ""

    def read_metrics(self) -> dict[str, float]:
        """Return simulated CPU and RAM metrics."""
        return {
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
        }

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------

    def inject_error(self, key: str, value: bool) -> None:
        """Enable or disable a named fault injection flag."""
        self.error_inject[key] = value

    @property
    def sent_commands(self) -> list[str]:
        """Return the list of commands collected by send()."""
        return list(self._sent_commands)
