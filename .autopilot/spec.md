# Spezifikation: CPE Hardware- & Software-Acceptance-Test-Automation

**Version:** 1.0 (Spec abgeleitet aus requirement.md v1.0)
**Status:** SPEC final für Build-Phase P1
**Sprache Code/Doku:** Englisch im Code, Deutsch in Betriebs-/Onboarding-Doku zulässig.

---

## 0. Leitentscheidung für den Autopilot-Build

Das Requirement beschreibt ein **physisches Testlabor** (Managed Switches, PDUs, RF-Dämpfer,
serielle Konsolen-Server, USB-Relais, echte CPEs, DSL/DOCSIS/PON-Anschlüsse). Ein Autopilot
ohne angeschlossene Hardware kann das nur dann sinnvoll und verifizierbar bauen, wenn die
**gesamte Außenwelt hinter Abstraktionsschichten mit deterministischen Simulatoren** liegt.

Deshalb ist die **zentrale Architektur-Invariante** dieser Spec:

> **Businesslogik (Testfälle, Orchestrierung, Reporting) importiert NIEMALS Hardware- oder
> Vendor-Bibliotheken direkt — ausschließlich definierte Interfaces (HAL / DUT-Abstraktion /
> Reference-Infra-Abstraktion). Jedes Interface hat (a) eine reale Treiber-Implementierung
> und (b) einen vollständig headless lauffähigen, deterministischen Simulator.**

Daraus folgt die Aufteilung des Done-Gates:

- **Headless-verifizierbar (blockiert Done-Gate):** Framework-Kern, alle Abstraktions-Interfaces,
  alle Simulatoren, die capability-/methodikbasierte Test-Engine, Reporting/DB/Charts und ein
  repräsentativer Satz Testfälle, der **gegen die Simulatoren grün** läuft.
- **Hardware-deferred (dokumentiert, blockiert Done-Gate NICHT):** Testfälle, die zwingend echte
  Hardware/Anschluss/RF/Optik benötigen. Sie sind als solche markiert, werden bei fehlender
  Hardware capability-basiert übersprungen (nicht failen) und sind in einer Deferred-Matrix
  gelistet.

---

## 1. Technologie-Stack (verbindlich)

| Bereich | Wahl | Begründung |
|---|---|---|
| Sprache | Python 3.11+ | OSS-Ökosystem des Requirements (Scapy, iperf-Bindings, GenieACS-NBI per HTTP) ist Python-nah |
| Test-Runner | `pytest` + `pytest-xdist` | Requirement nennt pytest; xdist liefert Parallelisierung (REQ-ARCH-03) |
| Markierung/Selektion | pytest-Marker + Custom-Plugin | Tags Smoke/Full/Regression/Tech + capability-skip (REQ-ARCH-01, REQ-DUT-03) |
| Config/Modelle | YAML + `pydantic` v2 | maschinenlesbares Inventar/Wiring-Map, validiert (REQ-HW-01) |
| HAL-Transport real | `pysnmp`, `ncclient` (NETCONF), `requests` (REST), `pyserial`, `paramiko` | hinter Treibern gekapselt, nie im Test |
| DUT CWMP | GenieACS NBI (HTTP) real + interner CWMP-Sim | §10 ACS-Tests |
| Traffic | iperf3-Wrapper real + Traffic-Sim | REQ-CRIT, §5 |
| Paket-Crafting | Scapy real + Sim-Hooks | Multicast/Firewall, §8.2/§7 |
| Reporting | pytest junit-xml + Jinja2-HTML + WeasyPrint(PDF, optional) | REQ-RPT-01 |
| Ergebnis-DB | SQLite (versioniert, Migrationsschema) | REQ-RPT-02 |
| Charts | `matplotlib` (headless Agg-Backend) | REQ-RPT-03 |
| Lint/Typen | `ruff` + `mypy --strict` (Kernmodule) | Qualitäts-Gate |
| Tests des Frameworks | `pytest` (Meta-Tests) + `coverage` | siehe Done-Gate |
| CI | GitLab-CI- + Jenkinsfile-Templates | REQ-RPT-04 |

Begründung Stack-Fokus: Der Autopilot baut **Framework + Simulatoren + Testfälle**, nicht das
physische Labor. Reale Treiber werden mit klarem Interface und Stub-Verhalten implementiert, aber
nur die Simulator-Pfade sind im Done-Gate verifizierbar.

---

## 2. Architektur & Modulstruktur

```
cpe_ta/                         # Python-Package (Framework-Kern)
  core/
    config.py                   # Pydantic-Modelle: Testbed, WiringMap, Inventory, Profiles
    inventory.py                # Wiring-Map-Auflösung: logische Rolle -> physischer Port
    runner.py                   # Test-Session, Setup/Teardown-Orchestrierung, Idempotenz
    selection.py                # Tag-/Capability-Selektion, Skip-Logik
    criteria.py                 # Pass/Fail-Methodik (Toleranz, Aggregat, RFC-Profile)
    results.py                  # Ergebnis-Modell, SQLite-Persistenz, Migrationen
    errors.py                   # Fehlertaxonomie (Hardware/DUT/Timeout/Config)
  hal/                          # Hardware-Abstraktionsschicht (Testbett-Instrumente)
    base.py                     # Protocols/ABCs: Switch, PDU, SerialConsole, RFAttenuator, USBRelay
    drivers/                    # reale Treiber (snmp_switch.py, netconf_switch.py, pdu_http.py ...)
    sim/                        # Simulatoren (sim_switch.py, sim_pdu.py, ...) — deterministisch
    factory.py                  # Instrument-Factory aus Config (real|sim per Flag)
  dut/                          # DUT-Abstraktion
    base.py                     # CPE-Interface (reset, power, console, config b/r, fw-flash)
    datamodel.py                # TR-098 <-> TR-181 Mapping-Layer
    capabilities.py             # Capability-Modell (Ports, Bänder, Linkspeed, VoIP, Tech)
    drivers/                    # Vendor-/Modell-Treiber (Adapter-Pattern)
    sim/                        # simuliertes CPE (CWMP-Agent, Konfig-State, Stats)
  infra/                        # Referenz-Infrastruktur-Abstraktion
    base.py                     # ACS, RADIUS, DHCP/DNS, SIP/IMS, Traffic-Endpoint, NTP, Fileserver
    real/                       # Adapter (GenieACS-NBI, FreeRADIUS, Kea, iperf3, Kamailio ...)
    sim/                        # Simulatoren je Referenzdienst
  report/
    junit.py  html.py  charts.py  pdf.py
  cli.py                        # Einstiegspunkt: cpe-ta run/list/report/inventory-validate
tests/                          # Testfall-Bibliothek (pytest), nach Domäne gegliedert
  hal/ dut/ lan/ wifi/ qos/ wan/ dhcp/ multicast/ security/ acs/ ipv6/ stress/ voip/ usb/ tech/
  framework/                    # Meta-Tests: testen das Framework selbst
conftest.py                     # Fixtures: testbed, dut, infra, criteria; real|sim-Schalter
testbed.example.yaml            # Beispiel-Inventar + Wiring-Map
docs/                           # Architektur, Betrieb, Onboarding, Deferred-Matrix
```

### 2.1 Querschnitts-Anforderungen (Mapping zu REQ-ARCH/DUT/INF)
- **REQ-ARCH-01** Tag-Selektion: Marker `smoke`, `full`, `regression`, `tech_dsl|docsis|pon|fwa`,
  `headless`, `hardware`. CLI: `cpe-ta run -m "smoke and headless"`.
- **REQ-ARCH-02** Idempotenz: jeder Test über Fixture `dut`/`testbed` mit erzwungenem
  Setup→bekannter Ausgangszustand→Teardown; Tests dürfen keine Reihenfolge voraussetzen.
- **REQ-ARCH-03** Parallelität: `pytest -n` mit VLAN-/Instanz-Isolation pro Worker; der Sim-Mode
  vergibt disjunkte virtuelle VLANs/Subnetze pro Worker.
- **REQ-DUT-01/02/03** Adapter-Pattern, TR-098/TR-181-Mapping-Layer, Capability-getriebenes Skip.
- **REQ-INF-01** Referenzdienste über einheitliches Interface, real|sim umschaltbar.

---

## 3. HAL-Anforderungen (Akzeptanz-relevant)

Jedes Instrument-Interface ist eine ABC/Protocol mit definierten Methoden, Rückgabetypen und
Fehlerverhalten. Für **jedes** Interface existiert real-Treiber-Skelett **und** deterministischer
Simulator. Simulatoren sind zustandsbehaftet, in-memory, ohne externe Verbindung lauffähig.

| Interface | Pflichtmethoden (Auszug) | Requirement |
|---|---|---|
| `Switch` | `port_enable/disable`, `set_speed_duplex`, `set_vlan`, `get_port_stats`, `set_mirror` | REQ-HW-04..08 |
| `PDU` | `power_on/off/cycle`, `get_outlet_state` | REQ-HW-09, REQ-CTRL-02 |
| `SerialConsole` | `open`, `read_until`, `send`, `read_metrics(cpu/ram)` | REQ-HW-10, REQ-CTRL-03 |
| `RFAttenuator` | `set_attenuation_db`, `get_attenuation`, `isolate` | REQ-HW-11 |
| `USBRelay` | `set_channel`, `pulse(button)` | REQ-HW-12 |
| `CPE` (DUT) | `factory_reset`, `power(via PDU)`, `console`, `config_backup/restore`, `fw_flash(rollback)` | REQ-CTRL-01..05 |

**HAL-Akzeptanzkriterien (HAL-AC):**
- **HAL-AC-1:** Kein Modul unter `cpe_ta/core`, `tests/*` (außer `tests/hal`) und `report/` importiert
  `pysnmp|ncclient|pyserial|paramiko|scapy` direkt — geprüft durch Meta-Test (Import-Linter-Regel).
- **HAL-AC-2:** Jedes HAL-Interface hat ≥1 Simulator; `pytest tests/hal -m headless` läuft ohne
  jegliche Hardware grün.
- **HAL-AC-3:** Simulator-Determinismus: zwei aufeinanderfolgende Läufe desselben Testsets liefern
  identische Ergebnis-Snapshots (Meta-Test vergleicht Hash der normierten Ergebnisse).
- **HAL-AC-4:** Wiring-Map-Auflösung: Testfälle adressieren logische Rollen („DUT-LAN-1"); Auflösung
  auf physische `switch:port` ist getestet inkl. Fehlerfall „Rolle nicht verkabelt".
- **HAL-AC-5:** Treiber-Austausch bricht keine Tests: Wechsel real↔sim erfolgt nur über
  `factory.py`/Config; Testfälle bleiben unverändert (verifiziert durch Parametrisierung des
  conftest-Schalters).

---

## 4. Test-Taxonomie: headless vs. hardware-deferred

Jeder Testfall trägt genau eine Ausführungsklasse:

- `@headless` — vollständig gegen Simulatoren lauffähig. **Done-Gate-relevant.**
- `@hardware` — benötigt physische Hardware/Anschluss. Wird ohne Hardware capability-übersprungen
  (`pytest.skip` mit Grund), nie failen. Gelistet in `docs/deferred-matrix.md`.

**Headless abbildbar (P1-MVP, müssen grün sein):**
- LAN-Logik: Autonegotiation-Verhandlung, Link-Flap/Recovery, VLAN-Tagging, MTU — gegen Sim-Switch
  + Sim-CPE (Counter/Status-Modell). (§3.1/3.2)
- WiFi-Logik (Zustandsmaschine): Security-Modus-Aushandlung OPEN/WPA2/WPA3/OWE, SSID-Sichtbarkeit,
  Guest-Netz, Band/SSID-Steering — gegen Sim-CPE-WiFi-Modell; **physische RF-Messung = deferred**. (§4)
- QoS/Performance: Methodik-Engine (Toleranz, Aggregat, RFC-2544/6349-Profil) gegen
  Traffic-Simulator mit konfigurierbaren synthetischen Durchsatz-/Latenzkurven. (§5, REQ-CRIT)
- WAN/Provisioning: PPPoE/IPoE-Zustandsaufbau, NAT/Port-Forwarding-Regelprüfung, Firewall
  Default-Deny (v4/v6) — gegen Sim-CPE + Sim-Infra. (§7)
- DHCP: Subnetze, statisch/dynamisch, Options (60/43/121/15/42/125), Pool-Stress-Logik. (§8.1/8.3/8.8)
- Multicast: IGMP/MLD Join/Leave-Statemachine, Zap-Time-Messlogik gegen Sim. (§8.2)
- IPv6/Dual-Stack: DHCPv6, SLAAC, PD, Firewall, DS-Lite/MAP-T-Profil-Schalter. (§2.7)
- Security: Scan-Orchestrierung gegen Sim-Target (offene Ports, schwache TLS, Default-Creds) +
  EN-18031-Checklisten-Engine (Status `pass|fail|manual`). (§9)
- ACS/CWMP: vollständige RPC-Suite gegen internen CWMP-Sim **und** optional gegen reale GenieACS-
  Instanz; Bootstrap, Get/Set/Add/Delete, Reboot, Diagnostics, ScheduleInform, Notifications. (§10)
- Stress/Soak: Orchestrierung + Abbruchkriterien (Reboot-Detection, Memory-Leak-Heuristik via
  Sim-Konsolen-Metriken); Kurzlauf headless, Langlauf deferred-konfigurierbar. (§6)

**Hardware-deferred (dokumentiert, nicht blockierend):**
- Echte RF-Durchsatz-/Roaming-/DFS-Messungen (§4.3, §5 physisch), reale optische Pegel/PON-
  Registrierung (§11.3), DSL-Sync/SNR an echter Leitung (§11.1), DOCSIS-Channel-Lock an echtem
  CMTS (§11.2), echter VoIP-Audio-Pfad/T.38 (§8.5 physisch), USB-Medien an echtem Stick (§8.4),
  USB-C PD (§8.6), LED-Photometrie (§8.7), echter Firmware-Flash auf physischem DUT.

---

## 5. Pass/Fail-Methodik (REQ-CRIT)

- **REQ-CRIT-01:** `criteria.py` definiert ein `PerfCriterion`-Modell: `tolerance`, `duration_s`,
  `transport (TCP|UDP)`, `tool`, `repetitions`, `aggregate (median|min|p95)`, `threshold`.
- **REQ-CRIT-02:** Referenz-Profile RFC 2544 (L2/L3) und RFC 6349 (TCP-Goodput) als Presets.
- **REQ-CRIT-03:** Linerate-Schwellen je Interface/Standard aus Config (`profiles/*.yaml`),
  fehlende Schwelle → Test `skip` mit klarer Meldung (kein stiller Pass).
- Aggregation und Schwellvergleich sind reine, unit-getestete Funktionen (deterministisch).

---

## 6. Persistenz, Reporting, Idempotenz, Nebenläufigkeit

- **REQ-RPT-01:** JUnit-XML (CI) + HTML (Mensch); PDF optional, fehlt WeasyPrint → graceful skip.
- **REQ-RPT-02:** SQLite-Ergebnis-DB mit Schema-Version + Migrationen; jeder Run mit
  `run_id, firmware_version, dut_id, timestamp, git_sha`. Trend-Query über Firmware-Stände.
- **REQ-RPT-03:** Charts (Durchsatz/Latenz-Verläufe) headless via matplotlib-Agg in PNG.
- **Idempotenz/Recovery:** Setup/Teardown stellen definierten Zustand her; bei Teardown-Fehler
  wird der Fehler geloggt, der Run aber nicht korrumpiert; DB-Schreibvorgänge transaktional.
- **Nebenläufigkeit:** xdist-Worker erhalten disjunkte VLAN-/Subnetz-/Instanz-Pools; DB-Zugriff
  serialisiert (WAL-Mode), keine Race-Conditions auf gemeinsamen Ressourcen.

---

## 7. Edge-Cases & Fehlerbehandlung (Pflicht)

- Ungültiges/inkonsistentes Inventar (Rolle ohne Verkabelung, doppelter Port) → Validierungsfehler
  vor Testlauf (`cpe-ta inventory-validate`), klare Meldung, Exit ≠ 0.
- Instrument-/DUT-Timeout, Verbindungsabbruch → typisierte Exceptions (`errors.py`), Test als
  `error` (≠ fail) klassifiziert, mit Diagnose-Kontext im Report.
- Leerer Zustand: kein DUT/leeres Inventar → verständliche Meldung, keine Tracebacks an Nutzer.
- Capability-Mismatch (z. B. WiFi-7-Test auf WiFi-5-DUT) → `skip` mit Grund, nicht `fail`.
- Simulator-Fehlerinjektion: Sim-Instrumente können konfigurierte Fehler/Flaps erzeugen, damit
  Recovery-/Negativ-Tests deterministisch prüfbar sind.

---

## 8. Sicherheit

- Secrets (ACS-/RADIUS-/Switch-Credentials, SNMP-Communities) nur via Env/Secret-File, niemals im
  Repo/Code; Config referenziert Secret-Namen, nicht Werte. Meta-Test grep't auf Klartext-Secrets.
- Input-Validierung aller Config-/Inventar-Eingaben über Pydantic.
- §9-Security-Tests: Scan-Engine, Default-Credential-Check, TLS-Versions-/Zertifikatsprüfung gegen
  Sim-Target; EN-18031-Mapping-Engine mit Status `pass|fail|manual` und Evidenz-Feld.
- CWMP/USP-TLS- und Zertifikatsvalidierung als eigener Testpfad (§9 REQ-SEC-03, §10).

---

## 9. Deployment & Betrieb

- Installierbar als Python-Package (`pip install -e .`), Einstieg über `cpe-ta` CLI.
- Befehle: `run`, `list`, `inventory-validate`, `report`, `db-migrate`.
- Reproduzierbar: `requirements.txt`/`pyproject.toml` mit Pin; `make test` / `make lint` Targets.
- Logging: strukturiert (Level konfigurierbar), Run-Logs je `run_id` ablegbar.
- CI: `.gitlab-ci.yml` + `Jenkinsfile` mit Stages lint→typecheck→headless-tests→report; Nightly-Job
  für `regression`-Marker (REQ-RPT-04).
- Recovery: Runs sind wiederanlaufbar; abgebrochener Run hinterlässt konsistente DB.

---

## 10. Dokumentation & Onboarding

- `README.md`: Quickstart (Install, `cpe-ta run -m "smoke and headless"`, Report öffnen).
- `docs/architecture.md`: Schichtenmodell, HAL-Invariante, real↔sim-Schalter.
- `docs/testbed.md`: Wiring-Map-/Inventar-Format mit `testbed.example.yaml`.
- `docs/deferred-matrix.md`: vollständige Liste hardware-deferred Tests + benötigte Hardware.
- `docs/writing-tests.md`: wie man capability-/methodikkonforme Testfälle schreibt.
- `docs/criteria.md`: RFC-2544/6349-Profile und Schwellwert-Pflege.

---

## 11. Definition of Done (MESSBAR) — Done-Gate des Autopilots

Der Build gilt als „grün", wenn ALLE folgenden Kriterien erfüllt sind. Jedes ist maschinell prüfbar.

**Architektur & HAL**
- **AC-01:** `pytest tests/framework/test_layering.py` grün → keine verbotenen Hardware-/Vendor-
  Imports in Businesslogik (HAL-AC-1).
- **AC-02:** Für jedes HAL-Interface (`Switch, PDU, SerialConsole, RFAttenuator, USBRelay, CPE`)
  existiert real-Skelett + Simulator; Meta-Test prüft Vollständigkeit der Implementierungen.
- **AC-03:** `pytest tests/hal -m headless` grün ohne Hardware (HAL-AC-2).
- **AC-04:** Determinismus-Test grün: zwei Läufe → identischer Ergebnis-Hash (HAL-AC-3).
- **AC-05:** Wiring-Map-Auflösung inkl. Fehlerfall getestet (HAL-AC-4).
- **AC-06:** real↔sim-Wechsel ohne Testfall-Änderung verifiziert (HAL-AC-5).

**Engine & Methodik**
- **AC-07:** Tag-/Capability-Selektion getestet: `-m "smoke and headless"`, capability-skip statt
  fail (REQ-ARCH-01, REQ-DUT-03).
- **AC-08:** Idempotenz: Tests laufen in beliebiger Reihenfolge grün (Reorder-Meta-Test) (REQ-ARCH-02).
- **AC-09:** Parallelität: `pytest -n 4 -m headless` grün ohne Cross-Talk (REQ-ARCH-03).
- **AC-10:** TR-098↔TR-181-Mapping-Layer unit-getestet (REQ-DUT-02).
- **AC-11:** `criteria.py` (Aggregat/Schwelle/RFC-Profile) unit-getestet; fehlende Schwelle → skip
  (REQ-CRIT-01..03).

**Domänen-Testabdeckung (headless, gegen Sim)**
- **AC-12:** Je Domäne ≥1 grüner headless-Testfall vorhanden und ausgeführt für: LAN, WiFi-Logik,
  QoS, WAN, DHCP/Options, Multicast, IPv6/Dual-Stack, Security/EN-18031, ACS/CWMP. Meta-Test prüft
  Marker-Coverage je Domäne.
- **AC-13:** ACS-RPC-Suite gegen CWMP-Sim grün (Bootstrap, Get/Set/Add/Delete, Reboot,
  Diagnostics, ScheduleInform, Notifications) (§10).
- **AC-14:** IPv6 läuft als Parametrisierung (v4/v6/dualstack) über Connectivity-/DHCP-/Firewall-
  Tests (REQ-IPV6-01).

**Reporting & Persistenz**
- **AC-15:** Lauf erzeugt valides JUnit-XML + HTML-Report; PNG-Chart wird generiert (REQ-RPT-01/03).
- **AC-16:** Ergebnisse landen in SQLite mit Run-Metadaten; Trend-Query über ≥2 simulierte
  Firmware-Stände liefert Reihen (REQ-RPT-02).

**Qualität & Betrieb**
- **AC-17:** `ruff check` ohne Fehler; `mypy --strict` auf `cpe_ta/core` + `cpe_ta/hal/base.py`
  ohne Fehler.
- **AC-18:** Coverage des Framework-Kerns (`cpe_ta/core`, `cpe_ta/hal`) ≥ 80 % (gemessen, geloggt).
- **AC-19:** `cpe-ta inventory-validate testbed.example.yaml` exit 0; defektes Inventar exit ≠ 0.
- **AC-20:** CI-Templates (`.gitlab-ci.yml`, `Jenkinsfile`) vorhanden und syntaktisch valide;
  Nightly-Regression-Stage definiert (REQ-RPT-04).
- **AC-21:** Doku vollständig: README + die fünf `docs/*`-Dateien inkl. `deferred-matrix.md` mit
  allen hardware-deferred Tests gemappt auf benötigte Hardware.

**Hardware-deferred (NICHT blockierend, nur Nachweis der Existenz)**
- **AC-22:** Alle `@hardware`-Tests sind in `docs/deferred-matrix.md` gelistet und werden bei
  fehlender Hardware sauber übersprungen (kein fail), nachgewiesen durch `pytest -m hardware`
  → alle `skipped`.

**Globales Gate-Kommando** (eine einzige reproduzierbare Verifikation):
```
make verify   # == ruff + mypy + pytest -m "headless" -n auto --junitxml --cov + report-gen
```
`make verify` exit 0 ⇒ Done-Gate erfüllt.

---

## 12. Phasen-Scope für den Autopilot

- **P1 (Done-Gate, dieser Build):** Kern-Framework, HAL+Simulatoren, DUT-Abstraktion+Sim,
  Referenz-Infra-Abstraktion+Sim, Methodik-Engine, Reporting/DB/Charts, headless-Testfälle der
  P1-Domänen (LAN, WiFi-Logik, QoS-Basis, WAN, DHCP/Options/Subnetze, Multicast, IPv6-Basis,
  Security-Scan+EN-18031-Engine, ACS/CWMP), CI-Templates, Doku, Deferred-Matrix.
- **P2 (Roadmap, Stubs+Marker erlaubt, nicht Gate-blockierend):** erweiterte WiFi (Roaming/Mesh/
  DFS), Latenzmetriken/Bufferbloat, Stress/Soak-Langlauf, DHCP-Pool-Stress real, USB-Medien, VoIP,
  LED, zugangsspezifische Tests (DSL/DOCSIS/PON physisch), EN-18031 vollständiges Mapping.
- **P3 (Roadmap):** USP/TR-369, USB-C PD, weitergehende Performance-Profile.

P2/P3-Domänen dürfen als headless-Logiktests vorhanden sein, soweit sinnvoll simulierbar; ihr
physischer Anteil ist deferred.

---

## 13. Offene Inputs (aus §13 Requirement — Defaults gesetzt, dokumentiert)

Diese Parameter blockieren P1 nicht; es werden dokumentierte Default-Profile in `profiles/` gesetzt
und in `docs/criteria.md`/`docs/testbed.md` als „anzupassen" markiert:
- Filesystem-Liste (§8.4), Mindestkapazitäten DHCP-Pool (§8.3).
- Provider-Provisioning-Profile (DHCP-Options-Sets, WAN-Modus).
- Linerate-Schwellwerte je Interface/Standard (REQ-CRIT-03).
- Vendor-/Modell-Liste der CPEs (DUT-Driver-Priorisierung) — Sim-CPE als Referenzmodell.
- Auswahl/Steuerschnittstelle der Switches/PDUs/Dämpfer — Sim-Treiber als Referenz, reale Treiber
  als Skelett mit dokumentierter Erweiterungsstelle.
```
```
_Spec erstellt: 2026-06-21 (Autopilot SPEC-Phase, Iteration 0)._
