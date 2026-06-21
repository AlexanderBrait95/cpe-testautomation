"""Help / Onboarding content data layer.

All content is data-driven from the real HAL/DUT/Infra interface names.
HAL_DEVICE_NAMES must stay in sync with cpe_ta/hal/base.py + cpe_ta/dut/base.py.
The meta-test (test_help.py) verifies this alignment automatically.
real_status is derived by introspecting the real driver classes (TP-01/AC-45).
"""
from __future__ import annotations

import importlib
import inspect
from typing import Literal

from cpe_ta.dashboard.models import HelpContent, HelpDevice, HelpQuickstartStep, HelpService

# Must match Protocol names in cpe_ta/hal/base.py (Switch, PDU, SerialConsole,
# RFAttenuator, USBRelay) + cpe_ta/dut/base.py (CPE) — 6 total.
HAL_DEVICE_NAMES: list[str] = [
    "Switch",
    "PDU",
    "SerialConsole",
    "RFAttenuator",
    "USBRelay",
    "CPE",
]

# Must match Protocol names in cpe_ta/infra/base.py — 7 total.
INFRA_SERVICE_KEYS: list[str] = [
    "acs",
    "radius",
    "dhcp",
    "sip",
    "traffic",
    "ntp",
    "fileserver",
]

# Mapping from device name to (module, class) for real driver introspection.
_HAL_DRIVER_MAP: dict[str, tuple[str, str]] = {
    "Switch": ("cpe_ta.hal.drivers.snmp_switch", "SNMPSwitch"),
    "PDU": ("cpe_ta.hal.drivers.pdu_http", "HTTPPdu"),
    "SerialConsole": ("cpe_ta.hal.drivers.serial_console", "SerialConsoleDriver"),
    "RFAttenuator": ("cpe_ta.hal.drivers.rf_attenuator", "RFAttenuatorDriver"),
    "USBRelay": ("cpe_ta.hal.drivers.usb_relay", "USBRelayDriver"),
    "CPE": ("cpe_ta.dut.drivers.generic", "GenericCPEDriver"),
}

# Mapping from service key to (module, class) for infra real driver introspection.
# Keys without an entry have no real driver yet → skeleton by default.
_INFRA_DRIVER_MAP: dict[str, tuple[str, str]] = {
    "acs": ("cpe_ta.infra.real.genie_acs", "GenieACSClient"),
    "radius": ("cpe_ta.infra.real.freeradius", "FreeRADIUSAdapter"),
    "dhcp": ("cpe_ta.infra.real.kea_dhcp", "KeaDHCPAdapter"),
    "traffic": ("cpe_ta.infra.real.iperf3", "Iperf3Endpoint"),
}


def _introspect_real_status(
    module_name: str, class_name: str
) -> Literal["implemented", "partial", "skeleton"]:
    """Return implementation status of a real driver class via source inspection.

    Checks all public methods for NotImplementedError:
    - all raise NotImplementedError (or class not found) → "skeleton"
    - some raise, some don't → "partial"
    - none raise → "implemented"
    """
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
    except (ImportError, AttributeError):
        return "skeleton"

    not_impl = 0
    impl = 0
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        try:
            src = inspect.getsource(method)
            if "NotImplementedError" in src:
                not_impl += 1
            else:
                impl += 1
        except (OSError, TypeError):
            not_impl += 1

    if impl == 0:
        return "skeleton"
    if not_impl == 0:
        return "implemented"
    return "partial"


_HARDWARE_DATA: list[tuple[str, str, str, bool]] = [
    (
        "Switch",
        "Managed switch — port enable/disable, VLAN tagging, speed/duplex, traffic mirroring",
        "SNMP v2c/v3 or NETCONF; see cpe_ta/hal/drivers/snmp_switch.py",
        True,
    ),
    (
        "PDU",
        "Power Distribution Unit — remote power on/off/cycle for DUT and other lab outlets",
        "HTTP REST API; see cpe_ta/hal/drivers/pdu_http.py",
        True,
    ),
    (
        "SerialConsole",
        "Serial console server — CPE serial console access, CPU/RAM metric polling",
        "TCP serial-over-IP (e.g. Moxa/Digi); see cpe_ta/hal/drivers/",
        True,
    ),
    (
        "RFAttenuator",
        "Programmable RF attenuator — control WiFi signal strength for coverage tests",
        "USB/GPIB; see cpe_ta/hal/drivers/; deferred for headless tests",
        True,
    ),
    (
        "USBRelay",
        "USB relay board — simulate hardware button presses (factory reset, WPS, etc.)",
        "USB HID; see cpe_ta/hal/drivers/",
        True,
    ),
    (
        "CPE",
        "Customer Premises Equipment (Device Under Test) — the router/modem/gateway being tested",
        "Controlled via PDU (power) + SerialConsole (console) + ACS (CWMP config)",
        True,
    ),
]

_INFRA_DATA: list[tuple[str, str, str, bool, str]] = [
    (
        "acs",
        "ACS — TR-069/CWMP Auto Configuration Server",
        "Bootstraps CPE, delivers firmware/config via CWMP; required for all ACS/provisioning tests",
        True,
        "Real: GenieACS NBI (HTTP); Sim: built-in CWMP simulator in cpe_ta/infra/sim/",
    ),
    (
        "radius",
        "RADIUS Authentication Server",
        "802.1X, PPPoE and WiFi-Enterprise auth; required for WAN/WiFi-Enterprise tests",
        True,
        "Real: FreeRADIUS; Sim: in-memory credential store",
    ),
    (
        "dhcp",
        "DHCP/DNS Server",
        "IP address pools, static leases, DHCP options (60/43/121/15/42/125) for provisioning tests",
        True,
        "Real: Kea or ISC dhcpd; Sim: in-memory lease table",
    ),
    (
        "sip",
        "SIP/IMS Server",
        "SIP registration and call setup for VoIP quality tests (codec, MOS, T.38)",
        True,
        "Real: Kamailio; Sim: stubbed call result; VoIP audio path is hardware-deferred",
    ),
    (
        "traffic",
        "Traffic Endpoint (iperf3)",
        "Throughput/latency measurement; required for QoS, performance (RFC 2544/6349) tests",
        True,
        "Real: iperf3 server binary; Sim: configurable synthetic TrafficResult",
    ),
    (
        "ntp",
        "NTP Time Server",
        "Verifies CPE time synchronization; checked during provisioning and ACS tests",
        True,
        "Real: chrony or ntpd; Sim: fixed timestamp stub",
    ),
    (
        "fileserver",
        "File Server (HTTP/FTP)",
        "Provides firmware images and config files for fw_flash and config_restore tests",
        True,
        "Real: lighttpd or nginx; Sim: in-memory file store with URL stub",
    ),
]

_QUICKSTART: list[HelpQuickstartStep] = [
    HelpQuickstartStep(
        order=1,
        title="Install",
        description="Install the framework into your Python environment.",
        command="pip install -e .",
    ),
    HelpQuickstartStep(
        order=2,
        title="Check Inventory",
        description="Copy testbed.example.yaml to testbed.yaml, edit for your lab, then validate.",
        command="cpe-ta inventory-validate testbed.yaml",
    ),
    HelpQuickstartStep(
        order=3,
        title="Run Smoke Tests",
        description="Execute a quick smoke test suite against the built-in simulators (no hardware needed).",
        command='cpe-ta run -m "smoke and headless"',
    ),
    HelpQuickstartStep(
        order=4,
        title="View Report",
        description="Open the dashboard to browse results, or generate a static HTML report.",
        command="cpe-ta dashboard",
    ),
    HelpQuickstartStep(
        order=5,
        title="Switch to Real Hardware",
        description=(
            "To test against physical hardware, first implement the real driver classes in "
            "cpe_ta/hal/drivers/ and cpe_ta/infra/real/ (currently all drivers are documented "
            "skeletons — see docs/architecture.md for the extension guide). Once a driver is "
            "implemented, update testbed.yaml with real device IPs/credentials and set USE_SIM=0."
        ),
        command=None,
    ),
]


def get_help_content() -> HelpContent:
    """Return the full help/onboarding content model with introspected real_status."""
    hardware: list[HelpDevice] = []
    for name, purpose, connection, sim_available in _HARDWARE_DATA:
        driver_ref = _HAL_DRIVER_MAP.get(name)
        rs = (
            _introspect_real_status(driver_ref[0], driver_ref[1])
            if driver_ref
            else "skeleton"
        )
        hardware.append(
            HelpDevice(
                name=name,
                purpose=purpose,
                connection=connection,
                sim_available=sim_available,
                real_status=rs,
            )
        )

    infrastructure: list[HelpService] = []
    for key, svc_name, purpose, sim_available, note in _INFRA_DATA:
        driver_ref = _INFRA_DRIVER_MAP.get(key)
        rs = (
            _introspect_real_status(driver_ref[0], driver_ref[1])
            if driver_ref
            else "skeleton"
        )
        infrastructure.append(
            HelpService(
                key=key,
                name=svc_name,
                purpose=purpose,
                sim_available=sim_available,
                note=note,
                real_status=rs,
            )
        )

    return HelpContent(
        quickstart=list(_QUICKSTART),
        hardware=hardware,
        infrastructure=infrastructure,
    )
