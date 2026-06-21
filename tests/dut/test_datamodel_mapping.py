"""Tests for TR-098 ↔ TR-181 bidirectional parameter mapping."""
from __future__ import annotations

import pytest

from cpe_ta.dut.datamodel import _PARAM_MAP, DataModel, normalize_path, translate_path


@pytest.mark.headless
class TestTranslatePathTR098toTR181:
    """TR-098 → TR-181 forward translation for all mapped paths."""

    @pytest.mark.parametrize("tr098,tr181", _PARAM_MAP)
    def test_forward_all_mapped_paths(self, tr098: str, tr181: str) -> None:
        result = translate_path(tr098, DataModel.TR098, DataModel.TR181)
        assert result == tr181

    def test_software_version(self) -> None:
        result = translate_path(
            "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
            DataModel.TR098,
            DataModel.TR181,
        )
        assert result == "Device.DeviceInfo.SoftwareVersion"

    def test_wan_ip_address(self) -> None:
        result = translate_path(
            "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.ExternalIPAddress",
            DataModel.TR098,
            DataModel.TR181,
        )
        assert result == "Device.IP.Interface.1.IPv4Address.1.IPAddress"

    def test_management_server_url(self) -> None:
        result = translate_path(
            "InternetGatewayDevice.ManagementServer.URL",
            DataModel.TR098,
            DataModel.TR181,
        )
        assert result == "Device.ManagementServer.URL"


@pytest.mark.headless
class TestTranslatePathTR181toTR098:
    """TR-181 → TR-098 reverse translation (roundtrip)."""

    @pytest.mark.parametrize("tr098,tr181", _PARAM_MAP)
    def test_reverse_all_mapped_paths(self, tr098: str, tr181: str) -> None:
        result = translate_path(tr181, DataModel.TR181, DataModel.TR098)
        assert result == tr098

    def test_roundtrip_software_version(self) -> None:
        original = "InternetGatewayDevice.DeviceInfo.SoftwareVersion"
        tr181 = translate_path(original, DataModel.TR098, DataModel.TR181)
        roundtrip = translate_path(tr181, DataModel.TR181, DataModel.TR098)
        assert roundtrip == original

    def test_roundtrip_ssid(self) -> None:
        original = "InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID"
        tr181 = translate_path(original, DataModel.TR098, DataModel.TR181)
        roundtrip = translate_path(tr181, DataModel.TR181, DataModel.TR098)
        assert roundtrip == original

    def test_roundtrip_all_paths(self) -> None:
        for tr098, _tr181 in _PARAM_MAP:
            assert translate_path(
                translate_path(tr098, DataModel.TR098, DataModel.TR181),
                DataModel.TR181,
                DataModel.TR098,
            ) == tr098


@pytest.mark.headless
class TestTranslatePathSameModel:
    """translate_path with same source and target returns path unchanged."""

    def test_same_model_tr098(self) -> None:
        path = "InternetGatewayDevice.DeviceInfo.SoftwareVersion"
        assert translate_path(path, DataModel.TR098, DataModel.TR098) == path

    def test_same_model_tr181(self) -> None:
        path = "Device.DeviceInfo.SoftwareVersion"
        assert translate_path(path, DataModel.TR181, DataModel.TR181) == path


@pytest.mark.headless
class TestTranslatePathUnknown:
    """Unknown paths raise KeyError."""

    def test_unknown_tr098_path_raises(self) -> None:
        with pytest.raises(KeyError, match="No mapping for"):
            translate_path(
                "InternetGatewayDevice.Unknown.Param",
                DataModel.TR098,
                DataModel.TR181,
            )

    def test_unknown_tr181_path_raises(self) -> None:
        with pytest.raises(KeyError, match="No mapping for"):
            translate_path(
                "Device.Unknown.Param",
                DataModel.TR181,
                DataModel.TR098,
            )

    def test_completely_foreign_path_raises(self) -> None:
        with pytest.raises(KeyError):
            translate_path("SomeOther.Path", DataModel.TR098, DataModel.TR181)


@pytest.mark.headless
class TestNormalizePath:
    """normalize_path detects prefix and normalizes to target model."""

    def test_igd_prefix_normalizes_to_tr181(self) -> None:
        result = normalize_path("InternetGatewayDevice.DeviceInfo.SoftwareVersion")
        assert result == "Device.DeviceInfo.SoftwareVersion"

    def test_device_prefix_normalizes_to_tr181_noop(self) -> None:
        # Device.* → TR181 when target is TR181: same path returned
        result = normalize_path(
            "Device.DeviceInfo.SoftwareVersion",
            DataModel.TR181,
        )
        assert result == "Device.DeviceInfo.SoftwareVersion"

    def test_igd_prefix_normalize_to_tr098_noop(self) -> None:
        # IGD → TR098: same path returned (translate_path same-model)
        result = normalize_path(
            "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
            DataModel.TR098,
        )
        assert result == "InternetGatewayDevice.DeviceInfo.SoftwareVersion"

    def test_device_prefix_normalize_to_tr098(self) -> None:
        result = normalize_path(
            "Device.DeviceInfo.SoftwareVersion",
            DataModel.TR098,
        )
        assert result == "InternetGatewayDevice.DeviceInfo.SoftwareVersion"

    def test_unknown_prefix_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Cannot detect data model"):
            normalize_path("SomeRandom.Path.Here")

    def test_normalize_wan_ip(self) -> None:
        result = normalize_path(
            "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.ExternalIPAddress"
        )
        assert result == "Device.IP.Interface.1.IPv4Address.1.IPAddress"
