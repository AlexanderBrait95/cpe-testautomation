# Plan: CPE Test-Automation Framework (P1 / Done-Gate)

**Abgeleitet aus:** spec.md v1.0 (AC-01..AC-22), requirement.md v1.0
**Stand:** 2026-06-21, PLAN-Phase Iteration 1 (nach VERIFY)
**Verify-Verdikt:** `gaps_found` — 2 Lücken integriert (Gruppe Z, priorisiert ganz oben).
Basis-Build T01–T40 vollständig & grün; nur Nachschärfung offen.

Reihenfolge = Build-Reihenfolge (Dependencies aufsteigend). Jede Task ist einzeln
verifizierbar. Gate-Nachweis pro Task in Spalte „Test/Nachweis". Globales Gate: `make verify`.

---

## Gruppe Z — Verify-Lücken (PRIORITÄT, vor allem anderen abarbeiten)

> Quelle: `.autopilot/verify-report.md` (2026-06-21, Commit 15a9104). Basis-Build ist grün;
> diese Tasks schließen die im VERIFY gefundenen Gate-/Doku-Lücken.

### T41 — Gate deckt Framework-Unit-Tests ab (Gap 1, MEDIUM)
- **Problem:** `make verify` läuft nur `-m headless`; 142 reine Framework-Unit-Tests
  (`test_criteria.py` 40, `test_selection.py` 30, `test_config.py` 22, `test_errors.py` 22,
  `tests/hal/test_inventory.py` 16, `test_cli_inventory.py` 12) laufen NICHT im Gate — obwohl
  AC-11 (criteria) und AC-19 (CLI inventory-validate) genau diese Suiten benennen. Regression
  dort ließe `make verify` weiterhin exit 0 → untergräbt §11 („make verify = einziges Gate").
- **Akzeptanzkriterium:** Das einzige Gate-Kommando führt die AC-11/AC-19-Unit-Suiten mit aus.
  Umsetzung: Gate-Selektor auf `-m "not hardware"` umstellen (bevorzugt, deckt headless +
  untagged ab) ODER `headless`-Marker an die 142 Unit-Tests ergänzen. `pytest -m hardware`
  muss weiterhin ausschließlich `skipped` liefern (AC-22 darf nicht brechen). Coverage-Gate
  ≥80 % bleibt erfüllt.
- **Dateien:** `Makefile` (verify-Target), ggf. `.gitlab-ci.yml`/`Jenkinsfile` (Test-Stage
  synchron halten), ggf. `pyproject.toml` (Marker-Doku).
- **Test/Nachweis:** `make verify` exit 0 und Run-Output zeigt ≥559 ausgeführte Tests
  (417 headless + 142 Unit); `pytest -m hardware` weiterhin alle `skipped`.

### T42 — Deferred-Matrix bereinigen (Gap 2, LOW)
- **Problem:** `docs/deferred-matrix.md` listet `test_fw_flash_real` und `test_fw_rollback_real`,
  die als Testfunktionen nicht existieren (Über-Listung, kosmetisch).
- **Akzeptanzkriterium:** Jeder in der Deferred-Matrix gelistete Test existiert real als
  `@hardware`-Testfunktion ODER der Eintrag wird entfernt/als „geplant (P2)" klar markiert.
  Konsistenz: Anzahl gelisteter Tests == Anzahl real vorhandener `@hardware`-Tests (15).
- **Dateien:** `docs/deferred-matrix.md` (ggf. `tests/dut/` falls Tests stattdessen ergänzt werden).
- **Test/Nachweis:** Abgleich Matrix ↔ `pytest -m hardware --collect-only`; keine Geister-Einträge.

---

## Gruppe A — Projekt-Skelett & Tooling

### T01 — Projekt-Bootstrap & Build-Tooling
- **Akzeptanzkriterium:** `pip install -e .` funktioniert; `cpe-ta --help` startet; `make lint`,
  `make test`, `make verify` Targets existieren. (AC-17 Vorbedingung, §9)
- **Dateien:** `pyproject.toml`, `requirements.txt`, `Makefile`, `cpe_ta/__init__.py`,
  `cpe_ta/cli.py` (Stub), `.gitignore`, `ruff.toml`/`[tool.ruff]`, `[tool.mypy]`.
- **Test/Nachweis:** `pip install -e . && cpe-ta --help` exit 0; `make` Targets vorhanden.

### T02 — Fehlertaxonomie
- **Akzeptanzkriterium:** Typisierte Exceptions (HardwareError, DUTError, TimeoutError-Wrapper,
  ConfigError) trennen `error` von `fail`. (§7, Scope-Log Fehler-Klassifikation)
- **Dateien:** `cpe_ta/core/errors.py`, `tests/framework/test_errors.py`.
- **Test/Nachweis:** Unit-Test: Hierarchie + Klassifikation `is_infrastructure_error()`.

---

## Gruppe B — Core: Config, Inventar, Selektion, Kriterien

### T03 — Config-Modelle (Pydantic v2)
- **Akzeptanzkriterium:** Pydantic-Modelle Testbed/WiringMap/Inventory/Profiles validieren YAML;
  ungültige Config → ConfigError vor Lauf. (REQ-HW-01, §7, AC-19 Vorbedingung)
- **Dateien:** `cpe_ta/core/config.py`, `tests/framework/test_config.py`, `testbed.example.yaml`.
- **Test/Nachweis:** Unit: gültiges + defektes YAML (doppelter Port, fehlende Rolle).

### T04 — Wiring-Map / Inventory-Auflösung
- **Akzeptanzkriterium:** Logische Rolle („DUT-LAN-1") → physisch `switch:port`; Fehlerfall „Rolle
  nicht verkabelt" wirft typisiert. (HAL-AC-4 / **AC-05**)
- **Dateien:** `cpe_ta/core/inventory.py`, `tests/hal/test_inventory.py`.
- **Test/Nachweis:** `pytest tests/hal/test_inventory.py` grün inkl. Negativfall.

### T05 — `inventory-validate` CLI-Befehl
- **Akzeptanzkriterium:** `cpe-ta inventory-validate testbed.example.yaml` exit 0; defektes Inventar
  exit ≠ 0, klare Meldung ohne Traceback. (**AC-19**, §7)
- **Dateien:** `cpe_ta/cli.py`, `tests/framework/test_cli_inventory.py`.
- **Test/Nachweis:** Subprocess/CliRunner: beide Exit-Codes geprüft.

### T06 — Pass/Fail-Methodik (criteria.py)
- **Akzeptanzkriterium:** `PerfCriterion` (tolerance/duration/transport/tool/repetitions/aggregate/
  threshold); RFC-2544 + RFC-6349 Presets; Aggregat (median/min/p95) + Schwellvergleich rein &
  deterministisch; fehlende Schwelle → skip (kein stiller Pass). (**AC-11**, REQ-CRIT-01..03)
- **Dateien:** `cpe_ta/core/criteria.py`, `profiles/rfc2544.yaml`, `profiles/rfc6349.yaml`,
  `tests/framework/test_criteria.py`.
- **Test/Nachweis:** Unit: Aggregate, Schwelle pass/fail, fehlende Schwelle → skip-Signal.

### T07 — Tag-/Capability-Selektion + Skip-Logik (pytest-Plugin)
- **Akzeptanzkriterium:** Marker `smoke/full/regression/tech_*/headless/hardware`; `-m "smoke and
  headless"` selektiert; Capability-Mismatch → `skip` statt `fail`. (**AC-07**, REQ-ARCH-01, REQ-DUT-03)
- **Dateien:** `cpe_ta/core/selection.py`, `conftest.py` (Marker-Registrierung + capability-skip-
  Hook), `pyproject.toml` (markers), `tests/framework/test_selection.py`.
- **Test/Nachweis:** Meta-Test: Selektion + capability-skip; `pytest -m "smoke and headless"` grün.

---

## Gruppe C — HAL (Interfaces + Simulatoren + reale Skelette)

### T08 — HAL Base-Interfaces (Protocols/ABCs)
- **Akzeptanzkriterium:** ABCs/Protocols für Switch, PDU, SerialConsole, RFAttenuator, USBRelay mit
  Pflichtmethoden + Rückgabetypen + Fehlerverhalten. (§3 Tabelle, AC-02 Vorbedingung)
- **Dateien:** `cpe_ta/hal/base.py`.
- **Test/Nachweis:** `mypy --strict cpe_ta/hal/base.py` ohne Fehler (Teil AC-17).

### T09 — HAL-Simulatoren (deterministisch, in-memory)
- **Akzeptanzkriterium:** Je Interface ≥1 Simulator (sim_switch/sim_pdu/sim_serial/sim_rf/
  sim_usbrelay), zustandsbehaftet, ohne externe Verbindung; Fehlerinjektion konfigurierbar. (§3, §7)
- **Dateien:** `cpe_ta/hal/sim/*.py`, `tests/hal/test_sim_instruments.py`.
- **Test/Nachweis:** `pytest tests/hal -m headless` grün ohne Hardware (**AC-03**).

### T10 — HAL reale Treiber-Skelette
- **Akzeptanzkriterium:** Treiber-Skelette (snmp_switch, netconf_switch, pdu_http, serial, rf, usb)
  implementieren die Interfaces; Vendor-Libs (pysnmp/ncclient/pyserial/paramiko) NUR hier. (REQ-HW-03)
- **Dateien:** `cpe_ta/hal/drivers/*.py`.
- **Test/Nachweis:** Vollständigkeits-Meta-Test (mit AC-02); Layering-Test erlaubt Imports nur hier.

### T11 — Instrument-Factory (real|sim per Config)
- **Akzeptanzkriterium:** `factory.py` erzeugt real- oder sim-Instrument allein aus Config/Flag;
  Testfälle bleiben bei real↔sim-Wechsel unverändert. (HAL-AC-5 / **AC-06**)
- **Dateien:** `cpe_ta/hal/factory.py`, `tests/hal/test_factory_switch.py`.
- **Test/Nachweis:** Parametrisierter Test (sim + skelett) ohne Testfall-Änderung grün.

### T12 — HAL-Vollständigkeits-Meta-Test
- **Akzeptanzkriterium:** Meta-Test prüft, dass jedes Interface real-Skelett + Simulator hat. (**AC-02**)
- **Dateien:** `tests/framework/test_hal_completeness.py`.
- **Test/Nachweis:** Test grün; fehlende Impl. lässt ihn rot werden.

---

## Gruppe D — DUT-Abstraktion

### T13 — DUT Base-Interface + Capability-Modell
- **Akzeptanzkriterium:** CPE-Interface (factory_reset, power, console, config_backup/restore,
  fw_flash+rollback); Capability-Modell (Ports, Bänder, Linkspeed, VoIP, Tech). (REQ-DUT-01, REQ-CTRL-01..05)
- **Dateien:** `cpe_ta/dut/base.py`, `cpe_ta/dut/capabilities.py`.
- **Test/Nachweis:** `mypy --strict` clean; Capability-Match-Unit-Test.

### T14 — TR-098 ↔ TR-181 Mapping-Layer
- **Akzeptanzkriterium:** Bidirektionaler Mapping-Layer unit-getestet. (**AC-10**, REQ-DUT-02)
- **Dateien:** `cpe_ta/dut/datamodel.py`, `tests/dut/test_datamodel_mapping.py`.
- **Test/Nachweis:** Unit: Roundtrip + repräsentative Parameter-Pfade.

### T15 — Sim-CPE (CWMP-Agent, Konfig-State, Stats) + Driver-Skelett
- **Akzeptanzkriterium:** Simuliertes CPE mit CWMP-Agent, Konfig-State, Counter/Status, WiFi-State-
  Modell; Vendor-Driver-Skelett (Adapter). (REQ-DUT-01, §4/§3.1 Sim-Basis)
- **Dateien:** `cpe_ta/dut/sim/sim_cpe.py`, `cpe_ta/dut/drivers/generic.py`,
  `tests/dut/test_sim_cpe.py`.
- **Test/Nachweis:** `pytest tests/dut -m headless` grün.

---

## Gruppe E — Referenz-Infra-Abstraktion

### T16 — Infra Base-Interfaces
- **Akzeptanzkriterium:** Interfaces ACS, RADIUS, DHCP/DNS, SIP/IMS, Traffic-Endpoint, NTP,
  Fileserver — einheitlich, real|sim umschaltbar. (REQ-INF-01)
- **Dateien:** `cpe_ta/infra/base.py`.
- **Test/Nachweis:** `mypy --strict`-tauglich; konsumiert in T17.

### T17 — Infra-Simulatoren + reale Adapter-Skelette
- **Akzeptanzkriterium:** Sim je Dienst (ACS/CWMP, RADIUS, DHCP, Traffic mit synthetischen
  Durchsatz-/Latenzkurven, SIP); reale Adapter-Skelette (GenieACS-NBI etc.) gekapselt. (REQ-INF-01, §5/§10)
- **Dateien:** `cpe_ta/infra/sim/*.py`, `cpe_ta/infra/real/*.py`, `tests/framework/test_infra_sim.py`.
- **Test/Nachweis:** Determinismus der Traffic-Kurven; Sim-Läufe grün.

---

## Gruppe F — Runner, Reporting, Persistenz

### T18 — Test-Session-Runner (Setup/Teardown/Idempotenz)
- **Akzeptanzkriterium:** Fixtures `testbed/dut/infra/criteria` erzwingen Ausgangszustand; Teardown-
  Fehler wird geloggt ohne Run-Korruption; Reihenfolge-unabhängig. (REQ-ARCH-02 / **AC-08**)
- **Dateien:** `cpe_ta/core/runner.py`, `conftest.py` (Fixtures), `tests/framework/test_reorder.py`.
- **Test/Nachweis:** Reorder-Meta-Test grün (Tests in verschiedener Reihenfolge).

### T19 — Nebenläufigkeit (xdist-Isolation)
- **Akzeptanzkriterium:** Disjunkte VLAN-/Subnetz-/Instanz-Pools je Worker; kein Cross-Talk;
  `pytest -n 4 -m headless` grün. (REQ-ARCH-03 / **AC-09**)
- **Dateien:** `cpe_ta/core/runner.py` (Worker-Pool-Vergabe), `conftest.py`,
  `tests/framework/test_parallel_isolation.py`.
- **Test/Nachweis:** `pytest -n 4 -m headless` grün, Isolations-Assertions.

### T20 — Ergebnis-Modell + SQLite-Persistenz + Migrationen
- **Akzeptanzkriterium:** SQLite (WAL, transaktional) mit Schema-Version + Migrationen; je Run
  `run_id, firmware_version, dut_id, timestamp, git_sha`; Trend-Query über ≥2 Firmware-Stände.
  (REQ-RPT-02 / **AC-16**); `cpe-ta db-migrate`.
- **Dateien:** `cpe_ta/core/results.py`, `cpe_ta/cli.py` (db-migrate), `tests/framework/test_results_db.py`.
- **Test/Nachweis:** Unit: 2 simulierte Firmware-Runs → Trend-Query liefert Reihen.

### T21 — Reporting: JUnit-XML + HTML + Charts + PDF(optional)
- **Akzeptanzkriterium:** Lauf erzeugt valides JUnit-XML + HTML; PNG-Chart via matplotlib-Agg; PDF
  optional, fehlt WeasyPrint → graceful skip. (**AC-15**, REQ-RPT-01/03)
- **Dateien:** `cpe_ta/report/{junit,html,charts,pdf}.py`, `cpe_ta/cli.py` (report),
  `tests/framework/test_report.py`.
- **Test/Nachweis:** Report-Artefakte erzeugt + validiert; Chart-PNG existiert.

---

## Gruppe G — Layering-Invariante (HAL-AC-1)

### T22 — Import-Linter / Layering-Meta-Test
- **Akzeptanzkriterium:** Kein Modul in `cpe_ta/core`, `cpe_ta/report`, `tests/*` (außer `tests/hal`)
  importiert `pysnmp|ncclient|pyserial|paramiko|scapy`; Secret-Klartext-grep. (**AC-01**, HAL-AC-1, §8)
- **Dateien:** `tests/framework/test_layering.py`.
- **Test/Nachweis:** `pytest tests/framework/test_layering.py` grün; künstlicher Verstoß → rot.

### T23 — Determinismus-Meta-Test
- **Akzeptanzkriterium:** Zwei Läufe desselben Sim-Testsets → identischer normierter Ergebnis-Hash.
  (HAL-AC-3 / **AC-04**)
- **Dateien:** `tests/framework/test_determinism.py`.
- **Test/Nachweis:** Hash-Vergleich zweier Läufe identisch.

---

## Gruppe H — Domänen-Testfälle (headless, gegen Sim)

> **AC-12:** je Domäne ≥1 grüner headless-Test + Marker-Coverage-Meta-Test.

### T24 — LAN-Tests
- **AK:** Autonegotiation, Link-Flap/Recovery, VLAN-Tagging, MTU gegen Sim-Switch+Sim-CPE. (§3.1/3.2)
- **Dateien:** `tests/lan/test_*.py`. **Nachweis:** `pytest tests/lan -m headless` grün.

### T25 — WiFi-Logik-Tests
- **AK:** Security-Aushandlung OPEN/WPA2/WPA3/OWE, SSID-Sichtbarkeit, Guest, Steering (State-Machine);
  RF physisch = deferred. (§4). **Dateien:** `tests/wifi/test_*.py`. **Nachweis:** grün headless.

### T26 — QoS/Performance-Tests
- **AK:** Methodik-Engine gegen Traffic-Sim (synthetische Kurven), RFC-Profil-Anwendung. (§5, REQ-CRIT).
- **Dateien:** `tests/qos/test_*.py`. **Nachweis:** grün headless; nutzt criteria.py.

### T27 — WAN/Provisioning-Tests
- **AK:** PPPoE/IPoE-Statemachine, NAT/Port-Forwarding, Firewall Default-Deny (v4/v6). (§7).
- **Dateien:** `tests/wan/test_*.py`. **Nachweis:** grün headless.

### T28 — DHCP-Tests
- **AK:** Subnetze, statisch/dynamisch, Options 60/43/121/15/42/125, Pool-Stress-Logik. (§8.1/8.3/8.8).
- **Dateien:** `tests/dhcp/test_*.py`. **Nachweis:** grün headless.

### T29 — Multicast-Tests
- **AK:** IGMP/MLD Join/Leave-Statemachine, Zap-Time-Messlogik gegen Sim. (§8.2).
- **Dateien:** `tests/multicast/test_*.py`. **Nachweis:** grün headless.

### T30 — IPv6/Dual-Stack-Tests (Parametrisierung v4/v6/dualstack)
- **AK:** DHCPv6, SLAAC, PD, Firewall; läuft als Parametrisierung über Connectivity/DHCP/Firewall.
  (§2.7 / **AC-14**, REQ-IPV6-01). **Dateien:** `tests/ipv6/test_*.py` + Param in WAN/DHCP.
- **Nachweis:** parametrisierte Tests grün für alle drei Stacks.

### T31 — Security/EN-18031-Tests
- **AK:** Scan-Engine gegen Sim-Target (offene Ports, schwache TLS, Default-Creds) + EN-18031-
  Checklisten-Engine mit Status `pass|fail|manual` + Evidenz-Feld. (§9, REQ-SEC-03).
- **Dateien:** `cpe_ta/` Security-Engine-Modul (z. B. `core/security.py` oder `tests/security/`),
  `tests/security/test_*.py`. **Nachweis:** grün headless; EN-18031-Status-Mapping getestet.

### T32 — ACS/CWMP-RPC-Suite
- **AK:** Vollständige RPC-Suite gegen CWMP-Sim: Bootstrap, Get/Set/Add/Delete, Reboot,
  Diagnostics, ScheduleInform, Notifications. (**AC-13**, §10).
- **Dateien:** `tests/acs/test_*.py`. **Nachweis:** `pytest tests/acs -m headless` grün, alle RPCs.

### T33 — Stress/Soak (Kurzlauf headless)
- **AK:** Orchestrierung + Abbruchkriterien (Reboot-Detection, Memory-Leak-Heuristik via Sim-
  Konsolenmetriken); Kurzlauf headless, Langlauf deferred. (§6). **Dateien:** `tests/stress/test_*.py`.
- **Nachweis:** Kurzlauf grün headless.

### T34 — Marker-Coverage-Meta-Test
- **AK:** Meta-Test prüft: je Domäne (LAN, WiFi, QoS, WAN, DHCP, Multicast, IPv6, Security, ACS)
  ≥1 headless-Test vorhanden + ausgeführt. (**AC-12**).
- **Dateien:** `tests/framework/test_domain_coverage.py`. **Nachweis:** Test grün.

---

## Gruppe I — Hardware-deferred

### T35 — Repräsentative @hardware-Tests + Deferred-Matrix
- **AK:** `@hardware`-Tests werden bei fehlender Hardware sauber übersprungen (kein fail);
  `pytest -m hardware` → alle `skipped`; alle in `docs/deferred-matrix.md` gemappt auf Hardware.
  (**AC-22**, §4 deferred-Liste). **Dateien:** `tests/tech/`, `tests/{wifi,voip,usb}/test_hw_*.py`,
  `docs/deferred-matrix.md`. **Nachweis:** `pytest -m hardware` → ausschließlich skipped.

---

## Gruppe J — CLI, CI, Doku, Gate

### T36 — CLI vervollständigen (run/list/report/inventory-validate/db-migrate)
- **AK:** Alle Befehle funktional; `cpe-ta run -m "smoke and headless"` führt aus + erzeugt Report.
  (§9). **Dateien:** `cpe_ta/cli.py`, `tests/framework/test_cli.py`. **Nachweis:** CLI-Tests grün.

### T37 — CI-Templates
- **AK:** `.gitlab-ci.yml` + `Jenkinsfile` syntaktisch valide, Stages lint→typecheck→headless→report,
  Nightly-Regression-Stage. (**AC-20**, REQ-RPT-04). **Dateien:** `.gitlab-ci.yml`, `Jenkinsfile`.
- **Nachweis:** YAML/Jenkins-Lint im Meta-Test/`make verify` (mind. YAML-Parse).

### T38 — Dokumentation
- **AK:** README (Quickstart) + `docs/{architecture,testbed,deferred-matrix,writing-tests,criteria}.md`
  vollständig; deferred-matrix vollständig gemappt. (**AC-21**). **Dateien:** `README.md`, `docs/*.md`.
- **Nachweis:** Datei-Existenz + Inhalts-Check (Meta-Test prüft Pflichtdateien).

### T39 — Qualitäts-Gate: ruff + mypy + Coverage
- **AK:** `ruff check` ohne Fehler; `mypy --strict` auf `cpe_ta/core` + `cpe_ta/hal/base.py` ohne
  Fehler; Coverage `cpe_ta/core`+`cpe_ta/hal` ≥80 %. (**AC-17, AC-18**).
- **Dateien:** querschnittlich (Cleanup), `pyproject.toml` (cov-config). **Nachweis:** `make verify`.

### T40 — `make verify` Gate-Orchestrierung
- **AK:** `make verify` == ruff + mypy + `pytest -m "headless" -n auto --junitxml --cov` + report-gen;
  exit 0 ⇒ Done-Gate. (**§11 globales Gate**). **Dateien:** `Makefile`.
- **Nachweis:** `make verify` exit 0.

---

## Done-Gate-Mapping (Kontrolle)

AC-01→T22 · AC-02→T12 · AC-03→T09 · AC-04→T23 · AC-05→T04 · AC-06→T11 · AC-07→T07 ·
AC-08→T18 · AC-09→T19 · AC-10→T14 · AC-11→T06 · AC-12→T24-T34 · AC-13→T32 · AC-14→T30 ·
AC-15→T21 · AC-16→T20 · AC-17→T39 · AC-18→T39 · AC-19→T05 · AC-20→T37 · AC-21→T38 ·
AC-22→T35 · Gate→T40.

Alle 22 AC abgedeckt. Build-Phase startet mit T01.
