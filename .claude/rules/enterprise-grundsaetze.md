# Enterprise-Grundsätze (VÖB Bankendienstleister)

1. **Keine Fehler, keine Halluzinationen.** Bei Unsicherheit: Tiefenanalyse, nicht raten. Lieber nachfragen.
2. **Dokumentation vor Code.** Feature → Modulspezifikation → Freigabe → Code → Test → Abnahme.
3. **Nachvollziehbarkeit.** Architekturentscheidungen als ADR (docs/adr/). Änderungen im Changelog.
4. **Abnahmefähigkeit.** Alles durch VÖB abnehmbar. Protokolle pro Meilenstein (M1-M6).
5. **Regulatorik.** DSGVO, BAIT, BSI-Grundschutz. Sicherheits-/Betriebskonzept sind Pflicht.
6. **Stabilität vor Speed.** Saubere Architektur, Upstream-Sync-Fähigkeit, minimale Core-Änderungen.
7. **Extend, don't modify.** ext_-Prefix, nur 10 Core-Dateien, Feature Flags für alles.

## VERBOTEN
- ❌ Onyx-Dateien verändern (außer 10 Core-Dateien auf erlaubte Weise)
- ❌ Onyx-DB-Tabellen mit ALTER TABLE ändern
- ❌ Onyx-Komponenten/CSS/Tests direkt editieren
- ❌ Code ohne Modulspezifikation + Freigabe
- ❌ Feature ohne Feature Flag
- ❌ Commit/Push ohne Nikos Freigabe
- ❌ Direkt auf main committen (immer über feature/* Branch + PR)
- ❌ Neue Dateien in backend/onyx/ oder web/src/ (statt backend/ext/ bzw. web/src/ext/)
- ❌ EE-Code nutzen, kopieren oder portieren (`backend/ee/`, `web/src/ee/`) — keine Lizenz vorhanden
- ❌ `ENABLE_PAID_ENTERPRISE_EDITION_FEATURES` auf `true` setzen
