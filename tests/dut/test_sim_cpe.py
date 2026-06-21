"""Tests for SimCPE — fully deterministic, no hardware required."""
from __future__ import annotations

import pytest

from cpe_ta.core.errors import DUTError
from cpe_ta.dut.base import CPE
from cpe_ta.dut.capabilities import CapabilitySet, Technology, WiFiBand
from cpe_ta.dut.sim.sim_cpe import SimCPE

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sim() -> SimCPE:
    return SimCPE()


@pytest.fixture()
def custom_sim() -> SimCPE:
    caps = CapabilitySet(
        lan_ports=2,
        wan_ports=1,
        wifi_bands=[WiFiBand.BAND_2_4],
        technologies=[Technology.DOCSIS],
        has_voip=True,
        voip_ports=2,
    )
    return SimCPE(dut_id="sim-docsis-01", caps=caps)


# ---------------------------------------------------------------------------
# T15-01: Protocol check
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_isinstance_cpe_protocol(sim: SimCPE) -> None:
    """SimCPE must satisfy the CPE Protocol at runtime."""
    assert isinstance(sim, CPE)


# ---------------------------------------------------------------------------
# T15-02: dut_id and capabilities
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_dut_id_default(sim: SimCPE) -> None:
    assert sim.dut_id == "sim-cpe-01"


@pytest.mark.headless
def test_dut_id_custom(custom_sim: SimCPE) -> None:
    assert custom_sim.dut_id == "sim-docsis-01"


@pytest.mark.headless
def test_capabilities_default(sim: SimCPE) -> None:
    caps = sim.capabilities
    assert caps.lan_ports == 4
    assert caps.wan_ports == 1
    assert WiFiBand.BAND_2_4 in caps.wifi_bands
    assert WiFiBand.BAND_5 in caps.wifi_bands
    assert caps.supports(Technology.DSL)
    assert caps.supports(Technology.FWA)
    assert not caps.supports(Technology.DOCSIS)
    assert caps.supports_wpa3 is True


@pytest.mark.headless
def test_capabilities_custom(custom_sim: SimCPE) -> None:
    caps = custom_sim.capabilities
    assert caps.lan_ports == 2
    assert caps.has_voip is True
    assert caps.voip_ports == 2
    assert caps.supports(Technology.DOCSIS)
    assert caps.has_band(WiFiBand.BAND_2_4)
    assert not caps.has_band(WiFiBand.BAND_5)


# ---------------------------------------------------------------------------
# T15-03: factory_reset
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_factory_reset_restores_defaults(sim: SimCPE) -> None:
    sim.set_parameter("Device.WiFi.SSID.1.SSID", "CustomSSID")
    assert sim.get_parameter("Device.WiFi.SSID.1.SSID") == "CustomSSID"

    sim.factory_reset()

    assert sim.get_parameter("Device.WiFi.SSID.1.SSID") == "SimNet"


@pytest.mark.headless
def test_factory_reset_increments_reboot_count(sim: SimCPE) -> None:
    before = sim.reboot_count
    sim.factory_reset()
    assert sim.reboot_count == before + 1


@pytest.mark.headless
def test_factory_reset_restores_wan_ip(sim: SimCPE) -> None:
    sim.power_off()
    sim.power_on()
    sim.factory_reset()
    assert sim.get_wan_ip() == "100.64.0.1"


# ---------------------------------------------------------------------------
# T15-04: power_cycle
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_power_off_clears_wan_ip(sim: SimCPE) -> None:
    sim.power_off()
    assert sim.get_wan_ip() is None


@pytest.mark.headless
def test_power_on_restores_wan_ip(sim: SimCPE) -> None:
    sim.power_off()
    sim.power_on()
    assert sim.get_wan_ip() == "100.64.0.1"


@pytest.mark.headless
def test_power_cycle_increments_reboot_count(sim: SimCPE) -> None:
    before = sim.reboot_count
    sim.power_cycle()
    assert sim.reboot_count == before + 1


@pytest.mark.headless
def test_power_cycle_leaves_dut_powered_on(sim: SimCPE) -> None:
    sim.power_cycle()
    assert sim.get_wan_ip() == "100.64.0.1"


# ---------------------------------------------------------------------------
# T15-05: config_backup + config_restore
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_backup_restore_roundtrip(sim: SimCPE) -> None:
    backup = sim.config_backup()

    # Modify state
    sim.set_parameter("Device.WiFi.SSID.1.SSID", "Modified")
    sim.set_parameter("Device.Firewall.Enable", False)

    # Restore
    sim.config_restore(backup)

    assert sim.get_parameter("Device.WiFi.SSID.1.SSID") == "SimNet"
    assert sim.get_parameter("Device.Firewall.Enable") is True


@pytest.mark.headless
def test_backup_is_independent_copy(sim: SimCPE) -> None:
    backup = sim.config_backup()
    backup["Device.WiFi.SSID.1.SSID"] = "Mutated"
    # Original should be unaffected
    assert sim.get_parameter("Device.WiFi.SSID.1.SSID") == "SimNet"


# ---------------------------------------------------------------------------
# T15-06: fw_flash + fw_rollback
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_fw_flash_updates_version(sim: SimCPE) -> None:
    sim.fw_flash("/firmware/2.5.1.bin")
    assert sim.get_parameter("Device.DeviceInfo.SoftwareVersion") == "2.5.1"


@pytest.mark.headless
def test_fw_flash_increments_reboot_count(sim: SimCPE) -> None:
    before = sim.reboot_count
    sim.fw_flash("/firmware/2.5.1.bin")
    assert sim.reboot_count == before + 1


@pytest.mark.headless
def test_fw_rollback_restores_original_version(sim: SimCPE) -> None:
    sim.fw_flash("/firmware/2.5.1.bin")
    sim.fw_rollback()
    assert sim.get_parameter("Device.DeviceInfo.SoftwareVersion") == "1.0.0"


@pytest.mark.headless
def test_fw_rollback_increments_reboot_count(sim: SimCPE) -> None:
    before = sim.reboot_count
    sim.fw_rollback()
    assert sim.reboot_count == before + 1


# ---------------------------------------------------------------------------
# T15-07: get/set_parameter
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_get_parameter_existing_key(sim: SimCPE) -> None:
    assert sim.get_parameter("Device.DeviceInfo.Manufacturer") == "SimVendor"


@pytest.mark.headless
def test_get_parameter_missing_key_returns_none(sim: SimCPE) -> None:
    assert sim.get_parameter("Device.NonExistent.Param") is None


@pytest.mark.headless
def test_set_parameter_stores_value(sim: SimCPE) -> None:
    sim.set_parameter("Device.WiFi.Radio.1.Channel", 11)
    assert sim.get_parameter("Device.WiFi.Radio.1.Channel") == 11


@pytest.mark.headless
def test_set_parameter_new_key(sim: SimCPE) -> None:
    sim.set_parameter("Device.Custom.NewParam", "hello")
    assert sim.get_parameter("Device.Custom.NewParam") == "hello"


@pytest.mark.headless
def test_get_parameter_powered_off_raises_dut_error(sim: SimCPE) -> None:
    sim.power_off()
    with pytest.raises(DUTError, match="powered off"):
        sim.get_parameter("Device.DeviceInfo.SoftwareVersion")


@pytest.mark.headless
def test_set_parameter_powered_off_raises_dut_error(sim: SimCPE) -> None:
    sim.power_off()
    with pytest.raises(DUTError, match="powered off"):
        sim.set_parameter("Device.WiFi.SSID.1.SSID", "Fail")


# ---------------------------------------------------------------------------
# T15-08: cwmp_inform
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_cwmp_inform_structure(sim: SimCPE) -> None:
    info = sim.cwmp_inform()
    assert info["manufacturer"] == "SimVendor"
    assert info["model"] == "SimCPE-1000"
    assert info["serial"] == "SIM000001"
    assert info["sw_version"] == "1.0.0"
    assert info["session_id"] == 1


@pytest.mark.headless
def test_cwmp_inform_increments_session_id(sim: SimCPE) -> None:
    sim.cwmp_inform()
    second = sim.cwmp_inform()
    assert second["session_id"] == 2


# ---------------------------------------------------------------------------
# T15-09: get_console_metrics
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_get_console_metrics_keys(sim: SimCPE) -> None:
    metrics = sim.get_console_metrics()
    assert "cpu_percent" in metrics
    assert "ram_percent" in metrics


@pytest.mark.headless
def test_get_console_metrics_defaults(sim: SimCPE) -> None:
    metrics = sim.get_console_metrics()
    assert metrics["cpu_percent"] == 5.0
    assert metrics["ram_percent"] == 20.0


@pytest.mark.headless
def test_simulate_memory_leak(sim: SimCPE) -> None:
    sim.simulate_memory_leak(10.0)
    assert sim.get_console_metrics()["ram_percent"] == 30.0


@pytest.mark.headless
def test_simulate_memory_leak_capped_at_100(sim: SimCPE) -> None:
    sim.simulate_memory_leak(200.0)
    assert sim.get_console_metrics()["ram_percent"] == 100.0


@pytest.mark.headless
def test_simulate_cpu_spike(sim: SimCPE) -> None:
    sim.simulate_cpu_spike(90.0)
    assert sim.get_console_metrics()["cpu_percent"] == 90.0


@pytest.mark.headless
def test_simulate_cpu_spike_capped_at_100(sim: SimCPE) -> None:
    sim.simulate_cpu_spike(150.0)
    assert sim.get_console_metrics()["cpu_percent"] == 100.0


# ---------------------------------------------------------------------------
# T15-10: get_wan_ip
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_get_wan_ip_default(sim: SimCPE) -> None:
    assert sim.get_wan_ip() == "100.64.0.1"


@pytest.mark.headless
def test_get_wan_ip_powered_off_returns_none(sim: SimCPE) -> None:
    sim.power_off()
    assert sim.get_wan_ip() is None
