# Requirement

# Requirements-Spezifikation: CPE Hardware- & Software-Acceptance-Test-Automation

**Version:** 1.0
**Ansatz:** In-house Framework (auf Open-Source-Bausteinen)
**Scope Zugangstechnologien:** DSL, DOCSIS, PON, FWA/Mobile-Cube (IP-Ebene)
**Out of Scope:** RAN-/Funk-Layer-Tests bei FWA/Mobile-Cube (nur IP-/Service-Ebene)

> Legende: `[OSS]` = empfohlener Open-Source-Baustein · `P1/P2/P3` = Umsetzungsphase

---

## 0. Strategie & Abgrenzung

Das Framework wird in-house entwickelt. „In-house" bezieht sich auf die **Orchestrierungs-, Testfall- und Reporting-Logik sowie die Hardware- und DUT-Abstraktion** – nicht auf die Basisinfrastruktur. Bewährte Open-Source-Bausteine werden integriert statt nachgebaut, um den Aufwand auf das Schreiben von Tests statt auf den Bau von Infrastruktur zu konzentrieren:

| Funktion | Empfohlener OSS-Baustein |
|---|---|
| Test-Runner / Orchestrierung | `pytest` oder `Robot Framework` |
| Referenz-ACS (CWMP/USP) | `GenieACS` |
| Traffic / Durchsatz | `iperf3`, `flent`, `Ostinato` |
| Paket-Crafting / Protokoll | `Scapy` |
| RADIUS (WiFi Enterprise, 802.1X) | `FreeRADIUS` |
| DHCP/DNS-Referenzdienste | `Kea`/`ISC-DHCP`, `dnsmasq`, `BIND` |
| VoIP-Gegenstelle / IMS-Sim | `Kamailio` / `Asterisk` |
| Security-Scan | `OpenVAS`/`Nessus` |
| WiFi-Client-Steuerung | `wpa_supplicant` + `iw` / `hostapd` |

---

## 1. Testbett-Topologie & Hardware-Schnittstellen

Das Framework läuft auf einem zentralen Test-/Control-Host. Die zu testenden CPEs (DUTs) werden in der Praxis über **Managed Switches** physisch mit dem Host und mit den Traffic-/Referenz-Endpunkten verbunden. Die Software muss daher nicht nur mit dem DUT, sondern aktiv mit der **physischen Testbett-Hardware** interagieren. Diese Hardware-Schnittstellen-Ebene ist zentraler Bestandteil des Frameworks, kein Zubehör.

### 1.1 Verkabelungs- & Topologie-Modell `P1`
- **REQ-HW-01:** Das Framework führt ein maschinenlesbares **Testbett-Inventar** (Wiring-Map): Welcher DUT-Port hängt an welchem Switch-Port, welche Traffic-Endpunkte und Referenzdienste an welchen Ports. Tests adressieren logische Rollen (z. B. „DUT-LAN-1"), nicht physische Ports.
- **REQ-HW-02:** Mehrere DUTs teilen sich die physische Switch-Fabric und werden über **VLANs logisch isoliert**, sodass parallele Tests sich nicht beeinflussen.
- **REQ-HW-03:** Die Hardware-Schnittstellen-Steuerung ist über einen Treiber-/Adapter-Layer abstrahiert, sodass ein Wechsel des Switch-/PDU-Herstellers die Testfälle nicht bricht.

### 1.2 Managed Switch als aktives Testinstrument `P1`
Der Switch ist nicht nur Verbindungsmedium, sondern wird programmatisch als Testinstrument angesteuert. Die Software muss folgende Switch-Funktionen über eine Steuerschnittstelle (`SNMP` / `NETCONF/YANG` / `REST` / Vendor-CLI) bedienen:
- **REQ-HW-04:** **Port enable/disable** zur Simulation von Kabel-Stecken/-Ziehen (Grundlage für Link-Flap-, Recovery- und Failover-Tests).
- **REQ-HW-05:** **Erzwingen von Speed/Duplex** pro Port (10/100/1000/…, Half/Full) als Gegenstelle für die LAN-Autonegotiation-Tests.
- **REQ-HW-06:** **Dynamische VLAN-Zuweisung** pro Port (DUT-Isolation sowie Bereitstellung abweichender Subnetze für Switching-Tests).
- **REQ-HW-07:** **Auslesen der Port-Statistiken/Counter** (Frames, Errors, Speed/Duplex-Status) als Messquelle und Plausibilisierung.
- **REQ-HW-08:** **Port-Mirroring / SPAN** zur Aktivierung von Packet-Capture auf definierten Verbindungen.

### 1.3 Weitere Hardware-Steuerschnittstellen `P1`
- **REQ-HW-09:** **Programmierbare PDU** (Power on/off des DUT, schaltbare Steckdosen).
- **REQ-HW-10:** **Serieller Konsolen-Server** (Serial-over-IP / Terminal-Server) für DUT-Konsolenzugriff zur Zustands-/Ressourcenüberwachung.
- **REQ-HW-11:** **Programmierbare RF-Dämpfungsglieder** und RF-Isolation (Schirmkammer/-box) für reproduzierbare WiFi-Messungen. Ohne RF-Kontrolle sind WiFi-Durchsatz-/Roaming-Ergebnisse nicht wiederholbar.
- **REQ-HW-12:** **USB-Schalt-/Relais-Hardware** für USB-Medien-Tests und ggf. physische Taster-Automation (Reset-/WPS-Button).

---

## 2. Architektur- & Querschnittsanforderungen

### 2.1 Test-Framework / Runner `P1`
- **REQ-ARCH-01:** Modularer Test-Runner mit Testfall-Selektion über Tags (Smoke / Full-Acceptance / Regression / pro Zugangstechnologie).
- **REQ-ARCH-02:** Idempotente Testfälle – jeder Test bringt DUT und Testbett in definierten Ausgangszustand (Setup/Teardown), keine Abhängigkeit von Vorläufen.
- **REQ-ARCH-03:** Parallelisierbarkeit auf Testbett-Ebene (mehrere DUTs gleichzeitig, VLAN-isoliert).

### 2.2 DUT-Abstraktionsschicht `P1`
- **REQ-DUT-01:** Einheitliche Geräte-Schnittstelle, die Vendor-/Modell-Unterschiede kapselt (Driver-/Adapter-Pattern pro CPE-Typ).
- **REQ-DUT-02:** Abstraktion über Datenmodell-Unterschiede **TR-098 (InternetGatewayDevice)** vs. **TR-181 (Device:2)**.
- **REQ-DUT-03:** Geräte-Inventar mit Capabilities (Ports, Bänder, max. Linkspeed, USB, VoIP-Ports, Zugangstechnologie), damit Tests capability-basiert skippen statt hart zu failen.

### 2.3 DUT-Control-Plane `P1`
- **REQ-CTRL-01:** Programmatischer **Factory Reset** vor/zwischen Testblöcken.
- **REQ-CTRL-02:** Power-Steuerung des DUT über die PDU (REQ-HW-09).
- **REQ-CTRL-03:** Konsolenzugriff (REQ-HW-10) zur Überwachung von CPU/RAM/Crash-Logs.
- **REQ-CTRL-04:** Konfig-Backup/-Restore zur schnellen Zustandsherstellung.
- **REQ-CTRL-05:** Firmware-Flash inkl. Up-/Downgrade und Rollback (A/B-Partition).

### 2.4 Referenz-Infrastruktur `P1`
- **REQ-INF-01:** Bereitstellung & Steuerung von Referenzdiensten am Testbett: ACS, RADIUS, DHCP/DNS, SIP/IMS-Simulator, NTP, TFTP/HTTP-Fileserver, Traffic-Endpunkte.

### 2.5 Ergebnis-, Report- & Regressions-Management `P1`
- **REQ-RPT-01:** Strukturierte Reports (JUnit-XML für CI + HTML/PDF für Menschen).
- **REQ-RPT-02:** Zentrale, versionierte Ergebnis-Datenbank für Trend-/Verlaufsanalyse über Firmware-Stände.
- **REQ-RPT-03:** Automatische Diagramm-Generierung (Durchsatz-/Latenzverläufe) als Querschnitts-Service.
- **REQ-RPT-04:** CI/CD-Anbindung (z. B. GitLab CI/Jenkins) inkl. Nightly-Regression-Run.

### 2.6 Pass/Fail-Kriterien & Methodik `P1`
- **REQ-CRIT-01:** Jeder Performance-Test definiert explizit: Toleranz, Messdauer, Transport (TCP/UDP), Tool, Wiederholungen, Aggregat (Median/Min).
- **REQ-CRIT-02:** Referenz-Methodik dokumentiert: **RFC 2544** (L2/L3-Durchsatz), **RFC 6349** (TCP-Goodput).
- **REQ-CRIT-03:** Schwellwerte wie „min. X % der Linerate" werden je Interface/Standard konkret hinterlegt.

### 2.7 Dual-Stack / IPv6 `P1`
- **REQ-IPV6-01:** Alle Connectivity-/DHCP-/Firewall-/Durchsatztests laufen in IPv4, IPv6 und Dual-Stack.
- **REQ-IPV6-02:** Tests für DHCPv6, SLAAC, Prefix Delegation, IPv6-Firewall sowie Transition-Mechanismen (DS-Lite / MAP-T) je nach Provider-Profil.

---

## 3. Hardware- / LAN-Tests

### 3.1 LAN-Autonegotiation `P1`
- 10 Mbit Half/Full, 100 Mbit Half/Full, 1 Gbit Full, bis 10 Gbit Full (capability-basiert).
- Programmatische Link-Speed-Konfiguration pro Interface; Gegenstelle über erzwungenes Speed/Duplex am Switch (REQ-HW-05).
- Link-Flap/Recovery (über Port enable/disable, REQ-HW-04), MTU/Jumbo-Frames, VLAN-Tagging (802.1Q), Cable-Diagnostics.

### 3.2 Switching `P1`
- Switching zwischen Subnetzen abweichend vom DHCP-Subnetz des CPE (Subnetz-Bereitstellung via VLANs, REQ-HW-06).
- Broadcast-/Multicast-Weiterleitung, MAC-Learning-Verhalten.

---

## 4. WiFi-Tests `P1`

### 4.1 Security-Modi
OPEN, WEP64/128 (prüfen, ob Abnahme noch nötig oder nur „wird korrekt abgelehnt"), WPA(TKIP/AES), WPA2(TKIP/AES), WPA+WPA2, WPA3 (SAE/AES), WPA2+WPA3, WiFi 6e, WiFi 7 MLO, OWE (Enhanced Open).

### 4.2 Szenarien
- Jeder Security-Modus, je Same-SSID (Band Steering) und Separate-SSID (2.4/5 GHz).
- Hidden/Visible SSID, Guest-Network.
- Downgrade des WiFi-Standards auf Test-Clients.

### 4.3 Erweiterte WiFi-Funktionen `P2`
- Roaming: 802.11k/v/r.
- EasyMesh / Mesh-Backhaul.
- DFS-Kanalverhalten (Radar-Detection), Kanal-/Bandbreitenwechsel.
- Max. Client-Anzahl & gleichzeitige Multi-Client-Last.

---

## 5. QoS / Performance `P1`

### 5.1 Basis Up-/Download
- Automatisierte Durchsatztests, LAN und WiFi, nach Methodik aus REQ-CRIT.

### 5.2 Parallel-Tests
- Parallel über alle LAN-Interfaces und WiFi-Interfaces (Default-Config).

### 5.3 Mixed-Traffic
- Download @T=0, Upload @T=1/3, Multicast @T=2/3; Verlaufsdiagramme (via REQ-RPT-03).
- Kombinationen: LAN-only · WiFi up/down + Multicast LAN · LAN up/down + WiFi Multicast.

### 5.4 Latenz-/Qualitätsmetriken `P2`
- Latenz, Jitter, Packet-Loss (nicht nur Durchsatz).
- DSCP/WMM-Priorisierung verifizieren; Bufferbloat (flent/RRUL).

---

## 6. Stress- / Stabilitätstests `P2`
- Kombinationen: WiFi-only · WiFi+LAN · +Voice · +Multicast · +Multicast+Voice; 2.4/5/6 GHz up/down.
- **REQ-STR-01:** Abbruchkriterien definiert (kein Reboot, kein Memory-Leak, CPU/RAM via Konsole überwacht).
- **REQ-STR-02:** Soak-Test über Stunden/Tage als eigene Kategorie (≠ Kurz-Stress).
- Mischlast statt nur FTP-Download (Profile aus 5.3 wiederverwenden).

---

## 7. WAN-Provisioning & Connectivity `P1`
- **REQ-WAN-01:** WAN-Aufbau über PPPoE, IPoE/DHCP — IPv4 & IPv6.
- **REQ-WAN-02:** NAT, Port-Forwarding/-Triggering, UPnP-IGD/PCP.
- **REQ-WAN-03:** Firewall-Tests (IPv4 und IPv6), Default-Deny inbound IPv6.
- **REQ-WAN-04:** DNS-Auflösung, NTP-Sync, MTU/PMTUD.
- **REQ-WAN-05:** Routing-Grundfunktionen (statische Routen, Multicast-Routing/IGMP-Proxy).

---

## 8. Spezialfunktionen

### 8.1 DHCP-Subnetze `P1`
- Default-Subnetze 10.0.0.x · 192.168.0.x · 192.168.1.x; dynamische & statische Zuweisung über LAN/WiFi.

### 8.2 Multicast `P1`
- Korrektes Join/Leave (IGMPv2/v3, MLDv1/v2 für IPv6), bis 5 parallele Streams.
- Channel-Zap-Time-Messung (IPTV-relevant).

### 8.3 DHCP-Pool-Stress `P2`
- > 90 % der Leases anfordern, danach Release, Lease-Allokationszeit messen, Fail bei Unterschreiten der definierten Mindestkapazität (REQ-CRIT-03).

### 8.4 USB-Medien `P2`
- Filesystem-Support (Liste zu liefern), Samba-Playback, DLNA-Streaming.

### 8.5 VoIP `P2`
- MTC/MOC-Call, Call Waiting, Conference.
- Codec-Matrix (G.711/G.722/G.729), T.38-Fax, Notruf, Registrierung/Re-Registrierung, MWI, DTMF.

### 8.6 USB-C Power Delivery `P3` (zukünftig)

### 8.7 LED on/off & Dimming `P2`

### 8.8 DHCP-Options `P1`
- Option 60, 43, 121, 15, 42, 125 (Vendor-Identifying) je nach Provisioning-Profil.

---

## 9. Security / RED-Konformität `P1`

> Seit 01.08.2025 sind die RED-Cybersecurity-Anforderungen (Art. 3.3 d/e/f, Delegierte VO (EU) 2022/30) verpflichtend. Relevanter harmonisierter Standard: **EN 18031-1/-2/-3:2024**. Ein reiner Vuln-Scan deckt dies nicht ab.

- **REQ-SEC-01:** Automatisierter Vuln-/Hardening-Scan `[OSS: OpenVAS/Nessus]` — offene Ports, schwache TLS-Versionen, Default-Credentials, bekannte CVEs.
- **REQ-SEC-02:** EN-18031-Checklisten-Mapping (teils manuell/teilautomatisiert): sichere Update-Mechanismen, Authentifizierung, Schutz personenbezogener Daten, Schutz der Netzfunktion.
- **REQ-SEC-03:** CWMP/USP über TLS, Zertifikatsvalidierung (siehe §10).

---

## 10. ACS-Tests (CWMP / TR-069) `P1`

> Referenz-ACS als Treiber: `[OSS: GenieACS]`. Die folgenden RPC-/Szenario-Tests werden gegen diesen Referenz-ACS automatisiert.

- Bootstrap/Session-Initiation, Periodic-Inform-Change, GetRPCMethods.
- Firmware-Download; GetParameterNames (complete/partial), Get Entire Object Model.
- GetParameterValues (complete/partial); SetParameterValues (bool/string).
- AddObject, DeleteObject, Reboot.
- IPPing-/TraceRoute-/Download-/Upload-/WLAN-Diagnostics.
- Session-Retry-Wait-Prolongation, HTTP-User-Agent-Verifikation, Zertifikatsvalidierung.
- APN-Wechsel auf `Fixip.a1.net`; Wechsel Bridge / IP-Passthrough.
- Get/SetParameterAttributes, Active Notifications, ScheduleInform, Connection-Request via XMPP/STUN (NAT-Traversal).

### 10.1 USP / TR-369 `P3`
- Roadmap-Strang: USP-Agent-Tests (Get/Set/Add/Delete/Operate, Notify) für CPEs mit USP-Support.

---

## 11. Zugangstechnologie-spezifische Tests `P2`

### 11.1 DSL
- Sync-Aufbau, Profile (17a/35b), G.vector, Retrain-Verhalten, SNR-Margin/Bitloading-Auslesung, Stabilität bei Leitungsstörung.

### 11.2 DOCSIS
- DS/US-Channel-Lock, Channel-Bonding, OFDM/OFDMA (DOCSIS 3.1), Config-File-Provisioning, Ranging.

### 11.3 PON
- ONU/ONT-Registrierung (GPON/XGS-PON), optische Pegel (RX/TX), Dying-Gasp, Service-Profile.

### 11.4 FWA / Mobile-Cube (nur IP-/Service-Ebene)
- **In Scope:** APN-Konfiguration/-Wechsel, Bridge/IP-Passthrough, Failover-Verhalten, IP-Connectivity & Durchsatz an der LAN-/WiFi-Seite.
- **Out of Scope:** RAN-/Funk-Layer-Tests (kein Modem-/Radio-Conformance).

---

## 12. Umsetzungs-Phasen

| Phase | Inhalt |
|---|---|
| **P1** | Testbett-/Hardware-Schnittstellen (§1), Architektur (§2), DUT-Abstraktion & Control-Plane, Reporting, IPv6-Basis, LAN, WiFi-Basis, QoS-Basis, WAN-Connectivity, DHCP/Subnetze/Options, Security-Scan, ACS/CWMP |
| **P2** | Erweiterte WiFi (Roaming/Mesh/DFS), Latenzmetriken, Stress/Soak, DHCP-Pool, USB, VoIP, LED, zugangsspezifische Tests, EN-18031-Mapping |
| **P3** | USP/TR-369, USB-C PD, weitergehende Performance-Profile |

---

## 13. Inputs / zu klärende Parameter
- Konkrete Filesystem-Liste (§8.4) und Mindestkapazitäten (§8.3).
- Provider-Provisioning-Profile je Zugangstechnologie (DHCP-Options-Sets, WAN-Modus).
- Linerate-Schwellwerte pro Interface/Standard (REQ-CRIT-03).
- Vendor-/Modell-Liste der abzunehmenden CPEs (für DUT-Driver-Priorisierung).
- Auswahl & Steuerschnittstelle der Managed Switches / PDUs / Dämpfungsglieder (für Hardware-Treiber, §1).

_Angelegt: 2026-06-20T23:05:43.459Z_

---

## 14. Web-Dashboard (P1 — neue Anforderung)

Das Framework bekommt ein **Web-Dashboard** als eigenständige Komponente (`cpe_ta/dashboard/`).
Ziel: Testergebnisse übersichtlich im Browser darstellen und Tests direkt aus dem Browser starten.

### 14.1 Stack & Betrieb
- **Backend:** FastAPI (Python), passt zur bestehenden `cpe_ta`-Codebasis.
- **Frontend:** Vanilla HTML/CSS/JavaScript — kein Build-System, keine Node-Deps.
- **Start:** `cpe-ta dashboard` startet den Server (CLI-Befehl analog zu bestehenden Commands).
- **Port:** 8080 (konfigurierbar).
- **Deployment:** Läuft lokal auf dem Control-Host, kein Internet-Zugriff nötig.

### 14.2 Seiten / Views

#### Overview (Startseite)
- Gesamtstatistik: Anzahl Passed / Failed / Skipped / Error (aus letztem Run oder kumulativ).
- Letzter Testlauf: Zeitstempel, Dauer, Git-Commit.
- Schnellzugriff auf die wichtigsten Domains.

#### Test-Domains
- Balkendiagramm: pro Domain (LAN, WiFi, WAN, DHCP, Security, ACS, VoIP, Stress, etc.) Pass/Fail-Quote.
- Klick auf Domain → gefilterte Testliste.

#### Testläufe (Run History)
- Tabelle aller Runs mit: Zeitstempel, Dauer, Passed/Failed/Skipped-Zähler, Git-Commit-Hash.
- Klick auf Run → Detail-Ansicht des Runs.

#### Testlauf-Detail
- Liste aller Tests des Runs mit Status-Icon (✓/✗/○), Testname, Domain, Dauer.
- Klick auf Test → Einzeltest-Detail.

#### Einzeltest-Detail
- Testname, Domain, Status, Dauer.
- Fehler-Message und Stacktrace (falls failed).
- Parametrisierungs-Info falls vorhanden.

#### Testbed-Status
- Zeigt das geladene Inventory (aus `testbed.yaml`): DUT-Name, HAL-Devices, konfigurierte Services.
- Verbindungsstatus (simuliert/real) pro Device.

#### Test-Run starten
- Formular: Test-Selektion via Marker-Tags (z. B. `headless`, `smoke`, Domain-Filter).
- „Run"-Button startet `pytest` als Subprocess im Hintergrund.
- Live-Fortschrittsanzeige (SSE oder Polling) während der Run läuft.
- Ergebnis wird nach Abschluss direkt in der History sichtbar.

### 14.3 Datenbasis
- Liest vorhandene `test-results.xml` (JUnit-Format) und die SQLite Results-DB (falls vorhanden).
- Parsed JUnit-XML für sofortige Kompatibilität ohne DB-Migration.
- Neue Runs werden automatisch in der DB gespeichert.

### 14.4 Akzeptanzkriterien
- `cpe-ta dashboard` startet ohne Fehler, Browser öffnet localhost:8080.
- Alle 6 Views sind erreichbar und zeigen sinnvollen Inhalt (ggf. „Keine Daten" wenn leer).
- Die vorhandene `test-results.xml` wird korrekt eingelesen und in der UI dargestellt.
- Ein Test-Run kann über die UI gestartet werden und der Status ist live sichtbar.
- Keine externen CDN-Abhängigkeiten (funktioniert offline).
- Tests für das Backend (FastAPI-Routes) im headless Gate (`make verify`).

_Erweitert: 2026-06-21 — Web-Dashboard Anforderung_
