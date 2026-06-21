# Deferred Hardware Test Matrix

Tests marked `@hardware` require physical hardware and are SKIPPED without it.
Run with: `pytest -m hardware` → all tests skipped (not failed).

## Access Technology Tests (tests/tech/)
| Test | Hardware Required |
|------|-------------------|
| test_dsl_sync | ADSL2+/VDSL2 modem, DSLAM |
| test_docsis_channel_lock | DOCSIS 3.1 CMTS, downstream |
| test_pon_registration | GPON/XGS-PON OLT, fiber |
| test_fwa_apn_config | LTE/5G modem, SIM card |

## WiFi RF Tests (tests/wifi/)
| Test | Hardware Required |
|------|-------------------|
| test_rf_throughput_2_4 | RF shielded chamber, WiFi client |
| test_rf_roaming_11r | Multiple APs, 802.11r support |
| test_dfs_radar_detection | RF signal generator (radar) |

## Stress/Soak Long-Run Tests (tests/stress/)
| Test | Hardware Required |
|------|-------------------|
| test_soak_24h | Physical DUT, 24h test window |
| test_soak_wifi_lan_voice | RF chamber + VoIP hardware |

## VoIP Tests (tests/voip/ — P2, stub)
| Test | Hardware Required |
|------|-------------------|
| test_voip_mtc | SIP phone, IMS infrastructure |
| test_voip_t38 | Fax machine, T.38 gateway |

## USB Media Tests (tests/usb/ — P2, stub)
| Test | Hardware Required |
|------|-------------------|
| test_usb_samba | Physical USB drive |
| test_usb_dlna | Physical USB drive, DLNA client |

## Firmware Flash (real DUT) — geplant (P2)
> Tests noch nicht implementiert; Scope in P2 nach Vendor-Auswahl (Spec §13).

| Test (geplant) | Hardware Required |
|----------------|-------------------|
| test_fw_flash_real | Physical CPE DUT, firmware binary |
| test_fw_rollback_real | Physical CPE DUT, dual-bank support |

## Optical Level Tests (PON — tests/tech/)
| Test | Hardware Required |
|------|-------------------|
| test_pon_rx_power | Optical power meter, GPON OLT |
| test_pon_dying_gasp | UPS power cutoff, OLT logging |
