from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Technology(Enum):
    DSL = "dsl"
    DOCSIS = "docsis"
    PON = "pon"
    FWA = "fwa"


class WiFiBand(Enum):
    BAND_2_4 = "2.4"
    BAND_5 = "5"
    BAND_6 = "6"


@dataclass
class CapabilitySet:
    lan_ports: int = 4
    wan_ports: int = 1
    wifi_bands: list[WiFiBand] = field(default_factory=list)
    max_linkspeed_mbps: int = 1000
    has_voip: bool = False
    has_usb: bool = False
    technologies: list[Technology] = field(default_factory=list)
    supports_wpa3: bool = True
    supports_wifi6: bool = False
    supports_wifi7: bool = False
    voip_ports: int = 0

    def supports(self, tech: Technology) -> bool:
        return tech in self.technologies

    def has_band(self, band: WiFiBand) -> bool:
        return band in self.wifi_bands
