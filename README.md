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
- `cpe_ta/dashboard/` — Web-Dashboard (FastAPI + Vanilla-HTML, 6 Views, offline)
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

## Web-Dashboard

```bash
# Dashboard starten (loopback, Port 8080)
cpe-ta dashboard

# Mit custom Port und Ergebnisdatei
cpe-ta dashboard --port 9090 --results test-results.xml

# Hilfe
cpe-ta dashboard --help
```

Das Dashboard öffnet `http://127.0.0.1:8080/` im Browser und zeigt 6 Views:
- **Overview** — Gesamtstatistik (Passed/Failed/Skipped/Error), letzter Run
- **Domains** — Pass/Fail-Quote pro Testdomäne (LAN, WiFi, WAN, …)
- **Run History** — Tabelle aller Runs mit Klick auf Detail-Ansicht
- **Run Detail** — alle Tests eines Runs mit Status-Icons und Fehler-Stacktraces
- **Testbed Status** — DUT, HAL-Devices und Services aus `testbed.yaml`
- **Start Run** — Marker-Ausdruck eingeben, pytest starten, Fortschritt live verfolgen

Das Dashboard läuft vollständig offline (kein CDN, kein Node.js, kein Build-System).
Backend-Tests (61 Tests) laufen headless im `make verify`-Gate.

Vollständige Dokumentation: [docs/](docs/)
