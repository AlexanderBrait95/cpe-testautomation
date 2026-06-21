"""Serial Console driver skeleton — requires pyserial (not in base requirements)."""

from __future__ import annotations

# Lazy import: pyserial is optional hardware-specific dependency
try:
    import serial  # type: ignore[import-untyped]  # noqa: F401

    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False


class SerialConsoleDriver:
    """Real Serial Console driver using pyserial.

    Connect this to physical console servers or direct RS-232/USB-serial
    adapters to interact with CPE devices over their management console.

    Raises
    ------
    NotImplementedError
        All methods — connect to real hardware to implement.
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        timeout_s: float = 10.0,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout_s = timeout_s

    def open(self) -> None:
        # TODO: serial.Serial(port=self._port, baudrate=self._baudrate, timeout=self._timeout_s)
        raise NotImplementedError("Serial driver: connect to real hardware")

    def close(self) -> None:
        # TODO: self._serial.close()
        raise NotImplementedError("Serial driver: connect to real hardware")

    def send(self, data: str) -> None:
        # TODO: self._serial.write(data.encode())
        raise NotImplementedError("Serial driver: connect to real hardware")

    def read_until(self, pattern: str, timeout_s: float = 10.0) -> str:
        # TODO: read data until pattern appears or timeout expires
        raise NotImplementedError("Serial driver: connect to real hardware")

    def read_metrics(self) -> dict[str, float]:
        # TODO: send metrics command and parse CPU/RAM from output
        raise NotImplementedError("Serial driver: connect to real hardware")
