# Research — Dashboard-Nachschärfung (2026-06-22)

Anlass: User-Feedback v1.1 — Dashboard ist „nur eine Ansicht", soll die Testautomation
**komplett bedienen** und dem Nutzer **erklären**, wie real getestet wird (Hardware,
Infrastruktur, Bedienung). Recherche zur Schärfung der Akzeptanzkriterien.

## Befund 1 — Was Nutzer von einem Test-Dashboard erwarten
Quelle: testsigma.com/blog/dashboard-testing, uxpin.com Dashboard Design Principles 2026.
Kernfunktionen über reines Anzeigen hinaus: **Filtern/Sortieren**, **Drill-down** in einzelne
Datenpunkte, **Schlüsselaktionen direkt ausführbar** (Run starten, Report exportieren),
konsistente/intuitive Navigation. „Time-to-insight" und „Task success rate" sind die
Erfolgsmetriken — ein Dashboard, das eine Aktion nicht zu Ende führen lässt, gilt als unfertig.
→ Übernommen: Filter über Run-/Test-Listen, Export, Run-Abbruch, Re-Run direkt aus der UI.

## Befund 2 — In-App-Guidance statt externer Doku
Quelle: digiteum.com Dashboard UX Tips, excited.agency Dashboard UX.
Bewährt: **Tooltips, On-Hover-Hinweise, kontextuelle Hilfe, Onboarding-Flows** direkt im UI
statt PDF-Handbuch. Nutzer sollen ohne Vorwissen die nächste sinnvolle Aktion erkennen
(Discoverability). Leerzustände sollen erklären, was zu tun ist, statt nur „keine Daten".
→ Übernommen: eigene **Hilfe/Onboarding-View** + kontextuelle Hinweise + handlungsleitende
Leerzustände. Kein blinder Feature-Dump — Fokus auf „wie bediene ich das, wie schließe ich
Hardware an, was brauche ich für reale Tests".

## Befund 3 — CPE-Testlab: was ein Nutzer real anschließen/aufbauen muss
Quelle: TP-Link 5G CPE Setup Guides (tp-link.com/document/27416), promptlink.com „What is CPE".
Realer Aufbau ist konkret und erklärbar: DUT mit **Strom** (über schaltbare PDU für
Power-Cycle), **Ethernet (RJ-45 LAN/WAN)** zum Managed Switch, **serielle Konsole** für
CPU/RAM-Metriken, je nach Zugangstechnik DSL/DOCSIS/PON/FWA-Anschluss, plus Referenz-Infra
(ACS, RADIUS, DHCP/DNS, iperf-Endpunkt). Netzbetreiber haben je nach Technik unterschiedliche
CPE-Testanforderungen.
→ Übernommen: Die Hilfe-View muss pro HAL-Gerät + Referenzdienst erklären **was, wofür, wie
angeschlossen**, und den **sim↔real-Schalter** sichtbar machen. Diese Inhalte existieren bereits
strukturiert in `docs/testbed.md`/`deferred-matrix.md` und der `testbed.yaml` — die UI macht sie
nur bedienbar/sichtbar, kein neuer fachlicher Scope.

## Konsequenz für die Spec
Die Dashboard-Erweiterung ist eine **Bedien- + Onboarding-Schicht** auf die bereits vorhandene
Engine/Doku — nicht neue Testfachlichkeit. Neue AC zielen auf: (a) vollständige Bedienbarkeit
(Run-Steuerung, Filter, Export, Testbed-Bedienung), (b) eingebaute Anleitung (Hardware-/Infra-/
Bedien-Onboarding in der UI), (c) handover-reife UX (Navigation, Leerzustände, Fehlertexte,
Hilfe). Alles headless via TestClient + statische Asset-Checks verifizierbar.

Quellen:
- https://testsigma.com/blog/dashboard-testing/
- https://www.uxpin.com/studio/blog/dashboard-design-principles/
- https://www.digiteum.com/dashboard-ux-design-tips-best-practices/
- https://excited.agency/blog/dashboard-ux-design
- https://www.tp-link.com/sg/document/27416/
- https://www.promptlink.com/media-library/blog/what-is-cpe-and-why-does-it-matter.html
