# Progress: CPE Test-Automation Framework (P1 / Done-Gate)

**Phase:** BUILD  
**Gestartet:** 2026-06-21  
**Stand:** In Arbeit

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
- [x] T41 — Gate deckt Framework-Unit-Tests ab (Gap 1, MEDIUM) — Gate auf `-m "not hardware"` umgestellt; 559 Tests (417 headless + 142 Unit), Coverage 90%
- [x] T42 — Deferred-Matrix bereinigen (Gap 2, LOW) — `test_fw_flash_real` / `test_fw_rollback_real` als "geplant (P2)" markiert; 15 reale @hardware-Tests in Matrix

## Done-Gate Status
**GRÜN — 559 Tests, ruff clean, mypy --strict clean, Coverage 90%, AC-22 (15 skipped)**
Commit: (aktuell)
