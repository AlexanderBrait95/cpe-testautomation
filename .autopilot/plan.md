# Plan: CPE Web-Dashboard (§14 / P1-Erweiterung)

**Abgeleitet aus:** spec.md v1.1 §14 + §14.5 (AC-23..AC-31), requirement.md §14
**Stand:** 2026-06-21, PLAN-Phase Iteration 4
**Verify-Verdikt der Vorrunde:** `clean` (betraf Kern-Framework AC-01..AC-22) — **keine offenen
Lücken**, daher keine Gruppe Z. Kern-Build T01–T42 vollständig & grün (559 Tests, Coverage 90 %).

**Scope dieser Iteration:** ausschließlich das **Web-Dashboard** als eigenständige Komponente
`cpe_ta/dashboard/` + Testsuite `tests/dashboard/`. Der bestehende Done-Gate (`make verify`,
`-m "not hardware"`) nimmt die neue Suite automatisch mit; AC-23..AC-31 erweitern §11.

**Reihenfolge = Build-Reihenfolge** (Dependencies aufsteigend). Jede Task einzeln verifizierbar;
Gate-Nachweis je Task in „Test/Nachweis". Globales Gate bleibt `make verify`.

---

## Befundbasis (für den BUILD verbindlich)

- **CLI-Framework:** `cpe_ta/cli.py` nutzt **click** (`@app.command(...)`, `click.group`), NICHT
  Typer. `dashboard`-Befehl daher als `@app.command("dashboard")` mit `click.option` umsetzen
  (Spec §14.1 nennt „Typer" nur illustrativ — bestehendes click-Muster gilt).
- **Daten-Quelle DB:** `cpe_ta/core/results.py` → `ResultsDB(db_path)` mit
  `get_runs() -> list[RunMetadata]`, `get_results_for_run(run_id) -> list[TestResult]`,
  `get_trend(domain, metric)`. `RunMetadata(run_id, firmware_version, dut_id, timestamp, git_sha)`,
  `TestResult` (Felder via `TestResult`-Dataclass). Data-Layer liest hierüber + via JUnit-Parse.
- **Domain-Ableitung:** JUnit-`classname`/Testpfad kodiert die Domäne (`tests/<domain>/...`).
  Data-Layer mappt Testname→Domäne über das `tests/<domain>/`-Segment bzw. `classname`-Präfix.
- **Dependency-Constraint:** Gate-Interpreter ist **brew `python3.11`** (3.11.15). Dort sind
  `fastapi`/`uvicorn`/`httpx` **NICHT installiert** (nur unter System-python3.9). T-D01 muss Deps
  zu `pyproject.toml`/`requirements.txt` ergänzen UND unter 3.11 installieren, sonst kollabiert die
  Dashboard-Suite im Gate.
- **Vorhandene Daten:** `test-results.xml` (JUnit, ~67 KB) existiert real im Projektroot →
  Grundlage für AC-25 (echte Zähler-Assertion).

---

## Gruppe DA — Fundament: Deps, Package-Skelett, Modelle

### T-D01 — Dashboard-Dependencies & Package-Skelett
- **Akzeptanzkriterium:** `fastapi`, `uvicorn`, `httpx` (für TestClient) in `pyproject.toml`
  (dependencies) + `requirements.txt`; unter dem Gate-Interpreter (brew python3.11) installiert
  und importierbar. Package `cpe_ta/dashboard/` mit `__init__.py`, leeren Modulen
  `app.py/data.py/runner.py/models.py` und `static/`-Ordner angelegt. (AC-23 Vorbedingung, §14.1)
- **Dateien:** `pyproject.toml`, `requirements.txt`, `cpe_ta/dashboard/__init__.py`,
  `cpe_ta/dashboard/{app,data,runner,models}.py` (Stub), `cpe_ta/dashboard/static/.gitkeep`.
- **Test/Nachweis:** `python3.11 -c "import fastapi, uvicorn, httpx, cpe_ta.dashboard"` exit 0;
  `pip install -e .` zieht Deps.

### T-D02 — Pydantic Response-Modelle (models.py)
- **Akzeptanzkriterium:** Pydantic-v2-Modelle für alle 6 Views: `OverviewModel` (counts
  passed/failed/skipped/error, last_run{time,duration,git_sha}, domains-Schnellzugriff),
  `DomainStat` (name, pass/fail/skip-Zähler, Quote), `RunSummary` (run_id, timestamp, duration,
  P/F/S, git_sha), `RunDetail` (Liste `TestEntry`: name, domain, status, duration, message?,
  stacktrace?, params?), `TestbedStatus` (dut, hal_devices, services, connection-status),
  `RunStartRequest{markers}`, `RunProgress{status,started,lines_tail,counts}`. Alle JSON-
  serialisierbar, `mypy --strict`-clean. (AC-24 Schema, AC-31)
- **Dateien:** `cpe_ta/dashboard/models.py`, `tests/dashboard/test_models.py`.
- **Test/Nachweis:** Modelle instanziieren + `.model_dump()` rund; `mypy --strict` clean.

---

## Gruppe DB — Daten-Layer (rein, unit-testbar)

### T-D03 — JUnit-XML-Parser + Domain-Aggregation (data.py)
- **Akzeptanzkriterium:** Reine Funktionen `parse_junit(path) -> RunDetail|TestEntry[]`,
  `overview(...)`, `domain_stats(...)`. Korrekte Zähler passed/failed/skipped/error; Domain-Mapping
  aus `classname`/Pfad. **Tolerantes Parsen:** defekte/teilweise XML überspringt kaputte Cases mit
  Warnung, **kein Crash** (AC-30). **Leerzustand:** fehlende XML → leere Strukturen, kein Throw
  (AC-26). (AC-25, AC-26, AC-30, §14.1 Backend↔Daten)
- **Dateien:** `cpe_ta/dashboard/data.py`, `tests/dashboard/test_data.py`,
  `tests/dashboard/fixtures/{broken.xml,empty-or-missing}`.
- **Test/Nachweis:** Assertion gegen erwartete Zähler aus realer `test-results.xml`; kaputte XML →
  tolerant; fehlende XML → leere Summen.

### T-D04 — DB-Lesezugriff + View-Aggregation (data.py)
- **Akzeptanzkriterium:** Data-Layer liest `ResultsDB` (`get_runs`, `get_results_for_run`,
  `get_trend`) und liefert `RunSummary[]`/`RunDetail`. Fehlende/leere DB → leere Listen, kein 500.
  Kombiniert JUnit (Sofort-Betrieb) + DB. Keine Secrets in Rückgaben. (AC-24, AC-26, §14.3-DB)
- **Dateien:** `cpe_ta/dashboard/data.py`, `tests/dashboard/test_data_db.py`.
- **Test/Nachweis:** In-memory `ResultsDB` mit 1–2 Runs → korrekte `RunSummary`; leere DB → `[]`.

---

## Gruppe DC — Run-Start (Subprocess, injizierbar)

### T-D05 — Run-Runner mit injizierbarer Command-Factory (runner.py)
- **Akzeptanzkriterium:** `DashboardRunner` startet `pytest -m "<markers>" --junitxml=<tmp>` als
  **Hintergrund-Subprocess** über eine **injizierbare Command-Factory** (Default = echte pytest-
  Argliste; Tests injizieren schnellen Fake-Command, der Mini-JUnit-XML schreibt). **`shell=False`,
  Argument-Liste** (keine Command-Injection). **Marker-Validierung** gegen Whitelist-Pattern
  (`^[a-zA-Z0-9_ ()and ortnt-]+$` analog Spec) → ungültig wirft, **kein Subprocess**. Nur **ein**
  aktiver Run; zweiter Start → Busy-Signal. Progress-Tracking (`status running→finished/failed`,
  `lines_tail`, `counts`). (AC-27, AC-28, §14.3)
- **Dateien:** `cpe_ta/dashboard/runner.py`, `tests/dashboard/test_runner.py`.
- **Test/Nachweis:** Fake-Command-Factory: `start()`→`running`→`finished`; Factory erhält **Liste**
  (kein Shell-String); ungültiger Marker → kein Subprocess; zweiter Start → Busy.

---

## Gruppe DD — FastAPI-App & Routen

### T-D06 — FastAPI-App-Factory + 6 JSON-Routen (app.py)
- **Akzeptanzkriterium:** `create_app(results_path, db_path, runner=None) -> FastAPI`
  instanziiert ohne laufenden Server (AC-23). Routen: `GET /api/overview`, `GET /api/domains`,
  `GET /api/runs`, `GET /api/runs/{run_id}`, `GET /api/testbed`, `POST /api/runs` +
  `GET /api/runs/active/progress` (Polling). Alle liefern bei vorhandener XML `200` + schema-
  konformes JSON (AC-24). **Leerzustand** → `200` leere Strukturen (AC-26). **Unbekannte run_id →
  404** klare Meldung (AC-30). Importiert nur `data.py`/`runner.py`, nie pytest-Interna. Static-
  Mount für Frontend. (AC-23, AC-24, AC-26, AC-27, AC-30, §14.2)
- **Dateien:** `cpe_ta/dashboard/app.py`, `tests/dashboard/test_routes.py`,
  `tests/dashboard/test_routes_empty.py`.
- **Test/Nachweis:** `TestClient`: alle 6 Routen `200`+Schema; leere XML/DB `200` ohne 500;
  unbekannte run_id `404`.

### T-D07 — Run-Start-Flow & Sicherheit über die API
- **Akzeptanzkriterium:** `POST /api/runs {markers}` mit Fake-Command-Factory startet, liefert
  sofort `run_id`/`status=running`; `/api/runs/active/progress` zeigt `running→finished`; danach
  erscheint Run in `GET /api/runs`. Zweiter paralleler Start → **409**. Ungültiger Marker → **4xx**
  (kein Subprocess). Default-Bind-Host `127.0.0.1` (in app/CLI-Default verankert, im Test geprüft).
  (AC-27, AC-28, §14.3)
- **Dateien:** `cpe_ta/dashboard/app.py`, `tests/dashboard/test_run_flow.py`.
- **Test/Nachweis:** Flow-Test `running→finished`+History; zweiter Start `409`; bad marker `4xx`;
  Default-Host-Assertion.

---

## Gruppe DE — CLI & Frontend

### T-D08 — CLI-Befehl `cpe-ta dashboard` (click)
- **Akzeptanzkriterium:** `@app.command("dashboard")` mit Optionen `--host` (Default `127.0.0.1`),
  `--port` (Default `8080`), `--results` (Default `test-results.xml`), `--db`. Startet uvicorn mit
  `create_app(...)`. `cpe-ta dashboard --help` zeigt Befehl + Optionen (AC-23). **Belegter Port →
  klare Fehlermeldung, Exit ≠ 0** (kein stiller Hang, §14.4). (AC-23, §14.1)
- **Dateien:** `cpe_ta/cli.py`, `tests/dashboard/test_cli_dashboard.py`.
- **Test/Nachweis:** `CliRunner`: `--help` listet `dashboard` + Default-Host `127.0.0.1`; Port-Belegt-
  Pfad → Exit ≠ 0 (uvicorn-Start gemockt/Fake).

### T-D09 — Vanilla-Frontend (6 Views, offline, kein CDN)
- **Akzeptanzkriterium:** `static/index.html` lädt **nur** lokale `app.css`/`app.js`; Hash-Routing-
  Navigation deckt alle 6 Views ab (`/`, `#/domains`, `#/runs`, `#/runs/{id}`, `#/testbed`,
  `#/start`); Daten via `fetch` von der JSON-API; Domain-Balken clientseitig per Canvas/SVG (keine
  Chart-Lib). **Keine externen `http(s)://`-Referenzen** (kein CDN/Font/JS). (AC-29, §14.1 Frontend)
- **Dateien:** `cpe_ta/dashboard/static/{index.html,app.css,app.js}`.
- **Test/Nachweis:** Offline-Meta-Test (siehe T-D10): grep `static/**` → keine externen URLs;
  `index.html` referenziert nur `app.css`/`app.js`.

---

## Gruppe DF — Qualität, Offline-Gate, Doku

### T-D10 — Offline-/Sicherheits-Meta-Test + Backend-Coverage
- **Akzeptanzkriterium:** Meta-Test grep't `cpe_ta/dashboard/static/**` auf externe `http://`/
  `https://`-Hosts → **keiner** (AC-29). Backend-Coverage `cpe_ta/dashboard` (ohne `static/`)
  ≥ **80 %**, gemessen/geloggt (AC-31). (AC-29, AC-31)
- **Dateien:** `tests/dashboard/test_offline.py`, `pyproject.toml` (cov-Include/omit static).
- **Test/Nachweis:** Offline-Test grün; Coverage-Report dashboard ≥80 %.

### T-D11 — Lint/Typen-Gate für Dashboard
- **Akzeptanzkriterium:** `ruff check cpe_ta/dashboard tests/dashboard` clean;
  `mypy --strict cpe_ta/dashboard/data.py cpe_ta/dashboard/models.py` clean. (AC-31)
- **Dateien:** querschnittlich (Cleanup), ggf. `pyproject.toml`/`Makefile` (mypy-Pfade ergänzen).
- **Test/Nachweis:** beide Kommandos exit 0; in `make verify` integriert.

### T-D12 — Gate-Integration + Doku-Update
- **Akzeptanzkriterium:** `make verify` nimmt `tests/dashboard/` über `-m "not hardware"`
  automatisch mit (Dashboard-Tests sind `@headless`); `make verify` exit 0 mit Dashboard-Suite.
  `.gitlab-ci.yml`/`Jenkinsfile` bleiben synchron (mypy-Dashboard-Pfade falls dort aufgeführt).
  README + `docs/architecture.md` um Dashboard-Abschnitt ergänzt (Start, Views, Offline). (§11 Gate,
  AC-31, §10 Doku)
- **Dateien:** `Makefile`, `.gitlab-ci.yml`, `Jenkinsfile`, `README.md`, `docs/architecture.md`.
- **Test/Nachweis:** `make verify` exit 0, Output zeigt ausgeführte `tests/dashboard/`-Tests;
  `pytest -m hardware` weiterhin nur skipped (AC-22 ungebrochen).

---

## Done-Gate-Mapping (Kontrolle §14.5)

AC-23→T-D06/T-D08 · AC-24→T-D02/T-D06 · AC-25→T-D03 · AC-26→T-D03/T-D04/T-D06 ·
AC-27→T-D05/T-D07 · AC-28→T-D05/T-D07 · AC-29→T-D09/T-D10 · AC-30→T-D03/T-D06 ·
AC-31→T-D10/T-D11. Gate-Integration→T-D12.

Alle 9 Dashboard-AC (AC-23..AC-31) abgedeckt. Bestehender Kern (AC-01..AC-22) bleibt unberührt;
`pytest -m hardware` muss nach Integration weiterhin ausschließlich `skipped` liefern.
Build-Phase startet mit T-D01 (Deps-Constraint zuerst auflösen).
