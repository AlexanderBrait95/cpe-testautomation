# Progress: CPE Test-Automation Framework (P1 / Done-Gate)

**Phase:** BUILD  
**Gestartet:** 2026-06-21  
**Stand:** Dashboard vollständig implementiert

## Gruppe A — Projekt-Skelett & Tooling
- [x] T01 — Projekt-Bootstrap & Build-Tooling
- [x] T02 — Fehlertaxonomie

## Gruppe B — Core
- [x] T03 — Config-Modelle (Pydantic v2)
- [x] T04 — Wiring-Map / Inventory-Auflösung
- [x] T05 — inventory-validate CLI-Befehl
- [x] T06 — Pass/Fail-Methodik (criteria.py)
- [x] T07 — Tag-/Capability-Selektion + Skip-Logik

## Gruppe C — HAL
- [x] T08 — HAL Base-Interfaces (Protocols/ABCs)
- [x] T09 — HAL-Simulatoren
- [x] T10 — HAL reale Treiber-Skelette
- [x] T11 — Instrument-Factory
- [x] T12 — HAL-Vollständigkeits-Meta-Test

## Gruppe D — DUT-Abstraktion
- [x] T13 — DUT Base-Interface + Capability-Modell
- [x] T14 — TR-098 ↔ TR-181 Mapping-Layer
- [x] T15 — Sim-CPE + Driver-Skelett

## Gruppe E — Referenz-Infra-Abstraktion
- [x] T16 — Infra Base-Interfaces
- [x] T17 — Infra-Simulatoren + reale Adapter-Skelette

## Gruppe F — Runner, Reporting, Persistenz
- [x] T18 — Test-Session-Runner
- [x] T19 — Nebenläufigkeit (xdist-Isolation)
- [x] T20 — Ergebnis-Modell + SQLite-Persistenz
- [x] T21 — Reporting: JUnit-XML + HTML + Charts + PDF

## Gruppe G — Layering-Invariante
- [x] T22 — Import-Linter / Layering-Meta-Test
- [x] T23 — Determinismus-Meta-Test

## Gruppe H — Domänen-Testfälle (headless)
- [x] T24 — LAN-Tests
- [x] T25 — WiFi-Logik-Tests
- [x] T26 — QoS/Performance-Tests
- [x] T27 — WAN/Provisioning-Tests
- [x] T28 — DHCP-Tests
- [x] T29 — Multicast-Tests
- [x] T30 — IPv6/Dual-Stack-Tests
- [x] T31 — Security/EN-18031-Tests
- [x] T32 — ACS/CWMP-RPC-Suite
- [x] T33 — Stress/Soak (Kurzlauf headless)
- [x] T34 — Marker-Coverage-Meta-Test

## Gruppe I — Hardware-deferred
- [x] T35 — @hardware-Tests + Deferred-Matrix

## Gruppe J — CLI, CI, Doku, Gate
- [x] T36 — CLI vervollständigen
- [x] T37 — CI-Templates
- [x] T38 — Dokumentation
- [x] T39 — Qualitäts-Gate: ruff + mypy + Coverage (86%)
- [x] T40 — make verify Gate-Orchestrierung

## Gruppe Z — Verify-Lücken
- [x] T41 — Gate deckt Framework-Unit-Tests ab
- [x] T42 — Deferred-Matrix bereinigen

## Gruppe Z² — Gate-Reparatur GAP-1 (Iteration 5)
- [x] TZ-01 — Stabile Sample-JUnit-XML `tests/dashboard/fixtures/sample-results.xml` angelegt (10 Tests, 3 Domains, bekannte Sollzahlen)
- [x] TZ-02 — `test_overview_real_xml_counts` auf stabile Fixture umgestellt; Hardcode 559 entfernt; Domain-Aggregation mitgeprüft
- [x] TZ-03 — `make verify`-Gate läuft exit 0: ruff clean, mypy clean, 620 passed 0 failed, Coverage 89%, AC-22 15 skipped

## Gruppe DA — Dashboard-Fundament
- [x] T-D01 — Dashboard-Dependencies & Package-Skelett (fastapi/uvicorn/httpx in pyproject.toml + requirements.txt; cpe_ta/dashboard/ angelegt)
- [x] T-D02 — Pydantic Response-Modelle models.py (OverviewModel, DomainStat, RunSummary, RunDetail, TestEntry, TestbedStatus, RunStartRequest, RunProgress)

## Gruppe DB — Daten-Layer
- [x] T-D03 — JUnit-XML-Parser + Domain-Aggregation (data.py: parse_junit, overview, domain_stats; tolerantes Parsen; Leerzustand)
- [x] T-D04 — DB-Lesezugriff + View-Aggregation (data.py: get_run_summaries, get_run_detail via ResultsDB)

## Gruppe DC — Run-Start
- [x] T-D05 — DashboardRunner mit injizierbarer Command-Factory (runner.py: shell=False, Marker-Whitelist, Busy-Signal, Progress-Tracking)

## Gruppe DD — FastAPI-App & Routen
- [x] T-D06 — FastAPI-App-Factory + 6 JSON-Routen (app.py: create_app, alle Routen 200 + Schema)
- [x] T-D07 — Run-Start-Flow & Sicherheit (409 bei Busy, 422 bei Bad-Marker, Default-Host 127.0.0.1)

## Gruppe DE — CLI & Frontend
- [x] T-D08 — CLI-Befehl `cpe-ta dashboard` (click, --host/--port/--results/--db, Port-Belegt-Exit ≠ 0)
- [x] T-D09 — Vanilla-Frontend (index.html/app.css/app.js, 6 Views, kein CDN, offline)

## Gruppe DF — Qualität, Offline-Gate, Doku
- [x] T-D10 — Offline-/Sicherheits-Meta-Test + Backend-Coverage (≥80% dashboard, test_offline.py)
- [x] T-D11 — Lint/Typen-Gate: ruff clean + mypy --strict clean für dashboard
- [x] T-D12 — Gate-Integration + Doku-Update (make verify nimmt tests/dashboard/ mit; README + docs/architecture.md aktualisiert)

## Done-Gate Status
**GRÜN — 620 Tests (559 Kern + 61 Dashboard), ruff clean, mypy --strict clean, Coverage 89%, AC-22 (15 skipped)**
**Dashboard AC-23..AC-31: alle erfüllt**
**Iteration 5 (GAP-1): Gate repariert — 620 passed 0 failed, keine spröde Assertion mehr**
