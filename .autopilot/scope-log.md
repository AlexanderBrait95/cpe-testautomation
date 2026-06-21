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
