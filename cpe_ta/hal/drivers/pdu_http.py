"""HTTP PDU driver skeleton — uses requests (already in dependencies)."""

from __future__ import annotations

import requests

from cpe_ta.hal.base import OutletState


class HTTPPdu:
    """Real PDU driver using HTTP REST API.

    Compatible with PDUs that expose a REST interface (e.g. APC, Raritan,
    Vertiv) over HTTP/HTTPS.

    Raises
    ------
    NotImplementedError
        All methods — connect to real hardware to implement.
    """

    def __init__(
        self,
        host: str,
        port: int = 80,
        username: str = "admin",
        password: str = "",
        use_https: bool = False,
    ) -> None:
        scheme = "https" if use_https else "http"
        self._base_url = f"{scheme}://{host}:{port}"
        self._auth = (username, password)
        # Suppress unused import warning — requests is used by real implementation
        self._session = requests.Session()
        self._session.auth = self._auth

    def power_on(self, outlet_id: str) -> None:
        # TODO: POST /api/outlets/<outlet_id>/on or vendor-specific endpoint
        raise NotImplementedError("HTTP PDU driver: connect to real hardware")

    def power_off(self, outlet_id: str) -> None:
        # TODO: POST /api/outlets/<outlet_id>/off or vendor-specific endpoint
        raise NotImplementedError("HTTP PDU driver: connect to real hardware")

    def power_cycle(self, outlet_id: str, delay_s: float = 2.0) -> None:
        # TODO: POST /api/outlets/<outlet_id>/cycle with delay parameter
        raise NotImplementedError("HTTP PDU driver: connect to real hardware")

    def get_outlet_state(self, outlet_id: str) -> OutletState:
        # TODO: GET /api/outlets/<outlet_id> and parse JSON response
        raise NotImplementedError("HTTP PDU driver: connect to real hardware")
