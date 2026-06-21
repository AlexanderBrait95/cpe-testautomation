"""TR-098 (InternetGatewayDevice) ↔ TR-181 (Device:2) Bidirectional Mapping."""
from __future__ import annotations

from enum import Enum


class DataModel(Enum):
    TR098 = "tr098"  # InternetGatewayDevice.*
    TR181 = "tr181"  # Device.*


# Mapping table: (tr098_path, tr181_path)
_PARAM_MAP: list[tuple[str, str]] = [
    (
        "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
        "Device.DeviceInfo.SoftwareVersion",
    ),
    (
        "InternetGatewayDevice.DeviceInfo.HardwareVersion",
        "Device.DeviceInfo.HardwareVersion",
    ),
    (
        "InternetGatewayDevice.DeviceInfo.Manufacturer",
        "Device.DeviceInfo.Manufacturer",
    ),
    (
        "InternetGatewayDevice.DeviceInfo.ModelName",
        "Device.DeviceInfo.ModelName",
    ),
    (
        "InternetGatewayDevice.DeviceInfo.SerialNumber",
        "Device.DeviceInfo.SerialNumber",
    ),
    (
        "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.ExternalIPAddress",
        "Device.IP.Interface.1.IPv4Address.1.IPAddress",
    ),
    (
        "InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID",
        "Device.WiFi.SSID.1.SSID",
    ),
    (
        "InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.BeaconType",
        "Device.WiFi.AccessPoint.1.Security.ModeEnabled",
    ),
    (
        "InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.KeyPassphrase",
        "Device.WiFi.AccessPoint.1.Security.KeyPassphrase",
    ),
    (
        "InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.Enable",
        "Device.WiFi.Radio.1.Enable",
    ),
    (
        "InternetGatewayDevice.DeviceInfo.UpTime",
        "Device.DeviceInfo.UpTime",
    ),
    (
        "InternetGatewayDevice.ManagementServer.URL",
        "Device.ManagementServer.URL",
    ),
    (
        "InternetGatewayDevice.ManagementServer.Username",
        "Device.ManagementServer.Username",
    ),
]


def translate_path(path: str, source_model: DataModel, target_model: DataModel) -> str:
    """Translate a parameter path between TR-098 and TR-181."""
    if source_model == target_model:
        return path
    for tr098, tr181 in _PARAM_MAP:
        if source_model == DataModel.TR098 and path == tr098:
            return tr181
        if source_model == DataModel.TR181 and path == tr181:
            return tr098
    raise KeyError(f"No mapping for '{path}' from {source_model.value}")


def normalize_path(path: str, target_model: DataModel = DataModel.TR181) -> str:
    """Detect model from path prefix and normalize to target_model."""
    if path.startswith("InternetGatewayDevice."):
        return translate_path(path, DataModel.TR098, target_model)
    elif path.startswith("Device."):
        return translate_path(path, DataModel.TR181, target_model)
    raise ValueError(f"Cannot detect data model for path: '{path}'")
