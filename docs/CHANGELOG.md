# Changelog

Alle wichtigen Änderungen am VÖB Service Chatbot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- [Infra] **Phase 2: StackIT DEV-Infrastruktur (in Arbeit)**
  - StackIT CLI Setup + Service Account `voeb-terraform` mit API Key
  - Container Registry im Portal aktiviert
  - Terraform `init` + `plan` erfolgreich (SKE Cluster, PostgreSQL Flex, Object Storage)
  - Terraform-Code Fix: `default_region` für Provider v0.80+
  - Runbook-Struktur `docs/runbooks/` mit Index + erstem Runbook (Projekt-Setup)
  - Implementierungsplan aktualisiert mit verifizierten Befehlen
  - Blockiert: SA benötigt `project.admin`-Rolle (wartet auf Org-Admin)
- [Feature] **Phase 4a: Extension Framework Basis**
  - `backend/ext/` Paketstruktur mit `__init__.py`, `config.py`, `routers/`
  - Feature Flag System: `EXT_ENABLED` Master-Switch + 6 Modul-Flags (AND-gated, alle default `false`)
  - Health Endpoint `GET /api/ext/health` (authentifiziert, zeigt Status aller Module)
  - Router-Registration Hook in `backend/onyx/main.py` (einzige Core-Datei-Änderung)
  - Docker-Deployment: `docker-compose.voeb.yml` (Dev) + `Dockerfile.voeb` (Production)
  - Modulspezifikation `docs/technisches-feinkonzept/ext-framework.md`
  - 10 Unit-Tests (5× Config Flags, 5× Health Endpoint) — alle bestanden
- [Feature] Dokumentation Repository initial setup
  - README mit Dokumentationsstruktur
  - Technisches Feinkonzept Template
  - Sicherheitskonzept (Entwurf)
  - Testkonzept mit Testfallkatalog
  - Architecture Decision Records (ADR-001 bis ADR-003)
  - Betriebskonzept (Entwurf)
  - Abnahme-Protokoll und Meilensteinplan
  - Changelog

### Changed
- [Documentation] Alle Dokumente in Deutsch verfasst (Banking-Standard)

### Fixed
- [Bugfix] Core-Datei-Pfade in `.claude/rules/` und `.claude/hooks/` korrigiert (4 von 7 Pfade waren falsch)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

---

## [1.0.0] – Documentation Release

### Added
- [Documentation] Initial dokumentation package für Banking-Sektor
  - Umfassendes Technisches Feinkonzept mit Modulspezifikation-Template
  - Sicherheitskonzept mit DSGVO, BAIT, und Banking-Anforderungen
  - Testkonzept mit Testpyramide und 11 Beispiel-Testfälle
  - 3 Architecture Decision Records (Onyx FOSS, Extension Architektur, StackIT)
  - Betriebskonzept mit Deployment, Monitoring, Backup-Strategie
  - Abnahme-Protokoll-Template und Meilensteinplan (M1-M6)
  - Changelog für Versionsverfolgung

### Status
- **Dokumentation**: 100% initial draft
- **Ready for**: Review-Prozess mit Stakeholdern
- **Next Step**: Finalisierung nach Feedback

---

## Versionierungsschema

Dieses Projekt folgt [Semantic Versioning](https://semver.org/):

- **MAJOR**: Bedeutende Änderungen, Breaking Changes
- **MINOR**: Neue Features, rückwärts-kompatibel
- **PATCH**: Bug Fixes, rückwärts-kompatibel

Beispiel: `1.2.3`
- `1` = MAJOR (Breaking changes seit v0)
- `2` = MINOR (2 neue Features seit v1.0)
- `3` = PATCH (3 Bugfixes seit v1.2)

---

## Dokumentations-Releases (geplant)

### Phase 1 – Dokumentation
- [x] Initial Documentation Setup
- [ ] Stakeholder Feedback Collection
- [ ] Dokumentation finalisieren nach Feedback

### Phase 2 – Infrastruktur (M1)
- [ ] Infrastruktur Go-Live
- [ ] Abnahmeprotokoll unterzeichnet
- [ ] Release Notes v1.0.0-infra

### Phase 3 – Authentifizierung (M2)
- [ ] Auth Module Release Notes
- [ ] Updated Dokumentation nach Implementation

### Phase 4 – Extensions (M3-M4)
- [ ] Token Limits Release
- [ ] RBAC Release
- [ ] Advanced Features Release

### Phase 5 – Go-Live Readiness (M5)
- [ ] Final Testing Release Notes
- [ ] Production Runbooks

### Phase 6 – Production (M6)
- [ ] Production Release v1.0.0
- [ ] Go-Live Announcement

---

## Dokumentations-Versionen

### v0.1 – Initial Draft
- Alle Basis-Dokumente erstellt
- Status: Entwurf
- Zielgruppe: Interne Review

### v0.5 – Stakeholder Review (geplant)
- Feedback von VÖB, CCJ, JNnovate eingearbeitet
- Status: In Überarbeitung

### v1.0 – Final Release (geplant)
- Alle Dokumente finalisiert und freigegeben
- Status: Produktionsreif

---

## Bekannte Probleme und Einschränkungen

### [ENTWURF]-Marker

Viele Abschnitte sind mit `[ENTWURF]` oder `[TBD]` gekennzeichnet. Diese werden nach finaler Konfiguration der Infrastruktur ergänzt:

- Sicherheitskonzept: Infrastruktur-Details (Vaults, WAF, etc.)
- Betriebskonzept: StackIT-spezifische Konfiguration
- Testkonzept: Testumgebungen nach Setup

### Dependencies

Dokumentation hängt ab von:
- StackIT Account und Konfiguration
- Entra ID Setup durch VÖB
- LLM Provider Entscheidung (noch offen)

---

## Zugehörige Dateien und Verweise

### Dokumentations-Struktur
```
/sessions/epic-nice-ritchie/docs/
├── README.md                                    (Main Index)
├── 01-technisches-feinkonzept/
│   ├── README.md                              (Modulübersicht)
│   └── template-modulspezifikation.md         (Template)
├── 02-sicherheitskonzept/
│   └── sicherheitskonzept.md                  (Security Concept)
├── 03-testkonzept/
│   └── testkonzept.md                         (Test Strategy)
├── 04-adr/
│   ├── README.md                              (ADR Index)
│   ├── adr-001-onyx-foss-als-basis.md        (Platform Choice)
│   ├── adr-002-extension-architektur.md       (Extension Architecture)
│   └── adr-003-stackit-als-cloud-provider.md (Cloud Provider)
├── 05-betriebskonzept/
│   └── betriebskonzept.md                     (Operations Concept)
├── 06-abnahme/
│   ├── abnahmeprotokoll-template.md           (Acceptance Protocol)
│   └── meilensteinplan.md                     (Milestone Plan)
└── 07-changelog/
    └── CHANGELOG.md                           (This File)
```

---

## Mitwirkende

- **CCJ**: Projektleitung und Governance
- **JNnovate**: Technische Umsetzung und Architektur
- **StackIT**: Cloud-Infrastruktur
- **VÖB**: Anforderungen und Abnahme

---

## Lizenz

Diese Dokumentation ist Teil des VÖB Service Chatbot Projekts.

- **Lizenz für Dokumentation**: CC BY-SA 4.0 (Attribution-ShareAlike)
- **Lizenz für Code**: MIT (siehe Onyx FOSS Base)

---

## Kontakt und Support

Bei Fragen zur Dokumentation:

- **CCJ Projektleitung**: [E-Mail TBD]
- **JNnovate Technical Lead**: [E-Mail TBD]

---

## Versionshistorie dieser Datei

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|-----------|
| 0.1 | [TBD] | [Autor] | Initial Release |

---

**Letzte Aktualisierung**: [Datum TBD]
**Wartete durch**: [Name/Team TBD]
**Nächste Überprüfung**: [Datum TBD – 30 Tage]
