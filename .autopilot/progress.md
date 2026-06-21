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

## Gruppe §15 — Dashboard v2 (Bedien- & Onboarding-Console)

### V2-A — Help-Datenlayer
- [x] TA-01 — `cpe_ta/dashboard/help.py` + Modelle in `models.py` (HelpContent, HelpDevice, HelpService, HelpQuickstartStep)
- [x] TA-02 — Route `GET /api/help` in `app.py`
- [x] TA-03 — Anti-Drift-Meta-Test `tests/dashboard/test_help.py`

### V2-B — Operations-Console Backend
- [x] TB-01 — `DashboardRunner.cancel()` + `POST /api/runs/active/cancel`
- [x] TB-02 — Filter/Sort in `data.py` + Query-Params `GET /api/runs` & `GET /api/runs/{id}`
- [x] TB-03 — Export `GET /api/runs/{id}/export?format=junit|html`
- [x] TB-04 — `POST /api/inventory/validate` + Modell `InventoryValidateResult`

### V2-C — Frontend-Neubau
- [x] TC-01 — 7. Nav-Punkt "Help & Setup" + Route `/#/help` in `index.html` / `app.js`
- [x] TC-02 — Marker-Presets als Checkboxen (smoke/full/regression/headless/tech_*)
- [x] TC-03 — Cancel-Button + Filter-Controls + Export-Links
- [x] TC-04 — Leerzustände (emptyState), ≥5 Tooltips, zentraler apiFetch-Wrapper (AC-40/41/42)

### V2-D — Gate-Konformität
- [x] TD-01 — Offline-Meta-Test unverändert grün (keine externen Refs in neuen Assets)
- [x] TD-02 — ruff clean, mypy --strict clean, Dashboard-Coverage ≥80%
- [x] TD-03 — `make verify` EXIT 0: **689 passed, 0 failed**, Coverage 90%

## Gruppe §16 — Nachschärfung (Gate-Reparatur, Iteration 8)

### S — Sicherheits-Härtung der §15-Routen
- [x] TS-01 — `inventory/validate` Pfad-Whitelist + Error-Sanitisierung (AC-46): `_is_safe_path` (CWD|tmp), `_sanitize_config_error`, Traversal/Foreign-Paths → 400, Secret-Token nicht in Response
- [x] TS-02 — HTML-Export XSS-frei (AC-47): `html.escape()` für alle interpolierten Felder in `render_run_html`, Content-Disposition-Filename gesäubert
- [x] TS-03 — JUnit-Parsing entity-bomb-fest (AC-48): `defusedxml>=0.7` in deps + `_defused_ET.parse()` in `parse_junit`, Billion-Laughs-Test terminiert < 1s
- [x] TS-04 — Runner-Ausgabepuffer beschränkt (AC-49): `deque(maxlen=1000)` statt unbegrenzter list, `list(self._lines)[-20:]` für Tail
- [x] TS-05 — Host-Sicherheitswarnung bei Nicht-Loopback-Bind (AC-50): `_LOOPBACK_HOSTS` + Warning auf stderr vor uvicorn.run

### P — Ehrliches Real-Status-Onboarding
- [x] TP-01 — `real_status`-Feld via Treiber-Introspektion (AC-45): `Literal[...]` in `HelpDevice`/`HelpService`, `_introspect_real_status()` + Treiber-Mappings in `help.py`, alle aktuell "skeleton"
- [x] TP-02 — Ehrlicher Quickstart "Switch to Real Hardware" (AC-45): Keine Behauptung sofort lauffähigem Real-Testing, Verweis auf Treiber-Implementierung + docs/architecture.md
- [x] TP-03 — Frontend rendert `real_status` sichtbar (AC-45 UI): `realStatusBadge()` in `app.js` für Hardware- und Infra-Einträge

### G — Gate-Konformität
- [x] TG-01 — ruff clean, mypy --strict clean (data.py, models.py, help.py, runner.py), Dashboard-Coverage ≥ 80 %
- [x] TG-02 — `make verify` EXIT 0: **710 passed (689+21 neue), 0 failed**, Coverage 91%, AC-22 (15 skipped), AC-01..AC-44 regressionsfrei

## Done-Gate Status
**GRÜN — 710 Tests, ruff clean, mypy --strict clean, Coverage 91%, AC-22 (15 skipped)**
**AC-45..AC-50 (§16): alle erfüllt**
**Iteration 8 (§16 Nachschärfung): Gate grün — 710 passed 0 failed**
