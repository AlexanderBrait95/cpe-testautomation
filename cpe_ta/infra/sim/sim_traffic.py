"""Simulated traffic endpoint (iperf3-like) for headless testing."""
from __future__ import annotations

from cpe_ta.infra.base import TrafficResult


class SimTrafficEndpoint:
    """Deterministic traffic simulator with configurable result values."""

    def __init__(
        self,
        configurable_throughput: float = 900.0,
        configurable_latency_ms: float = 1.0,
        configurable_jitter_ms: float = 0.1,
        configurable_packet_loss: float = 0.0,
    ) -> None:
        self.configurable_throughput = configurable_throughput
        self.configurable_latency_ms = configurable_latency_ms
        self.configurable_jitter_ms = configurable_jitter_ms
        self.configurable_packet_loss = configurable_packet_loss
        self.server_running: bool = False
        self._server_port: int = 5201
        self._server_protocol: str = "tcp"

    def start_server(self, port: int = 5201, protocol: str = "tcp") -> None:
        self.server_running = True
        self._server_port = port
        self._server_protocol = protocol

    def stop_server(self) -> None:
        self.server_running = False

    def run_client(
        self,
        target_ip: str,
        duration_s: int,
        protocol: str = "tcp",
        parallel: int = 1,
    ) -> TrafficResult:
        return TrafficResult(
            throughput_mbps=self.configurable_throughput,
            latency_ms=self.configurable_latency_ms,
            jitter_ms=self.configurable_jitter_ms,
            packet_loss_percent=self.configurable_packet_loss,
        )
