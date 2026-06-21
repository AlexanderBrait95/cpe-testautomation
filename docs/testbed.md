# Testbed Configuration Guide

## Overview

The testbed YAML file is the single source of truth for a physical (or simulated) test environment. It describes all infrastructure components — switches, PDUs, DUTs — and defines the wiring map that maps logical port roles to physical switch ports.

Before running any test, validate the testbed file:

```bash
cpe-ta inventory-validate testbed.yaml
```

## VLAN Isolation Concept

Each DUT under test is placed in a dedicated VLAN to ensure complete traffic isolation between concurrent test runs. The switch ports are configured as VLAN access ports (untagged) for DUT-facing ports and as trunk ports (tagged) for uplink connections to the traffic-generation host. This ensures:

1. DUT LAN ports cannot receive broadcast traffic from other DUTs.
2. WAN traffic for one DUT is isolated from WAN traffic for another.
3. Management traffic to the test controller remains on a separate management VLAN.

The `wiring_map` entries in the testbed YAML define the port-to-role mapping, and the framework's switch HAL automatically applies the correct VLAN configuration before each test case and tears it down after.

## testbed.example.yaml — Field Reference

```yaml
id: "lab-testbed-01"
```

**`id`** (required, string) — Unique identifier for this testbed. Appears in test reports and database records. Use a descriptive slug like `lab-testbed-01` or `ci-testbed-rack-a`.

```yaml
switches:
  - switch_id: "sw-main"
    host: "192.168.1.10"
    protocol: "snmp"
    community: "public"
```

**`switches`** (optional, list) — Network switches under HAL control.

- `switch_id` (required) — Logical name used in the wiring map.
- `host` (required) — Management IP address or hostname.
- `protocol` (required) — Management protocol. Accepted values: `snmp`, `netconf`, `restconf`.
- `community` — SNMP community string (only for `protocol: snmp`).

```yaml
pdus:
  - pdu_id: "pdu-main"
    host: "192.168.1.20"
    protocol: "http"
    username: "admin"
    password: "admin"
```

**`pdus`** (optional, list) — Power Distribution Units for DUT power cycling.

- `pdu_id` (required) — Logical name referenced in DUT entries.
- `host` (required) — Management IP address or hostname.
- `protocol` (required) — Management protocol. Currently supported: `http`.
- `username` / `password` — Credentials for the PDU management interface.

```yaml
duts:
  - dut_id: "dut-alpha"
    model: "EasyBox 904 DSL"
    vendor: "Vodafone"
    serial: "VF0123456789"
    technology: "dsl"
    pdu_id: "pdu-main"
    pdu_outlet: "1"
    console_host: "192.168.1.30"
    console_port: 9001
```

**`duts`** (optional, list) — Devices under test.

- `dut_id` (required) — Logical name used in test fixtures and reports.
- `model` (required) — Human-readable model name.
- `vendor` (required) — Vendor/manufacturer name.
- `serial` (optional) — Device serial number for traceability.
- `technology` (optional) — Access technology: `dsl`, `docsis`, `pon`, or `fwa`. Drives technology-specific marker selection.
- `pdu_id` / `pdu_outlet` (optional) — PDU reference for remote power cycling.
- `console_host` / `console_port` (optional) — Serial console over TCP (e.g., via ser2net).

```yaml
wiring_map:
  entries:
    - role: "DUT-LAN-1"
      port:
        switch_id: "sw-main"
        port_id: "gi0/1"
    - role: "DUT-WAN"
      port:
        switch_id: "sw-main"
        port_id: "gi0/5"
```

**`wiring_map`** (optional, object) — Physical port assignments.

- `entries` (list) — Each entry maps a logical `role` to a physical `port`.
  - `role` — Logical name (e.g., `DUT-LAN-1`, `DUT-LAN-2`, `DUT-WAN`, `TRAFFIC-HOST`).
  - `port.switch_id` — Must match a `switch_id` defined in `switches`.
  - `port.port_id` — Physical port identifier in the switch's own notation (e.g., `gi0/1`, `eth1`).

The framework validates that no two roles share the same physical port (`switch_id` + `port_id` combination must be unique).

## Minimal Valid testbed.yaml

The only required field is `id`. All other sections are optional and gracefully absent when running in pure simulator mode:

```yaml
id: "sim-only"
```

Running `cpe-ta inventory-validate sim-only.yaml` on this file exits 0. Tests marked `@pytest.mark.headless` will skip hardware fixture setup and use simulators directly.

## Best Practices

- Always version-control your testbed YAML (without passwords — use environment variables for secrets).
- Use `cpe-ta inventory-validate` as a pre-flight check in CI before any test run.
- Name DUT IDs and switch IDs consistently across multiple testbed files (one per rack or environment).
- Keep the wiring map up to date when cables are moved — the framework will enforce role uniqueness automatically.
