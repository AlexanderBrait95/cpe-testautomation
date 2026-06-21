# Scope-Log

Erweiterungen/Konkretisierungen über das wörtliche Requirement hinaus, mit Begründung.
Das Requirement ist die Untergrenze; alle Punkte hier schärfen Lieferbarkeit/Verifizierbarkeit.

## SPEC-Phase, Iteration 0 (2026-06-21)

- **HAL-Invariante als harte Architekturregel + Import-Linter-Meta-Test (AC-01).**
  Begründung: Requirement fordert Treiber-/Adapter-Layer (REQ-HW-03, REQ-DUT-01), sagt aber nicht,
  wie die Einhaltung erzwungen wird. Ohne maschinelle Prüfung erodiert die Abstraktion. Pflicht,
  damit der Autopilot headless überhaupt verifizierbar bauen kann.

- **Deterministische Simulatoren für JEDES Interface (HAL, DUT, Referenz-Infra) + Determinismus-
  Meta-Test (AC-03/AC-04).** Begründung: Requirement beschreibt physisches Labor; Autopilot hat
  keine Hardware. Simulatoren sind Voraussetzung für ein erreichbares Done-Gate. Direkt aus der
  Autopilot-HAL-Vorgabe abgeleitet.

- **Explizite Zweiteilung `@headless` (Gate-blockierend) vs. `@hardware` (deferred, nicht
  blockierend) inkl. Deferred-Matrix (AC-22, §4).** Begründung: Requirement unterscheidet das
  nicht; nötig, damit physisch unvermeidbare Tests den Autopilot-Done-Gate nicht blockieren, aber
  trotzdem dokumentiert sind.

- **Konkrete Stack-Festlegung (Python 3.11, pytest+xdist, pydantic, SQLite, matplotlib, ruff,
  mypy).** Begründung: Requirement nennt „pytest ODER Robot" und OSS-Optionen; für einen
  deterministischen Build ist eine eindeutige Wahl nötig. pytest gewählt (flexibler für In-house-
  Framework + capability-skip + xdist).

- **`make verify` als einziges, reproduzierbares Gate-Kommando (§11).** Begründung: Requirement
  definiert kein Done-Kommando; der Autopilot braucht eine messbare, idempotente Verifikation.

- **Coverage-Schwelle ≥80 % auf Framework-Kern (AC-18) + ruff/mypy-Gate (AC-17).** Begründung:
  Requirement fordert Tests, aber kein messbares Qualitätsziel; ohne Schwelle kein objektives Gate.

- **Default-Profile für offene §13-Inputs statt Blockade (§13).** Begründung: Requirement listet
  offene Klärpunkte; statt darauf zu warten, werden dokumentierte Defaults gesetzt und als
  „anzupassen" markiert, damit P1 lieferbar bleibt. Kein Feature-Aufblähen — nur Platzhalter.

- **Fehler-Klassifikation `error` ≠ `fail` + Fehlertaxonomie (`errors.py`, §7).** Begründung:
  Requirement fordert Stabilität/Recovery implizit (REQ-STR-01); saubere Trennung verhindert, dass
  Infrastruktur-/Timeout-Probleme als fachliche Fehlschläge fehlinterpretiert werden.

KEINE Erweiterung des fachlichen Test-Scopes über das Requirement hinaus — alle Domänen (§3–§11)
stammen aus dem Requirement. Ergänzt wurde ausschließlich, was Lieferbarkeit und maschinelle
Verifizierbarkeit headless sicherstellt.

## SPEC-Phase, Iteration 4 (2026-06-21) — §14 Web-Dashboard

Requirement um §14 erweitert (FastAPI + Vanilla-HTML-Dashboard). Konkretisierungen über den
wörtlichen §14-Text hinaus, jeweils zur headless-Verifizierbarkeit/Sicherheit:

- **JSON-API-Schnittstelle als Backbone (§14.2) + injizierbare Command-Factory für Run-Start
  (§14.3).** Begründung: §14 fordert Views + Run-Start, sagt aber nicht, wie der Done-Gate ohne
  Live-Server und ohne echten langen pytest-Lauf verifiziert wird. Saubere JSON-Routen + Fake-
  Command machen AC-24/AC-27 headless mit `TestClient` prüfbar — kein blinder Feature-Zusatz,
  nur Testbarkeit.

- **Loopback-Default-Bind + Marker-Whitelist + `shell=False`-Subprocess (§14.1, AC-28).**
  Begründung: §14 nennt keine Sicherheit; ein Endpoint, der pytest startet, ist ohne Input-
  Validierung command-injection-anfällig und bei `0.0.0.0`-Bind netzexponiert. Pflicht-Härtung.

- **Offline-Meta-Test gegen CDN-Referenzen (AC-29).** Begründung: §14.4 fordert „funktioniert
  offline / keine CDN-Abhängigkeiten" — ohne maschinellen Grep-Test ist das nicht objektiv
  prüfbar. Macht das Requirement-Kriterium messbar.

- **Explizite Edge-Case-Liste + Fehler-Status-Codes (404/409/422, Leerzustand→200) (§14.4,
  AC-26/AC-30).** Begründung: §14.4 nennt „ggf. Keine Daten", lässt Fehlerpfade aber offen;
  präzisiert zu messbaren HTTP-Kontrakten, damit die UI nie Tracebacks zeigt.

- **6 Views statt wörtlich 7 Überschriften: „Einzeltest-Detail" als Drill-down der Run-Detail-
  View.** Begründung: §14.4-AC sagt „Alle 6 Views erreichbar", §14.2 listet 7 Überschriften.
  Aufgelöst gemäß AC-Zahl — Einzeltest ist Detailfeld derselben Run-Detail-Route, keine eigene
  Top-Level-Navigation. Keine Funktionalität entfällt.

- **ruff/mypy-strict/Coverage-Schwelle auch für `cpe_ta/dashboard` (AC-31).** Begründung: §14.4
  fordert „Tests für das Backend im headless Gate", nennt aber kein Qualitätsziel; konsistent zum
  bestehenden Gate (AC-17/AC-18) auf das Dashboard ausgedehnt. Vanilla-JS bewusst ausgenommen
  (kein JS-Testharness im Scope).
