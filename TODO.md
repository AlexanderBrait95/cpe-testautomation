# TODO — cpe-testautomation

Offene Punkte für künftige Autopilot-Runs oder manuelle Umsetzung.

---

## PRIO 1 — Dashboard: Vollständige Bedienoberfläche

Das aktuelle Dashboard ist eine reine Ansicht ohne echte Steuerungsfunktionen.
Ziel: Das Dashboard soll die **einzige Oberfläche** sein, um das gesamte Test-Framework zu bedienen —
von der Testbett-Konfiguration über die Testausführung bis zum Report.

### Fehlende Funktionen

- **Testbett-Konfiguration im Browser**
  - Testbed YAML direkt im Dashboard anlegen / bearbeiten (kein manuelles Editieren von YAML-Dateien)
  - Hardware-Geräte hinzufügen: Switch, PDU, Serial-Console, RF-Dämpfer, DUT (CPE/Modem/Router)
  - Verbindungstest pro Gerät (Ping/SNMP/SSH/Telnet — je nach Treiber)
  - Wiring-Map: welcher DUT-Port hängt an welchem Switch-Port (grafisch oder tabellarisch)

- **DUT-Verwaltung**
  - DUT (Modem/Router/CPE) registrieren: Modell, Firmware-Stand, Zugangstechnologie (DSL/DOCSIS/PON/FWA)
  - Capabilities pflegen (LAN-Ports, WiFi-Bänder, USB, VoIP, etc.)
  - DUT-Status: online/offline, aktuelle IP, letzter bekannter Zustand

- **Testausführung — volle Kontrolle**
  - Test-Selektion: nach Domain, Tag, Einzeltest, ganzer Suite
  - Parallele Runs auf mehreren DUTs gleichzeitig (VLAN-isoliert)
  - Live-Output: gestreamter pytest-Log während der Run läuft (SSE/WebSocket)
  - Abbrechen eines laufenden Runs

- **Ergebnis-Auswertung**
  - Trendverläufe: Pass-Rate über Firmware-Stände / Zeit
  - Vergleich zweier Runs (Diff: welche Tests haben sich verändert?)
  - Durchsatz-/Latenz-Diagramme direkt im Dashboard (aus den Messdaten)
  - Filter & Suche in Testergebnissen

- **Report-Export**
  - HTML-Report download
  - PDF-Report download
  - JUnit-XML für CI-Systeme

---

## PRIO 2 — Onboarding & Bedienungsanleitung

Aktuell gibt es keine Erklärung für neue Nutzer, wie das System aufgebaut und bedient wird.
Das muss als integrierter Teil des Dashboards UND als Dokumentation existieren.

### Hardware-Setup-Guide (im Dashboard integriert)
Schritt-für-Schritt-Anleitung direkt im Browser:

1. **Was brauche ich für reale Tests?**
   - Control-Host (Linux/Mac, auf dem cpe-ta läuft)
   - Managed Switch (SNMP/NETCONF/REST-fähig) — welche Modelle werden unterstützt?
   - Programmierbare PDU (schaltbare Steckdosen für DUT-Power-Cycling)
   - Serieller Konsolen-Server (z. B. Digi, Lantronix, oder USB-Serial-Adapter)
   - RF-Dämpfungsglied + Schirmkammer/Schirmbox für reproduzierbare WiFi-Tests
   - USB-Relais für physische Taster-Automation (Reset/WPS)
   - Der DUT (Modem/Router/CPE) selbst

2. **Wie schließe ich alles an?**
   - Topologie-Diagramm: Control-Host ↔ Switch ↔ DUT ↔ Traffic-Endpunkte
   - Welcher Port des DUT kommt an welchen Switch-Port?
   - PDU-Steckdose dem DUT zuweisen
   - Serielle Konsole: USB-Serial oder Konsolen-Server verbinden
   - WiFi: DUT in Schirmkammer, RF-Dämpfer zwischen DUT-Antenne und Test-Client

3. **Welche Referenz-Infrastruktur brauche ich?**
   - GenieACS (ACS/TR-069) — Installation & Konfiguration
   - FreeRADIUS (WiFi Enterprise, 802.1X)
   - Kea DHCP / dnsmasq
   - iperf3-Server als Traffic-Endpunkt
   - Kamailio/Asterisk als SIP-Gegenstelle (VoIP-Tests)
   - OpenVAS für Security-Scans
   Für alle: Docker-Compose-Beispiel mitliefern (schneller Einstieg)

4. **Testbed konfigurieren**
   - `testbed.yaml` Schritt für Schritt befüllen (mit Wizard im Dashboard)
   - Validierung: `cpe-ta inventory-validate testbed.yaml`

5. **Ersten Test ausführen**
   - Headless (ohne Hardware): `cpe-ta run -m headless` — sofort ohne Hardware lauffähig
   - Mit Hardware: Smoke-Test starten, Ergebnis im Dashboard ansehen

### Dokumentation (docs/)
- `docs/hardware-setup.md` — vollständige Hardware-Verkabelungsanleitung
- `docs/infrastructure.md` — Referenz-Dienste aufsetzen (inkl. Docker-Compose)
- `docs/first-run.md` — vom leeren Rechner zum ersten grünen Test
- `docs/testbed-config.md` — testbed.yaml Referenz mit allen Feldern erklärt
- `docs/faq.md` — häufige Fehler und Lösungen

---

## PRIO 3 — Dashboard UX / Design

- Responsives Layout (auch auf größeren Monitoren im Testlabor nutzbar)
- Dunkles Theme (Standard in Testlabor-Umgebungen)
- Status-Anzeige: Ist gerade ein Test-Run aktiv? (persistenter Header-Indikator)
- Notification bei Run-Ende (Browser-Notification oder Telegram-Integration)
- Mehrsprachigkeit: DE/EN umschaltbar

---

## PRIO 4 — CI/CD Integration

- GitHub Actions Workflow (`.github/workflows/ci.yml`) ergänzen
- Nightly-Run automatisch per Cron starten
- Dashboard-Link im PR-Comment nach CI-Run

---

_Zuletzt aktualisiert: 2026-06-21_
