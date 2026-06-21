"""Tests for all infrastructure simulators — headless, no hardware required."""
from __future__ import annotations

import pytest

from cpe_ta.infra.base import (
    ACSService,
    DHCPLease,
    DHCPService,
    FileServer,
    NTPService,
    RADIUSService,
    SIPService,
    TrafficEndpoint,
    TrafficResult,
)
from cpe_ta.infra.sim.sim_acs import SimACSService
from cpe_ta.infra.sim.sim_dhcp import SimDHCPService
from cpe_ta.infra.sim.sim_fileserver import SimFileServer
from cpe_ta.infra.sim.sim_ntp import SimNTPService
from cpe_ta.infra.sim.sim_radius import SimRADIUSService
from cpe_ta.infra.sim.sim_sip import SimSIPService
from cpe_ta.infra.sim.sim_traffic import SimTrafficEndpoint

# ===========================================================================
# SimACSService
# ===========================================================================


@pytest.fixture()
def acs() -> SimACSService:
    return SimACSService()


@pytest.mark.headless
class TestSimACS:
    def test_isinstance_acs_service(self, acs: SimACSService) -> None:
        assert isinstance(acs, ACSService)

    def test_bootstrap_cpe_returns_status(self, acs: SimACSService) -> None:
        result = acs.bootstrap_cpe("SN-001")
        assert result["status"] == "bootstrapped"
        assert result["serial"] == "SN-001"

    def test_bootstrap_idempotent(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-001")
        result = acs.bootstrap_cpe("SN-001")
        assert result["status"] == "bootstrapped"

    def test_get_parameter_values_returns_defaults(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-002")
        vals = acs.get_parameter_values("SN-002", ["Device.DeviceInfo.SerialNumber"])
        assert vals["Device.DeviceInfo.SerialNumber"] == "SN-002"

    def test_get_parameter_values_missing_key_returns_none(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-003")
        vals = acs.get_parameter_values("SN-003", ["Device.Unknown.Param"])
        assert vals["Device.Unknown.Param"] is None

    def test_set_parameter_values_stores_value(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-004")
        acs.set_parameter_values("SN-004", {"Device.DeviceInfo.SoftwareVersion": "2.0.0"})
        vals = acs.get_parameter_values("SN-004", ["Device.DeviceInfo.SoftwareVersion"])
        assert vals["Device.DeviceInfo.SoftwareVersion"] == "2.0.0"

    def test_set_parameter_values_generates_notifications(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-005")
        acs.set_parameter_values("SN-005", {"Device.WiFi.SSID.1.SSID": "NewSSID"})
        notes = acs.get_notifications("SN-005")
        assert len(notes) == 1
        assert notes[0]["type"] == "ValueChange"
        assert notes[0]["path"] == "Device.WiFi.SSID.1.SSID"
        assert notes[0]["new"] == "NewSSID"

    def test_get_notifications_flushes_queue(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-006")
        acs.set_parameter_values("SN-006", {"Device.Firewall.Enable": False})
        acs.get_notifications("SN-006")  # flush
        assert acs.get_notifications("SN-006") == []

    def test_no_notification_when_value_unchanged(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-007")
        acs.set_parameter_values("SN-007", {"Device.DeviceInfo.SoftwareVersion": "1.0.0"})
        notes = acs.get_notifications("SN-007")
        assert len(notes) == 0

    def test_add_object_returns_index(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-008")
        idx = acs.add_object("SN-008", "Device.NAT.PortMapping")
        assert idx == 1
        idx2 = acs.add_object("SN-008", "Device.NAT.PortMapping")
        assert idx2 == 2

    def test_delete_object_removes_keys(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-009")
        acs.add_object("SN-009", "Device.NAT.PortMapping")
        state_before = acs.get_cpe_state("SN-009")
        assert any("Device.NAT.PortMapping" in k for k in state_before)
        acs.delete_object("SN-009", "Device.NAT.PortMapping")
        state_after = acs.get_cpe_state("SN-009")
        assert not any("Device.NAT.PortMapping" in k for k in state_after)

    def test_reboot_sets_flag(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-010")
        assert not acs.is_rebooted("SN-010")
        acs.reboot("SN-010")
        assert acs.is_rebooted("SN-010")

    def test_download_logs_entry(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-011")
        acs.download("SN-011", "http://fw.example.com/2.0.bin", "1 Firmware Upgrade Image")
        log = acs.get_download_log("SN-011")
        assert len(log) == 1
        assert log[0]["url"] == "http://fw.example.com/2.0.bin"
        assert log[0]["file_type"] == "1 Firmware Upgrade Image"

    def test_schedule_inform_logs_delay(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-012")
        acs.schedule_inform("SN-012", 30)
        acs.schedule_inform("SN-012", 60)
        schedule = acs.get_inform_schedule("SN-012")
        assert schedule == [30, 60]

    def test_run_diagnostics_ipping(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-013")
        result = acs.run_diagnostics("SN-013", "IPPing", {"host": "8.8.8.8"})
        assert result["diag_type"] == "IPPing"
        assert result["packets_sent"] == 4
        assert result["packets_received"] == 4
        assert result["average_response_time_ms"] == 5.0

    def test_run_diagnostics_traceroute(self, acs: SimACSService) -> None:
        acs.bootstrap_cpe("SN-014")
        result = acs.run_diagnostics("SN-014", "TraceRoute", {})
        assert result["success"] is True

    def test_auto_register_on_get(self, acs: SimACSService) -> None:
        """Unregistered serial is auto-bootstrapped on first access."""
        vals = acs.get_parameter_values("SN-AUTO", ["Device.DeviceInfo.SerialNumber"])
        assert vals["Device.DeviceInfo.SerialNumber"] == "SN-AUTO"


# ===========================================================================
# SimDHCPService
# ===========================================================================


@pytest.fixture()
def dhcp() -> SimDHCPService:
    return SimDHCPService()


@pytest.mark.headless
class TestSimDHCP:
    def test_isinstance_dhcp_service(self, dhcp: SimDHCPService) -> None:
        assert isinstance(dhcp, DHCPService)

    def test_set_pool_stores_config(self, dhcp: SimDHCPService) -> None:
        dhcp.set_pool("192.168.1.0/24", "192.168.1.100", "192.168.1.200", lease_time_s=3600)
        cfg = dhcp.get_pool_config()
        assert cfg["subnet"] == "192.168.1.0/24"
        assert cfg["start"] == "192.168.1.100"
        assert cfg["end"] == "192.168.1.200"
        assert cfg["lease_time_s"] == 3600

    def test_add_static_lease_appears_in_get_leases(self, dhcp: SimDHCPService) -> None:
        dhcp.add_static_lease("aa:bb:cc:dd:ee:ff", "192.168.1.50")
        leases = dhcp.get_leases()
        assert len(leases) == 1
        lease = leases[0]
        assert isinstance(lease, DHCPLease)
        assert lease.mac == "aa:bb:cc:dd:ee:ff"
        assert lease.ip == "192.168.1.50"

    def test_add_multiple_static_leases(self, dhcp: SimDHCPService) -> None:
        dhcp.add_static_lease("11:22:33:44:55:66", "10.0.0.10")
        dhcp.add_static_lease("aa:bb:cc:00:11:22", "10.0.0.11")
        assert len(dhcp.get_leases()) == 2

    def test_set_option_stores_value(self, dhcp: SimDHCPService) -> None:
        dhcp.set_option(6, "8.8.8.8")  # DNS server
        dhcp.set_option(3, "192.168.1.1")  # Router
        opts = dhcp.get_options()
        assert opts[6] == "8.8.8.8"
        assert opts[3] == "192.168.1.1"

    def test_flush_leases_clears_all(self, dhcp: SimDHCPService) -> None:
        dhcp.add_static_lease("11:22:33:44:55:66", "10.0.0.5")
        dhcp.flush_leases()
        assert dhcp.get_leases() == []

    def test_get_leases_empty_initially(self, dhcp: SimDHCPService) -> None:
        assert dhcp.get_leases() == []


# ===========================================================================
# SimTrafficEndpoint
# ===========================================================================


@pytest.fixture()
def traffic() -> SimTrafficEndpoint:
    return SimTrafficEndpoint()


@pytest.mark.headless
class TestSimTraffic:
    def test_isinstance_traffic_endpoint(self, traffic: SimTrafficEndpoint) -> None:
        assert isinstance(traffic, TrafficEndpoint)

    def test_server_not_running_initially(self, traffic: SimTrafficEndpoint) -> None:
        assert traffic.server_running is False

    def test_start_server_sets_flag(self, traffic: SimTrafficEndpoint) -> None:
        traffic.start_server(port=5201, protocol="tcp")
        assert traffic.server_running is True

    def test_stop_server_clears_flag(self, traffic: SimTrafficEndpoint) -> None:
        traffic.start_server()
        traffic.stop_server()
        assert traffic.server_running is False

    def test_run_client_returns_traffic_result(self, traffic: SimTrafficEndpoint) -> None:
        result = traffic.run_client("10.0.0.1", duration_s=10)
        assert isinstance(result, TrafficResult)

    def test_run_client_deterministic_throughput(self, traffic: SimTrafficEndpoint) -> None:
        r1 = traffic.run_client("10.0.0.1", 10)
        r2 = traffic.run_client("10.0.0.2", 10)
        assert r1.throughput_mbps == r2.throughput_mbps == 900.0

    def test_run_client_default_latency(self, traffic: SimTrafficEndpoint) -> None:
        result = traffic.run_client("10.0.0.1", 10)
        assert result.latency_ms == 1.0

    def test_run_client_default_packet_loss(self, traffic: SimTrafficEndpoint) -> None:
        result = traffic.run_client("10.0.0.1", 10)
        assert result.packet_loss_percent == 0.0

    def test_configurable_throughput(self) -> None:
        ep = SimTrafficEndpoint(configurable_throughput=500.0)
        result = ep.run_client("10.0.0.1", 10)
        assert result.throughput_mbps == 500.0

    def test_configurable_packet_loss(self) -> None:
        ep = SimTrafficEndpoint(configurable_packet_loss=1.5)
        result = ep.run_client("10.0.0.1", 10)
        assert result.packet_loss_percent == 1.5

    def test_udp_protocol_still_returns_result(self, traffic: SimTrafficEndpoint) -> None:
        result = traffic.run_client("10.0.0.1", 10, protocol="udp", parallel=4)
        assert result.throughput_mbps == 900.0


# ===========================================================================
# SimRADIUSService
# ===========================================================================


@pytest.fixture()
def radius() -> SimRADIUSService:
    return SimRADIUSService()


@pytest.mark.headless
class TestSimRADIUS:
    def test_isinstance_radius_service(self, radius: SimRADIUSService) -> None:
        assert isinstance(radius, RADIUSService)

    def test_add_user_then_authenticate_success(self, radius: SimRADIUSService) -> None:
        radius.add_user("alice", "secret123")
        assert radius.authenticate("alice", "secret123") is True

    def test_authenticate_wrong_password(self, radius: SimRADIUSService) -> None:
        radius.add_user("bob", "correct")
        assert radius.authenticate("bob", "wrong") is False

    def test_authenticate_nonexistent_user(self, radius: SimRADIUSService) -> None:
        assert radius.authenticate("ghost", "pass") is False

    def test_remove_user_prevents_auth(self, radius: SimRADIUSService) -> None:
        radius.add_user("carol", "pass")
        radius.remove_user("carol")
        assert radius.authenticate("carol", "pass") is False
        assert not radius.has_user("carol")

    def test_add_user_with_attributes(self, radius: SimRADIUSService) -> None:
        radius.add_user("dave", "pass", attributes={"Service-Type": "Framed-User"})
        attrs = radius.get_user_attributes("dave")
        assert attrs["Service-Type"] == "Framed-User"

    def test_add_user_without_attributes_empty_dict(self, radius: SimRADIUSService) -> None:
        radius.add_user("eve", "pass")
        assert radius.get_user_attributes("eve") == {}

    def test_remove_nonexistent_user_is_noop(self, radius: SimRADIUSService) -> None:
        radius.remove_user("nobody")  # should not raise


# ===========================================================================
# SimSIPService
# ===========================================================================


@pytest.fixture()
def sip() -> SimSIPService:
    return SimSIPService()


@pytest.mark.headless
class TestSimSIP:
    def test_isinstance_sip_service(self, sip: SimSIPService) -> None:
        assert isinstance(sip, SIPService)

    def test_register_stores_extension(self, sip: SimSIPService) -> None:
        sip.register("1001", "pass")
        assert sip.is_registered("1001")

    def test_register_multiple_extensions(self, sip: SimSIPService) -> None:
        sip.register("1001", "p1")
        sip.register("1002", "p2")
        assert sip.is_registered("1001")
        assert sip.is_registered("1002")

    def test_make_call_returns_success(self, sip: SimSIPService) -> None:
        sip.register("1001", "p1")
        sip.register("1002", "p2")
        result = sip.make_call("1001", "1002", duration_s=5.0)
        assert result.success is True

    def test_make_call_duration_propagated(self, sip: SimSIPService) -> None:
        result = sip.make_call("1001", "1002", duration_s=10.0)
        assert result.duration_s == 10.0

    def test_make_call_codec_and_mos(self, sip: SimSIPService) -> None:
        result = sip.make_call("1001", "1002")
        assert result.codec == "G.711"
        assert result.mos_score == 4.2

    def test_hangup_removes_active_call(self, sip: SimSIPService) -> None:
        sip.make_call("1001", "1002")
        calls = sip.get_active_calls()
        call_id = next(iter(calls))
        sip.hangup(call_id)
        assert call_id not in sip.get_active_calls()

    def test_hangup_nonexistent_call_is_noop(self, sip: SimSIPService) -> None:
        sip.hangup("nonexistent-call-id")  # should not raise

    def test_multiple_calls_increment_counter(self, sip: SimSIPService) -> None:
        sip.make_call("1001", "1002")
        sip.make_call("1001", "1003")
        assert len(sip.get_active_calls()) == 2


# ===========================================================================
# SimNTPService
# ===========================================================================


@pytest.fixture()
def ntp() -> SimNTPService:
    return SimNTPService()


@pytest.mark.headless
class TestSimNTP:
    def test_isinstance_ntp_service(self, ntp: SimNTPService) -> None:
        assert isinstance(ntp, NTPService)

    def test_get_time_returns_fixed_timestamp(self, ntp: SimNTPService) -> None:
        assert ntp.get_time() == 1750000000.0

    def test_get_time_deterministic(self, ntp: SimNTPService) -> None:
        t1 = ntp.get_time()
        t2 = ntp.get_time()
        assert t1 == t2

    def test_is_synchronized_true_by_default(self, ntp: SimNTPService) -> None:
        assert ntp.is_synchronized() is True

    def test_custom_fixed_time(self) -> None:
        custom = SimNTPService(fixed_time=1000000.0)
        assert custom.get_time() == 1000000.0

    def test_custom_unsynchronized(self) -> None:
        unsync = SimNTPService(synchronized=False)
        assert unsync.is_synchronized() is False


# ===========================================================================
# SimFileServer
# ===========================================================================


@pytest.fixture()
def fs() -> SimFileServer:
    return SimFileServer()


@pytest.mark.headless
class TestSimFileServer:
    def test_isinstance_file_server(self, fs: SimFileServer) -> None:
        assert isinstance(fs, FileServer)

    def test_put_file_returns_url(self, fs: SimFileServer) -> None:
        url = fs.put_file("firmware.bin", b"\x00\x01\x02")
        assert url == "http://sim-fileserver.local/firmware.bin"

    def test_put_file_stores_content(self, fs: SimFileServer) -> None:
        content = b"test content"
        fs.put_file("config.xml", content)
        assert fs.get_content("config.xml") == content

    def test_get_url_returns_correct_url(self, fs: SimFileServer) -> None:
        fs.put_file("test.bin", b"data")
        url = fs.get_url("test.bin")
        assert url == "http://sim-fileserver.local/test.bin"

    def test_delete_file_removes_it(self, fs: SimFileServer) -> None:
        fs.put_file("old.bin", b"data")
        fs.delete_file("old.bin")
        assert not fs.has_file("old.bin")
        assert fs.get_content("old.bin") is None

    def test_delete_nonexistent_file_is_noop(self, fs: SimFileServer) -> None:
        fs.delete_file("does-not-exist.bin")  # should not raise

    def test_list_files_empty_initially(self, fs: SimFileServer) -> None:
        assert fs.list_files() == []

    def test_list_files_after_put(self, fs: SimFileServer) -> None:
        fs.put_file("a.bin", b"a")
        fs.put_file("b.bin", b"b")
        files = fs.list_files()
        assert "a.bin" in files
        assert "b.bin" in files
        assert len(files) == 2

    def test_has_file_false_for_missing(self, fs: SimFileServer) -> None:
        assert not fs.has_file("missing.bin")

    def test_has_file_true_after_put(self, fs: SimFileServer) -> None:
        fs.put_file("present.bin", b"x")
        assert fs.has_file("present.bin")

    def test_custom_base_url(self) -> None:
        custom = SimFileServer(base_url="http://my-server.local:8080")
        url = custom.put_file("fw.bin", b"data")
        assert url == "http://my-server.local:8080/fw.bin"
