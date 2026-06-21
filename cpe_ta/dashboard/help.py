"""Help / Onboarding content data layer.

All content is data-driven from the real HAL/DUT/Infra interface names.
HAL_DEVICE_NAMES must stay in sync with cpe_ta/hal/base.py + cpe_ta/dut/base.py.
The meta-test (test_help.py) verifies this alignment automatically.
"""
from __future__ import annotations

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

_HARDWARE_DATA: list[HelpDevice] = [
    HelpDevice(
        name="Switch",
        purpose="Managed switch — port enable/disable, VLAN tagging, speed/duplex, traffic mirroring",
        connection="SNMP v2c/v3 or NETCONF; see cpe_ta/hal/drivers/snmp_switch.py",
        sim_available=True,
    ),
    HelpDevice(
        name="PDU",
        purpose="Power Distribution Unit — remote power on/off/cycle for DUT and other lab outlets",
        connection="HTTP REST API; see cpe_ta/hal/drivers/pdu_http.py",
        sim_available=True,
    ),
    HelpDevice(
        name="SerialConsole",
        purpose="Serial console server — CPE serial console access, CPU/RAM metric polling",
        connection="TCP serial-over-IP (e.g. Moxa/Digi); see cpe_ta/hal/drivers/",
        sim_available=True,
    ),
    HelpDevice(
        name="RFAttenuator",
        purpose="Programmable RF attenuator — control WiFi signal strength for coverage tests",
        connection="USB/GPIB; see cpe_ta/hal/drivers/; deferred for headless tests",
        sim_available=True,
    ),
    HelpDevice(
        name="USBRelay",
        purpose="USB relay board — simulate hardware button presses (factory reset, WPS, etc.)",
        connection="USB HID; see cpe_ta/hal/drivers/",
        sim_available=True,
    ),
    HelpDevice(
        name="CPE",
        purpose="Customer Premises Equipment (Device Under Test) — the router/modem/gateway being tested",
        connection="Controlled via PDU (power) + SerialConsole (console) + ACS (CWMP config)",
        sim_available=True,
    ),
]

_INFRA_DATA: list[HelpService] = [
    HelpService(
        key="acs",
        name="ACS — TR-069/CWMP Auto Configuration Server",
        purpose="Bootstraps CPE, delivers firmware/config via CWMP; required for all ACS/provisioning tests",
        sim_available=True,
        note="Real: GenieACS NBI (HTTP); Sim: built-in CWMP simulator in cpe_ta/infra/sim/",
    ),
    HelpService(
        key="radius",
        name="RADIUS Authentication Server",
        purpose="802.1X, PPPoE and WiFi-Enterprise auth; required for WAN/WiFi-Enterprise tests",
        sim_available=True,
        note="Real: FreeRADIUS; Sim: in-memory credential store",
    ),
    HelpService(
        key="dhcp",
        name="DHCP/DNS Server",
        purpose="IP address pools, static leases, DHCP options (60/43/121/15/42/125) for provisioning tests",
        sim_available=True,
        note="Real: Kea or ISC dhcpd; Sim: in-memory lease table",
    ),
    HelpService(
        key="sip",
        name="SIP/IMS Server",
        purpose="SIP registration and call setup for VoIP quality tests (codec, MOS, T.38)",
        sim_available=True,
        note="Real: Kamailio; Sim: stubbed call result; VoIP audio path is hardware-deferred",
    ),
    HelpService(
        key="traffic",
        name="Traffic Endpoint (iperf3)",
        purpose="Throughput/latency measurement; required for QoS, performance (RFC 2544/6349) tests",
        sim_available=True,
        note="Real: iperf3 server binary; Sim: configurable synthetic TrafficResult",
    ),
    HelpService(
        key="ntp",
        name="NTP Time Server",
        purpose="Verifies CPE time synchronization; checked during provisioning and ACS tests",
        sim_available=True,
        note="Real: chrony or ntpd; Sim: fixed timestamp stub",
    ),
    HelpService(
        key="fileserver",
        name="File Server (HTTP/FTP)",
        purpose="Provides firmware images and config files for fw_flash and config_restore tests",
        sim_available=True,
        note="Real: lighttpd or nginx; Sim: in-memory file store with URL stub",
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
            "Update testbed.yaml with real device IPs/credentials, set USE_SIM=0 "
            "and re-run — the same tests execute against physical hardware."
        ),
        command=None,
    ),
]


def get_help_content() -> HelpContent:
    """Return the full help/onboarding content model."""
    return HelpContent(
        quickstart=list(_QUICKSTART),
        hardware=list(_HARDWARE_DATA),
        infrastructure=list(_INFRA_DATA),
    )
