# Architecture — CPE Test-Automation Framework

## Overview

The CPE Test-Automation Framework follows a strict layered architecture that separates business logic (test cases), hardware abstraction (HAL), device-under-test control (DUT), reference infrastructure services, and reporting. This separation ensures that every test can run headless against deterministic simulators without requiring physical hardware.

## Layer Model

```
┌──────────────────────────────────────────────────────┐
│  Tests (tests/)                                      │
│  Business logic: what to measure and what passes     │
├──────────────────────────────────────────────────────┤
│  Core (cpe_ta/core/)                                 │
│  Framework engine: config, inventory, criteria,      │
│  results persistence, test runner orchestration      │
├──────────────────────────────────────────────────────┤
│  DUT (cpe_ta/dut/)                                   │
│  Device abstraction: CPE interface, TR-181 data      │
│  model mapping, SimCPE simulator                     │
├──────────────────────────────────────────────────────┤
│  Infra (cpe_ta/infra/)                               │
│  Reference services: ACS/CWMP, RADIUS, DHCP,        │
│  traffic generation, SIP, NTP, file server           │
├──────────────────────────────────────────────────────┤
│  HAL (cpe_ta/hal/)                                   │
│  Hardware abstraction: Switch, PDU, SerialConsole,   │
│  RF attenuator, USB relay — Protocol objects only    │
├──────────────────────────────────────────────────────┤
│  HAL Drivers (cpe_ta/hal/drivers/)                   │
│  Vendor-specific implementations: NETCONF switch,   │
│  SNMP switch, HTTP PDU, serial console, RF, USB      │
└──────────────────────────────────────────────────────┘
```

## Core Layer (`cpe_ta/core/`)

The core layer provides the foundational building blocks:

- **config.py** — Loads and validates the testbed YAML file into a `TestbedConfig` Pydantic model. Raises `ConfigError` on any structural or semantic problem.
- **inventory.py** — Validates the wiring map (port assignments, role uniqueness, duplicate detection).
- **criteria.py** — Loads performance criteria profiles from YAML files (e.g., `profiles/rfc2544.yaml`). Provides `PerfCriterion` and `evaluate_result()` for pass/fail decisions against thresholds.
- **results.py** — SQLite-backed result store (`ResultsDB`) with WAL mode and schema migrations. `TestResult` and `RunMetadata` dataclasses are the data model.
- **runner.py** — Test runner orchestration: sets up fixtures, runs test cases, and stores results.
- **selection.py** — Test selection logic based on marker expressions and DUT capabilities.
- **security.py** — EN-18031 security requirement model and compliance check engine.
- **errors.py** — Base exception hierarchy.

## HAL Layer (`cpe_ta/hal/`)

### HAL Invariant

**No vendor-specific imports are allowed outside `cpe_ta/hal/drivers/`.**

The `hal/base.py` module defines only `Protocol` classes (structural typing):
- `Switch` — Port enable/disable, VLAN, stats, port mirroring
- `PDU` — Outlet power control (on/off/cycle)
- `SerialConsole` — Terminal access and metric reads
- `RFAttenuator` — Channel attenuation for WiFi tests
- `USBRelay` — USB relay channel control

This means any code in `cpe_ta/core/`, `cpe_ta/dut/`, `cpe_ta/infra/`, or `tests/` that receives a HAL object works against the Protocol, never against a concrete vendor driver. The concrete drivers (NETCONF, SNMP, HTTP, pyserial, etc.) live exclusively in `hal/drivers/`.

### Real vs. Simulator Switch

The `hal/factory.py` module exposes a factory function that returns either a real driver or a simulator depending on the `sim_mode` flag in the testbed config or the `--sim-mode` CLI option:

```python
switch = get_switch(config.switches[0], sim_mode=True)  # returns SimSwitch
switch = get_switch(config.switches[0], sim_mode=False) # returns NetconfSwitch
```

Tests never call the factory directly. Instead, pytest fixtures defined in `conftest.py` files handle the factory call and inject the correct implementation.

## DUT Layer (`cpe_ta/dut/`)

- **base.py** — `CPEInterface` Protocol: defines the operations a test can perform on a DUT (get/set parameters, reboot, factory reset, etc.).
- **capabilities.py** — `DUTCapabilities` dataclass listing optional features (WiFi 6, IPv6, VoIP, USB, etc.) for capability-gated test selection.
- **datamodel.py** — TR-098 / TR-181 parameter path mapping. Abstracts the difference between TR-098 (DSL) and TR-181 (unified) naming.
- **drivers/generic.py** — Real SSH/TR-069 driver implementation.
- **sim/sim_cpe.py** — In-memory SimCPE that stores parameters in a dict, supports all Protocol methods, and is fully deterministic.

## Infra Layer (`cpe_ta/infra/`)

Reference infrastructure services used by test cases:

| Service | Simulator | Real Implementation |
|---------|-----------|---------------------|
| ACS/CWMP | `sim_acs.py` | `genie_acs.py` |
| DHCP | `sim_dhcp.py` | `kea_dhcp.py` |
| RADIUS | `sim_radius.py` | `freeradius.py` |
| Traffic | `sim_traffic.py` | `iperf3.py` |
| SIP | `sim_sip.py` | (external PBX) |
| NTP | `sim_ntp.py` | (system NTP) |
| File Server | `sim_fileserver.py` | (HTTP server) |

All simulators implement the same `Protocol` interface defined in `infra/base.py`.

## Reporting (`cpe_ta/report/`)

- **junit.py** — Generates JUnit-compatible XML for CI integration.
- **html.py** — Renders an HTML report using an inline Jinja2 template. Color-coded by outcome (passed/failed/error/skipped).
- **charts.py** — Matplotlib charts (throughput by firmware, latency trend). Always uses the `Agg` backend (no display required).
- **pdf.py** — Optional PDF generation via WeasyPrint. Returns `False` gracefully when WeasyPrint is not installed.

## Headless / Hardware Separation

All test files use two marker categories:

- `@pytest.mark.headless` — Test runs entirely against simulators. No real hardware, no network access. These tests run in CI on every commit.
- `@pytest.mark.hardware` — Test requires physical hardware (Switch, PDU, real CPE). These tests are skipped when the `--markers headless` filter is active.

The `skip_if_missing()` helper (in `conftest.py`) allows hardware tests to detect absent hardware at runtime and skip gracefully instead of failing hard.

## Testbed YAML and Wiring Map

The single source of truth for a test environment is `testbed.yaml` (validated with `cpe-ta inventory-validate`). The wiring map defines which physical port on which switch corresponds to which logical DUT port role (DUT-LAN-1, DUT-WAN, etc.).

For a complete field-by-field explanation, see [testbed.md](testbed.md).

## Performance Criteria Profiles

Performance thresholds (e.g., minimum throughput, maximum latency) are defined in YAML profiles under `profiles/`. The engine loads these at test time and calls `evaluate_result()` to determine pass/fail. Profiles reference RFC 2544 and RFC 6349 methodology. See [criteria.md](criteria.md) for details.
