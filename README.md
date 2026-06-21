# CPE Test-Automation Framework

Hardware- und Software-Acceptance-Test-Framework für CPE-Geräte (DSL, DOCSIS, PON, FWA).

## Quickstart

```bash
pip install -e .
cpe-ta inventory-validate testbed.example.yaml
cpe-ta run -m "smoke and headless"
```

## Architektur

Das Framework trennt strikt Businesslogik (Testfälle) von Hardware-Zugriff (HAL).
Alle Tests laufen headless gegen deterministische Simulatoren.

- `cpe_ta/core/` — Framework-Kern (Config, Inventory, Criteria, Results, Runner)
- `cpe_ta/hal/` — Hardware-Abstraktionsschicht (Switch, PDU, SerialConsole, RF, USB)
- `cpe_ta/dut/` — DUT-Abstraktion (CPE-Interface, TR-098/TR-181-Mapping, Sim-CPE)
- `cpe_ta/infra/` — Referenz-Infrastruktur (ACS, RADIUS, DHCP, Traffic, SIP)
- `cpe_ta/report/` — Reporting (JUnit-XML, HTML, Charts, PDF)
- `tests/` — Testfall-Bibliothek (LAN, WiFi, QoS, WAN, DHCP, Multicast, IPv6, Security, ACS)

## Test-Ausführung

```bash
# Alle headless Tests (kein Hardware erforderlich)
make verify

# Spezifische Domäne
pytest tests/lan -m headless -v

# Hardware-Tests (werden übersprungen ohne Hardware)
pytest -m hardware

# Parallel (4 Worker)
pytest -m headless -n 4
```

## Testbed-Konfiguration

Kopiere `testbed.example.yaml` und passe Switch/PDU/DUT-Adressen an.
Validierung: `cpe-ta inventory-validate testbed.yaml`

Vollständige Dokumentation: [docs/](docs/)
