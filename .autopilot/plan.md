# Plan: CPE Test-Automation — §15 Dashboard v2 (Bedien- & Onboarding-Console)

**Abgeleitet aus:** spec.md §15 (AC-32..AC-44) + scope-log.md (2026-06-22, §15) + research.md
**Stand:** 2026-06-22, PLAN-Phase
**Vorlauf-Verdikt (VERIFY Iteration 6):** `clean` — §14-Dashboard (AC-01..AC-31) vollständig erfüllt,
`make verify` EXIT 0, 620 passed. **Keine offene Lücke im Bestand.** Diese Iteration ist eine
**Spec-Erweiterung** (§15 wurde nach dem letzten clean-Lauf ergänzt), kein Gate-Reparatur-Run.

**Scope:** Ausschließlich die in §15.4 definierten neuen AC-32..AC-44. Die bestehenden AC-23..AC-31
bleiben unangetastet und müssen grün bleiben. **Kein neuer Test-Fachscope** (keine neue Domäne,
keine Hardware-Logik) — reine Bedien- + Onboarding-Schicht auf vorhandene Engine/Artefakte/Doku.
Architektur-Invariante bleibt: FastAPI-JSON-API + Vanilla-HTML/CSS/JS, kein Build/Node/CDN, offline.
Globales Gate bleibt `make verify` (exit 0).

---

## Befundbasis (verifizierter Ist-Stand, für BUILD verbindlich)

- **Backend `cpe_ta/dashboard/`:** `app.py` (6 Routen: overview/domains/runs/runs-id/testbed/POST-runs
  + active/progress), `data.py` (parse_junit, overview, domain_stats, get_run_summaries,
  get_run_detail, get_testbed_status, load_results), `runner.py` (`DashboardRunner`, `validate_marker`,
  injizierbare Command-Factory, shell=False), `models.py` (8 Modelle).
- **Frontend `cpe_ta/dashboard/static/`:** `index.html` (571 B, minimal), `app.css`, `app.js` (~12 KB,
  6 Views per fetch). Aktuell **6 Nav-Punkte**, Marker als Freitext, kein Help-View, keine Tooltips,
  keine handlungsleitenden Leerzustände, keine zentrale fetch-Fehlerbehandlung (zu verifizieren im BUILD).
- **Real definierte Interfaces (für AC-37 datengetrieben):**
  HAL `cpe_ta/hal/base.py` → `Switch, PDU, SerialConsole, RFAttenuator, USBRelay` (5 Protocols).
  DUT `cpe_ta/dut/base.py` → `CPE` (1 Protocol). **Zusammen die 6 in AC-37 geforderten Geräte.**
  Infra `cpe_ta/infra/base.py` → `ACSService, RADIUSService, DHCPService, TrafficEndpoint,
  SIPService, NTPService, FileServer` (7 Dienste, für AC-38).
- **Wiederverwendbare Validierung (AC-43):** `cpe_ta/core/inventory.py:validate_wiring_map` +
  `load_testbed` + `ConfigError` — identische Logik wie CLI `inventory-validate` (`cli.py:91`).
- **`DashboardRunner` kann noch NICHT abbrechen:** kein `cancel()`/`terminate`, kein Status
  `cancelled`. Muss für AC-33 ergänzt werden.
- **`/api/runs` & `/api/runs/{id}` haben KEINE Query-Filter** (AC-34) und keinen Export (AC-35).

---

## Gruppe V2-A — Onboarding-Datenmodell & `/api/help` (AC-36..AC-39, Kern des Feedbacks)

### TA-01 — Help-Content-Modul `help.py` (datengetrieben, mypy-strict)
- **Akzeptanzkriterium:** Neues Modul `cpe_ta/dashboard/help.py` mit reinen, unit-testbaren
  Funktionen, die ein Pydantic-`HelpContent`-Modell liefern, bestehend aus:
  (a) `quickstart`: geordnete, nicht-leere Schrittliste (Install → Inventar prüfen → smoke-Run →
  Report → sim→real) — AC-39;
  (b) `hardware`: **ein Eintrag pro real definiertem HAL/DUT-Interface** (`Switch, PDU, SerialConsole,
  RFAttenuator, USBRelay, CPE`) mit Feldern `name`, `purpose`, `connection`, `sim_available: bool` —
  AC-37. Die Geräteliste wird **aus den Interface-Namen abgeleitet** (z. B. Konstante, die gegen
  `hal/base.py`+`dut/base.py` per Meta-Test gegengeprüft wird), nicht im JS hartkodiert;
  (c) `infrastructure`: Eintrag pro Referenzdienst (`acs, radius, dhcp, sip, traffic, ntp, fileserver`)
  mit `purpose` + sim↔real-Hinweis + Verweis auf hardware-deferred — AC-38.
- **Betroffene Dateien:** `cpe_ta/dashboard/help.py` (neu), `cpe_ta/dashboard/models.py`
  (neue Modelle `HelpContent`, `HelpQuickstartStep`, `HelpDevice`, `HelpService`).
- **Test/Nachweis:** `mypy --strict cpe_ta/dashboard/help.py cpe_ta/dashboard/models.py` clean;
  Unit-Test in `tests/dashboard/test_help.py`: Quickstart nicht leer, 6 Hardware-Einträge mit allen
  Pflichtfeldern, 7 Infra-Keys vorhanden.

### TA-02 — Route `GET /api/help` in `app.py`
- **Akzeptanzkriterium:** `GET /api/help` liefert `200` + schema-konformes `HelpContent`-JSON aus dem
  Daten-Layer (`help.py`), keine JS-Hardkodierung. Importiert nur den Content-Layer, keine Engine-Interna.
- **Betroffene Dateien:** `cpe_ta/dashboard/app.py`.
- **Test/Nachweis:** TestClient `GET /api/help` → 200; Response enthält `quickstart`, `hardware`,
  `infrastructure`.

### TA-03 — Vollständigkeits-Meta-Test gegen reale Interfaces (Anti-Drift, AC-37)
- **Akzeptanzkriterium:** Meta-Test in `tests/dashboard/test_help.py` gleicht die Help-Hardware-Liste
  gegen die **real per `Protocol` definierten** Interfaces in `cpe_ta/hal/base.py` (Switch, PDU,
  SerialConsole, RFAttenuator, USBRelay) **und** `cpe_ta/dut/base.py` (CPE) ab. Fehlt ein Gerät in
  `help.py` oder kommt ein Interface hinzu, das nicht abgedeckt ist → Test **failt**. Analog
  Plausibilitätscheck der 7 Infra-Keys gegen `cpe_ta/infra/base.py`.
- **Betroffene Dateien:** `tests/dashboard/test_help.py` (neu).
- **Test/Nachweis:** `pytest tests/dashboard/test_help.py -q` grün; künstliches Entfernen eines
  Hardware-Eintrags lässt den Test rot werden (manuell verifiziert, nicht eingecheckt).

---

## Gruppe V2-B — Operations-Console Backend (AC-32, AC-33, AC-34, AC-35, AC-43)

### TB-01 — Run-Abbruch: `DashboardRunner.cancel()` + `POST /api/runs/active/cancel` (AC-33)
- **Akzeptanzkriterium:** `DashboardRunner` erhält `cancel()`, das den aktiven Subprocess sauber
  terminiert (`terminate()`, kurzer Join, ggf. `kill()`-Fallback), Status auf `cancelled` setzt und
  keinen Zombie hinterlässt. Route `POST /api/runs/active/cancel`: bei aktivem Run → `200` + Status
  `cancelled`; ohne aktiven Run → klare `404`/`409` (kein 500). `progress()` reflektiert `cancelled`.
- **Betroffene Dateien:** `cpe_ta/dashboard/runner.py`, `cpe_ta/dashboard/app.py`,
  `cpe_ta/dashboard/models.py` (Status-Wert `cancelled` zulässig).
- **Test/Nachweis:** `tests/dashboard/test_run_flow.py` (erweitert): Fake-Command (langlaufend, z. B.
  `python -c "import time; time.sleep(30)"`) starten → `running`, cancel → `cancelled`; zweiter Cancel
  ohne Run → 404/409.

### TB-02 — Filter/Sortierung für Run-History & Test-Liste (AC-34)
- **Akzeptanzkriterium:** `GET /api/runs` akzeptiert optionale Query-Params `status`, `domain`, `q`,
  `sort`; `GET /api/runs/{id}` akzeptiert `status`, `domain`, `q`. Filterung erfolgt in reinen
  Funktionen im Daten-Layer (`data.py`), nicht in der Route. Ohne Filter = vollständige Liste
  (Rückwärtskompatibilität zu AC-24). `sort` (z. B. `time|duration|status`, optional `-` für desc)
  ändert die Reihenfolge deterministisch. Ungültiger `sort`/`status`-Wert → tolerant (ignoriert oder
  `422`, dokumentiert), kein 500.
- **Betroffene Dateien:** `cpe_ta/dashboard/data.py` (neue Funktionen `filter_runs`,
  `filter_entries`, `sort_runs`), `cpe_ta/dashboard/app.py` (Query-Parameter).
- **Test/Nachweis:** `tests/dashboard/test_filter.py` (neu): Fixture mit gemischten Status/Domains;
  `?status=failed` liefert nur failed; `?domain=lan` nur lan; `?q=…` Freitext-Teilmenge;
  `?sort=duration` deterministische Ordnung; ohne Filter = volle Menge.

### TB-03 — Report-Export `GET /api/runs/{id}/export?format=junit|html` (AC-35)
- **Akzeptanzkriterium:** Liefert ein herunterladbares Artefakt mit korrektem `Content-Type`
  (`application/xml` für junit, `text/html` für html) **und** `Content-Disposition: attachment;
  filename=...`. Quelle: vorhandenes JUnit-XML (results_path bzw. Run-XML) und HTML-Report-Generator
  (`cpe_ta/report/html.py`, falls vorhanden — sonst minimaler HTML-Render aus den Run-Entries).
  Unbekannte `run_id` → `404`; unbekanntes `format` → `422`.
- **Betroffene Dateien:** `cpe_ta/dashboard/app.py`, ggf. kleine Hilfsfunktion in `data.py`
  (`render_run_html`/`run_junit_bytes`). Reuse von `cpe_ta/report/` wo vorhanden.
- **Test/Nachweis:** `tests/dashboard/test_export.py` (neu): junit → 200 + `application/xml` +
  Content-Disposition; html → 200 + `text/html`; bad format → 422; unbekannte run_id → 404.

### TB-04 — Inventar-Validierung aus der UI: `POST /api/inventory/validate` (AC-43)
- **Akzeptanzkriterium:** Route nimmt einen Inventar-Bezug (Pfad oder Default-`testbed.yaml`) und
  liefert für gültiges Inventar `{"ok": true, "errors": []}`, für defektes
  `{"ok": false, "errors": [...]}` (strukturierte Liste, **kein 500**, kein Traceback). Wiederverwendung
  von `load_testbed` + `validate_wiring_map` + `ConfigError` aus `cpe_ta/core/inventory.py` — äquivalent
  zur CLI `inventory-validate`. Testbed-View-Route (`/api/testbed`) zeigt weiterhin je Gerät/Dienst
  sim/real-Status (bereits vorhanden, ggf. minimal um real/sim-Feld geschärft).
- **Betroffene Dateien:** `cpe_ta/dashboard/app.py`, `cpe_ta/dashboard/models.py`
  (`InventoryValidateResult`), ggf. dünner Wrapper in `data.py`.
- **Test/Nachweis:** `tests/dashboard/test_inventory.py` (neu): gültige `testbed.example.yaml` → ok=true;
  absichtlich defektes Inventar (Rolle ohne Verkabelung/Doppelport) → ok=false + nicht-leere errors,
  Status 200 (kein 500).

---

## Gruppe V2-C — Frontend-Neubau (AC-32, AC-36, AC-40, AC-41, AC-42)

### TC-01 — 7. Navigationspunkt „Hilfe & Setup" + Routing `/#/help` (AC-36)
- **Akzeptanzkriterium:** `index.html`/`app.js` haben eine eigenständige „Hilfe & Setup"-View mit
  Hash-Route `/#/help`, die `GET /api/help` lädt und Quickstart, Hardware-Tabelle (pro Gerät: Zweck,
  Anschluss, Simulator verfügbar) und Infrastruktur-Liste rendert. Navigation umfasst nun **7 Views**.
- **Betroffene Dateien:** `cpe_ta/dashboard/static/index.html`, `app.js`, `app.css`.
- **Test/Nachweis:** Meta-Test `tests/dashboard/test_frontend.py` grep't Nav-Eintrag + Route `#/help`
  in `index.html`/`app.js`.

### TC-02 — Marker-Presets als Steuerelemente statt Freitext (AC-32)
- **Akzeptanzkriterium:** „Run starten"-View bietet **auswählbare Marker-Presets** (mind. `smoke`,
  `full`, `regression`, `headless`; zusätzlich `tech_dsl|docsis|pon|fwa`) als Checkbox/Radio/Button-
  Steuerelemente; der zusammengesetzte Marker-Ausdruck wird an `POST /api/runs` gesendet. Freitext darf
  als Zusatz bleiben, ist aber nicht mehr der einzige Pfad.
- **Betroffene Dateien:** `index.html`, `app.js`.
- **Test/Nachweis:** Meta-Test prüft Vorhandensein der Preset-Steuerelemente (mind. smoke/full/
  regression/headless) im Frontend-Markup; TestClient bestätigt, dass `POST /api/runs` einen
  Preset-Marker akzeptiert.

### TC-03 — Run-Abbruch-Button + Filter/Export-Bedienelemente (AC-33/34/35 UI-Seite)
- **Akzeptanzkriterium:** Aktiver Run zeigt einen **Abbrechen-Button** (`POST /api/runs/active/cancel`);
  Run-History & Test-Liste haben Filter-Controls (Status/Domain/Freitext) + Sortierung, die die neuen
  Query-Params nutzen; Run-Detail bietet Export-Links (junit/html) auf `/api/runs/{id}/export`.
- **Betroffene Dateien:** `index.html`, `app.js`, `app.css`.
- **Test/Nachweis:** Meta-Test grep't Cancel-Button + Filter-Controls + Export-Links im Frontend;
  Backend-Routen bereits durch TB-01/02/03 getestet.

### TC-04 — Handlungsleitende Leerzustände + Tooltips + zentrale fetch-Fehlerbehandlung (AC-40/41/42)
- **Akzeptanzkriterium:**
  (a) AC-40: Bei leeren Listen rendert `app.js` einen Hinweis mit Handlungsaufforderung (Verweis auf
  „Run starten"/Hilfe), nicht nur ein leeres Element — eigener Empty-State-Pfad.
  (b) AC-41: Schlüsselelemente (Marker-Auswahl, Run-Button, sim/real-Status) tragen Hilfetexte
  (`title=`/Tooltip) — **≥ 5 Hilfetext-Vorkommen** in `index.html`/`app.js`.
  (c) AC-42: zentrale `fetch`-Wrapper-Funktion in `app.js`, die nicht-2xx-Antworten abfängt und das
  strukturierte `{detail}` des Backends als lesbare Meldung anzeigt (kein roher Traceback).
- **Betroffene Dateien:** `index.html`, `app.js`, `app.css`.
- **Test/Nachweis:** Meta-Test in `test_frontend.py`: Empty-State-Pfad vorhanden, ≥5 `title=`/Tooltip-
  Vorkommen, zentrale Fehlerbehandlungsfunktion referenziert. Backend `{detail}`-Form via TestClient
  (AC-42-Backendseite) geprüft (z. B. 404/422 liefern `{"detail": ...}`).

---

## Gruppe V2-D — Qualitäts-Gate-Konformität (AC-44) + Gesamtverifikation

### TD-01 — Offline-/Asset-Meta-Test auf neue statische Assets ausweiten (AC-44/AC-29)
- **Akzeptanzkriterium:** Der bestehende Offline-Meta-Test (`test_offline.py`) deckt alle neuen/
  geänderten Assets ab: **keine** externen `http(s)://`/CDN-/Font-Referenzen; `index.html` lädt nur
  lokale `app.css`/`app.js`. Neue Help-View bringt keine externen Abhängigkeiten ein.
- **Betroffene Dateien:** `tests/dashboard/test_offline.py` (ggf. nur Re-Run, Glob deckt static/** ab).
- **Test/Nachweis:** `pytest tests/dashboard/test_offline.py -q` grün nach Frontend-Neubau.

### TD-02 — Lint/Typen/Coverage für erweiterte Dashboard-Module (AC-44)
- **Akzeptanzkriterium:** `ruff check cpe_ta/dashboard tests/dashboard` clean; `mypy --strict` clean
  für `cpe_ta/dashboard/data.py`, `models.py`, **neu `help.py`**; Dashboard-Backend-Coverage
  (`cpe_ta/dashboard` ohne `static/`) **≥ 80 %** inkl. der neuen Routen/Funktionen.
- **Betroffene Dateien:** ggf. kleine Folgekorrekturen in `runner.py`/`app.py`/`data.py`.
- **Test/Nachweis:** `ruff check …` exit 0; `mypy --strict …` no issues; Coverage-Report Dashboard-
  Subset ≥ 80 %.

### TD-03 — Globales Done-Gate `make verify` exit 0 (Regression-frei)
- **Akzeptanzkriterium:** `make verify` läuft **exit 0**: ruff clean, mypy clean, `pytest -m
  "not hardware"` 0 failed (Bestand 620 + neue tests/dashboard/-Tests), Coverage Kern ≥ 80 % &
  Dashboard ≥ 80 %. `pytest -m hardware` weiterhin nur `skipped` (AC-22 ungebrochen). **AC-23..AC-31
  bleiben grün** (keine Regression an Bestandsrouten/Offline-Nachweis).
- **Betroffene Dateien:** keine (reiner Verifikationslauf) + ggf. minimale Folgekorrekturen.
- **Test/Nachweis:** `make verify; echo $?` → `0`; Report zeigt neue `tests/dashboard/`-Tests
  (`test_help`, `test_filter`, `test_export`, `test_inventory`, `test_frontend`, erweitertes
  `test_run_flow`) ausgeführt; `pytest -m hardware -q` → nur skipped.

---

## Done-Gate-Mapping (Kontrolle §15.4)

| AC | Task(s) | Nachweis |
|---|---|---|
| AC-32 Marker-Presets | TC-02 | Meta-Test Preset-Controls + TestClient POST |
| AC-33 Run-Abbruch | TB-01, TC-03 | running→cancelled, 404/409 ohne Run |
| AC-34 Filter/Sort | TB-02, TC-03 | gefilterte Teilmengen, deterministische Sortierung |
| AC-35 Export | TB-03, TC-03 | Content-Type+Disposition, 404/422 |
| AC-36 Hilfe-View (7.) | TA-02, TC-01 | Nav + Route `/#/help` |
| AC-37 Hardware datengetrieben | TA-01, TA-03 | 6 Geräte, Anti-Drift-Meta-Test gegen base.py |
| AC-38 Infra + Modus | TA-01, TA-02 | 7 Infra-Keys + sim↔real |
| AC-39 Quickstart | TA-01, TC-01 | geordnete Schritte, gerendert |
| AC-40 Leerzustände | TC-04 | Empty-State-Pfad in app.js |
| AC-41 Tooltips | TC-04 | ≥5 Hilfetext-Vorkommen |
| AC-42 Fehlertexte | TB-* (`{detail}`), TC-04 | strukturierte Fehler + zentraler fetch-Handler |
| AC-43 Testbed/Validierung | TB-04 | ok/Fehlerliste, gültig+ungültig |
| AC-44 Gate-Konformität | TD-01, TD-02, TD-03 | ruff/mypy/Coverage/Offline + make verify exit 0 |

**Build-Reihenfolge:** V2-A (Help-Datenlayer) → V2-B (Backend-Routen) → V2-C (Frontend-Neubau) →
V2-D (Gate). Backend zuerst, damit das Frontend gegen reale Routen baut. Erwarteter Aufwand:
eine BUILD-Iteration; danach VERIFY gegen AC-32..AC-44.
