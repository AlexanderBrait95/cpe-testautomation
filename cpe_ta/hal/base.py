"""Hardware Abstraction Layer — Pure Protocols (no vendor imports)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class PortStats:
    tx_frames: int
    rx_frames: int
    tx_errors: int
    rx_errors: int
    speed_mbps: int
    duplex_full: bool


@dataclass
class OutletState:
    outlet_id: str
    powered: bool


@runtime_checkable
class Switch(Protocol):
    def port_enable(self, port_id: str) -> None: ...

    def port_disable(self, port_id: str) -> None: ...

    def set_speed_duplex(self, port_id: str, speed_mbps: int, full_duplex: bool) -> None: ...

    def set_vlan(self, port_id: str, vlan_id: int, tagged: bool = False) -> None: ...

    def get_port_stats(self, port_id: str) -> PortStats: ...

    def set_mirror(self, source_port: str, dest_port: str, enabled: bool) -> None: ...


@runtime_checkable
class PDU(Protocol):
    def power_on(self, outlet_id: str) -> None: ...

    def power_off(self, outlet_id: str) -> None: ...

    def power_cycle(self, outlet_id: str, delay_s: float = 2.0) -> None: ...

    def get_outlet_state(self, outlet_id: str) -> OutletState: ...


@runtime_checkable
class SerialConsole(Protocol):
    def open(self) -> None: ...

    def close(self) -> None: ...

    def send(self, data: str) -> None: ...

    def read_until(self, pattern: str, timeout_s: float = 10.0) -> str: ...

    def read_metrics(self) -> dict[str, float]: ...  # keys: cpu_percent, ram_percent


@runtime_checkable
class RFAttenuator(Protocol):
    def set_attenuation_db(self, channel: int, db: float) -> None: ...

    def get_attenuation(self, channel: int) -> float: ...

    def isolate(self, enabled: bool) -> None: ...


@runtime_checkable
class USBRelay(Protocol):
    def set_channel(self, channel: int, state: bool) -> None: ...

    def pulse(self, channel: int, duration_s: float = 0.5) -> None: ...
