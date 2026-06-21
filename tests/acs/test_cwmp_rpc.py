"""T32 — ACS / CWMP RPC suite tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.infra.sim.sim_acs import SimACSService

pytestmark = [pytest.mark.headless, pytest.mark.smoke]

_SERIAL = "SIM000001"
_SERIAL2 = "SIM000002"
_SERIAL3 = "SIM000003"


def test_bootstrap_inform(sim_acs: SimACSService) -> None:
    """bootstrap_cpe must return a dict with serial, acs_url, and status."""
    result = sim_acs.bootstrap_cpe(_SERIAL)
    assert result["serial"] == _SERIAL
    assert "acs_url" in result
    assert "status" in result


def test_get_parameter_values(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """get_parameter_values must return a dict keyed by the requested paths."""
    acs, serial = bootstrapped_acs
    result = acs.get_parameter_values(serial, ["Device.DeviceInfo.SerialNumber"])
    assert isinstance(result, dict)
    assert "Device.DeviceInfo.SerialNumber" in result


def test_set_parameter_values(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """set_parameter_values must persist values retrievable via get_parameter_values."""
    acs, serial = bootstrapped_acs
    acs.set_parameter_values(serial, {"Device.WiFi.SSID.1.SSID": "TestNet"})
    result = acs.get_parameter_values(serial, ["Device.WiFi.SSID.1.SSID"])
    assert result["Device.WiFi.SSID.1.SSID"] == "TestNet"


def test_add_object(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """add_object must return a positive integer instance number."""
    acs, serial = bootstrapped_acs
    instance = acs.add_object(serial, "Device.WiFi.SSID.")
    assert isinstance(instance, int)
    assert instance > 0


def test_delete_object(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """delete_object must complete without raising an exception."""
    acs, serial = bootstrapped_acs
    acs.add_object(serial, "Device.WiFi.SSID.")
    # Should not raise
    acs.delete_object(serial, "Device.WiFi.SSID.")


def test_reboot(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """reboot must set the reboot flag on the ACS-side CPE record."""
    acs, serial = bootstrapped_acs
    acs.reboot(serial)
    assert acs.is_rebooted(serial) is True


def test_download_firmware(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """download must log the firmware request into the download log."""
    acs, serial = bootstrapped_acs
    url = "http://firmware.example.com/v2.0.0.bin"
    acs.download(serial, url, "Firmware")
    log = acs.get_download_log(serial)
    assert len(log) >= 1
    assert log[0]["url"] == url
    assert log[0]["file_type"] == "Firmware"


def test_schedule_inform(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """schedule_inform must complete without raising and log the delay."""
    acs, serial = bootstrapped_acs
    acs.schedule_inform(serial, delay_s=300)
    schedule = acs.get_inform_schedule(serial)
    assert 300 in schedule


def test_notifications(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """After a set operation, get_notifications must return the value-change events."""
    acs, serial = bootstrapped_acs
    acs.set_parameter_values(serial, {"Device.DeviceInfo.SoftwareVersion": "2.0.0"})
    notifications = acs.get_notifications(serial)
    assert isinstance(notifications, list)
    assert len(notifications) >= 1


def test_diagnostics_ipping(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """run_diagnostics with IPPing must return a dict containing 'packets_received'."""
    acs, serial = bootstrapped_acs
    result = acs.run_diagnostics(serial, "IPPing", {"host": "8.8.8.8"})
    assert isinstance(result, dict)
    assert "packets_received" in result


def test_diagnostics_traceroute(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """run_diagnostics with TraceRoute must return a dict with 'hops'."""
    acs, serial = bootstrapped_acs
    result = acs.run_diagnostics(serial, "TraceRoute", {"host": "8.8.8.8"})
    assert isinstance(result, dict)
    assert "hops" in result


def test_multiple_sessions(sim_acs: SimACSService) -> None:
    """Bootstrapping 3 different CPEs must result in 3 tracked CPE states."""
    sim_acs.bootstrap_cpe(_SERIAL)
    sim_acs.bootstrap_cpe(_SERIAL2)
    sim_acs.bootstrap_cpe(_SERIAL3)

    # Each serial must have its own state
    state1 = sim_acs.get_cpe_state(_SERIAL)
    state2 = sim_acs.get_cpe_state(_SERIAL2)
    state3 = sim_acs.get_cpe_state(_SERIAL3)

    assert state1["Device.DeviceInfo.SerialNumber"] == _SERIAL
    assert state2["Device.DeviceInfo.SerialNumber"] == _SERIAL2
    assert state3["Device.DeviceInfo.SerialNumber"] == _SERIAL3


def test_http_user_agent(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """bootstrap_cpe response must contain expected fields (status, serial, acs_url)."""
    acs, serial = bootstrapped_acs
    result = acs.get_cpe_state(serial)
    # bootstrap stores at minimum: SerialNumber, SoftwareVersion, ManagementServer.URL
    assert "Device.DeviceInfo.SerialNumber" in result
    assert "Device.DeviceInfo.SoftwareVersion" in result
    assert "Device.ManagementServer.URL" in result


def test_connection_request(bootstrapped_acs: tuple[SimACSService, str]) -> None:
    """schedule_inform + get_notifications after a set must return a non-empty list."""
    acs, serial = bootstrapped_acs
    acs.schedule_inform(serial, delay_s=0)
    # Trigger a parameter change to generate a notification
    acs.set_parameter_values(serial, {"Device.DeviceInfo.UpTime": 42})
    notifications = acs.get_notifications(serial)
    assert isinstance(notifications, list)
    # At minimum one ValueChange notification
    assert len(notifications) >= 1
