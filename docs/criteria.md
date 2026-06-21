# Performance Criteria Profiles

## Overview

Performance tests in this framework compare measured metrics against thresholds defined in YAML profile files under `profiles/`. The criteria engine decouples test code from threshold values, making it easy to update pass/fail limits without modifying test logic.

## PerfCriterion Fields

Each criterion in a profile YAML maps to a `PerfCriterion` dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Human-readable criterion name |
| `min_throughput_mbps` | float | Minimum acceptable throughput (Mbit/s). 0 = not enforced. |
| `max_latency_ms` | float | Maximum acceptable round-trip latency (ms). 0 = not enforced. |
| `max_jitter_ms` | float | Maximum acceptable jitter (ms). 0 = not enforced. |
| `max_loss_pct` | float | Maximum acceptable packet loss percentage. 0 = not enforced. |
| `methodology` | str | Reference methodology (e.g., `rfc2544`, `rfc6349`, `custom`). |

A field value of `0` means the criterion is not enforced for that metric — the test will only evaluate fields with non-zero thresholds.

## RFC 2544 Profile

RFC 2544 defines a standard throughput, latency, frame loss, and back-to-back test methodology for network equipment. The profile at `profiles/rfc2544.yaml` implements the standard criteria for a GbE CPE LAN port:

```yaml
lan_throughput:
  name: "LAN Throughput (RFC 2544)"
  min_throughput_mbps: 800.0
  max_latency_ms: 5.0
  max_jitter_ms: 1.0
  max_loss_pct: 0.01
  methodology: "rfc2544"
```

## RFC 6349 Profile

RFC 6349 (Framework for TCP Throughput Testing) defines criteria for TCP-layer performance. The profile at `profiles/rfc6349.yaml` covers WAN-side TCP throughput:

```yaml
wan_tcp_throughput:
  name: "WAN TCP Throughput (RFC 6349)"
  min_throughput_mbps: 90.0
  max_latency_ms: 50.0
  max_jitter_ms: 10.0
  max_loss_pct: 0.1
  methodology: "rfc6349"
```

## Adding a New Profile

1. Create a new YAML file under `profiles/`, e.g., `profiles/voip.yaml`.
2. Define one or more named criteria blocks:

```yaml
voip_mos:
  name: "VoIP MOS Score"
  min_throughput_mbps: 0.1
  max_latency_ms: 150.0
  max_jitter_ms: 30.0
  max_loss_pct: 1.0
  methodology: "custom"
```

3. In your test, load the profile and evaluate:

```python
from cpe_ta.core.criteria import load_criteria, evaluate_result

criterion = load_criteria("profiles/voip.yaml")["voip_mos"]
assert evaluate_result(measured, criterion)
```

Profiles are hot-reloaded at test time — no framework restart needed.
