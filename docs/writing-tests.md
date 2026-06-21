# Writing Tests for the CPE Test-Automation Framework

## Overview

Test cases in this framework are standard pytest functions or methods, extended with a small set of conventions that ensure capability-gated selection, hardware-optional execution, and deterministic headless runs.

## Headless vs. Hardware Markers

Every test must be decorated with exactly one of the two primary execution markers:

```python
@pytest.mark.headless
def test_lan_switching_sim(sim_switch, sim_dut):
    """Runs against SimSwitch and SimCPE — no hardware required."""
    ...

@pytest.mark.hardware
def test_lan_switching_real(real_switch, real_dut):
    """Requires a physical switch and CPE — skipped in CI headless mode."""
    ...
```

- `@pytest.mark.headless` — The test must complete entirely against simulators. It may not open any real TCP connections, SNMP sessions, serial ports, or SSH connections. CI runs only headless tests.
- `@pytest.mark.hardware` — The test requires physical hardware. When `pytest -m headless` is the active filter (e.g., in `make verify`), hardware tests are excluded by the marker expression and never collected.

Do not mix the two markers on a single test function.

## Using `skip_if_missing()`

Within a `@pytest.mark.hardware` test, use `skip_if_missing()` to detect absent hardware at runtime and skip gracefully:

```python
import pytest
from tests.conftest import skip_if_missing

@pytest.mark.hardware
def test_pdu_power_cycle(pdu, dut):
    skip_if_missing(pdu, "PDU not configured in testbed")
    pdu.power_cycle(dut.pdu_outlet)
    ...
```

This prevents a hard failure when the testbed YAML exists but a particular piece of hardware is not connected or not configured.

## Fixtures

The framework provides fixtures at multiple levels:

### Simulator Fixtures (headless)

| Fixture | Type | Source |
|---------|------|--------|
| `sim_switch` | `SimSwitch` | `conftest.py` (root or domain) |
| `sim_pdu` | `SimPDU` | `conftest.py` |
| `sim_dut` | `SimCPE` | `conftest.py` |
| `sim_acs` | `SimACSService` | `tests/acs/conftest.py` |
| `sim_dhcp` | `SimDHCPService` | `tests/dhcp/conftest.py` |
| `sim_traffic` | `SimTrafficService` | `tests/qos/conftest.py` |
| `sim_radius` | `SimRADIUSService` | `tests/security/conftest.py` |

### Hardware Fixtures (require real testbed)

| Fixture | Type | Notes |
|---------|------|-------|
| `real_switch` | `Switch` Protocol | Created via `hal.factory.get_switch()` |
| `real_pdu` | `PDU` Protocol | Created via `hal.factory.get_pdu()` |
| `real_dut` | `CPEInterface` Protocol | Created via `dut.drivers.generic` |

## Writing a Capability-Gated Test

When a test requires an optional DUT capability (WiFi 6, IPv6, VoIP, etc.), check the capability via the `DUTCapabilities` object rather than hard-coding assumptions:

```python
@pytest.mark.headless
def test_wifi6_rate(sim_dut, sim_rf):
    caps = sim_dut.get_capabilities()
    if not caps.wifi6:
        pytest.skip("DUT does not support WiFi 6")
    # proceed with WiFi 6 specific test
    ...
```

For hardware tests, the same pattern applies with the real DUT fixture.

## Performance Criterion Pattern

Performance tests compare measured values against thresholds defined in criteria profiles:

```python
from cpe_ta.core.criteria import load_criteria, evaluate_result

@pytest.mark.headless
def test_throughput(sim_traffic, sim_dut):
    criterion = load_criteria("profiles/rfc2544.yaml")["lan_throughput"]
    result = sim_traffic.measure_throughput(duration_s=10)
    assert evaluate_result(result, criterion), (
        f"Throughput {result.throughput_mbps:.1f} Mbit/s below "
        f"threshold {criterion.min_throughput_mbps} Mbit/s"
    )
```

See [criteria.md](criteria.md) for profile format details.

## Test File Placement

Place tests in the domain directory that best matches their primary concern:

```
tests/
├── lan/          # Layer-2 switching, autoneg, throughput
├── wifi/         # SSID, security modes, RF attenuation
├── qos/          # Traffic shaping, DSCP marking, RFC 2544
├── wan/          # NAT, firewall, WAN connectivity
├── dhcp/         # DHCPv4/v6 pool, options, relay
├── multicast/    # IGMP snooping, multicast streams
├── ipv6/         # IPv6 stack, RA, NDP, prefix delegation
├── security/     # EN-18031, port scan, credential checks
├── acs/          # CWMP RPC, parameter set/get, firmware upgrade
└── stress/       # Soak, reboot cycles, memory leak checks
```

Cross-domain tests (e.g., QoS over IPv6) belong in the dominant domain and may import fixtures from sibling conftest files using `pytest`'s fixture scope.

## Naming Conventions

- Test functions: `test_<what>_<condition>` — e.g., `test_dhcp_lease_renew`, `test_firewall_blocks_wan_to_lan`.
- Use descriptive names — the test name becomes the JUnit XML `testcase name` attribute.
- Avoid abbreviations in test names.
