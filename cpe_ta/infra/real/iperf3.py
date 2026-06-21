"""iperf3 endpoint adapter stub — real traffic implementation."""
from __future__ import annotations

from cpe_ta.infra.base import TrafficResult


class Iperf3Endpoint:
    """Adapter wrapping the iperf3 CLI tool. All methods raise NotImplementedError until wired."""

    def __init__(self, host: str) -> None:
        self._host = host

    def start_server(self, port: int = 5201, protocol: str = "tcp") -> None:
        raise NotImplementedError("Connect to iperf3")

    def stop_server(self) -> None:
        raise NotImplementedError("Connect to iperf3")

    def run_client(
        self,
        target_ip: str,
        duration_s: int,
        protocol: str = "tcp",
        parallel: int = 1,
    ) -> TrafficResult:
        raise NotImplementedError("Connect to iperf3")
