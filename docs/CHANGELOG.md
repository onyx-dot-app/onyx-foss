# Changelog

Alle wichtigen Änderungen am VÖB Service Chatbot werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Security
- [Infra] **C6: DB_READONLY_PASSWORD in K8s Secret verschoben** (2026-03-05)
  - Passwort war im Klartext in K8s ConfigMap — jetzt über `auth.dbreadonly` als K8s Secret (identisch zu postgresql/redis/objectstorage)
  - CI/CD Workflow in allen 3 Deploy-Jobs angepasst
- [Infra] **H8: Security-Header auf nginx** (2026-03-05)
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` via `http-snippet` in values-common.yaml
- [CI/CD] **H11: image_tag Script Injection gefixt** (2026-03-05)
  - `${{ inputs.image_tag }}` → `env:` Variable (GitHub Security Lab Best Practice) + Docker-Tag-Regex-Validierung
- [Docs] **Cloud-Infrastruktur-Audit** (2026-03-04)
  - 5 Opus-Agenten: 10 CRITICAL, 18 HIGH, ~20 MEDIUM, ~12 LOW Findings
  - 5 Findings verifiziert durch separate Code-Analyse-Agenten
  - Audit-Dokument: `docs/audit/cloud-infrastruktur-audit-2026-03-04.md`
- [Infra] **SEC-01: PostgreSQL ACL eingeschränkt** (2026-03-03)
  - PG ACL von `0.0.0.0/0` auf Cluster-Egress-IP `188.34.93.194/32` + Admin-IP eingeschränkt
  - Default `pg_acl` in beiden Terraform-Modulen entfernt → erzwingt explizite Angabe pro Environment
  - Terraform Credentials-Handling: `credentials.json` Wrapper, `chmod 600`, `.envrc` in `.gitignore`
- [Security] **GitHub Actions SHA-Pinning** (2026-03-02)
  - Alle 6 Actions auf Commit-SHA fixiert statt Major-Version-Tags (Supply-Chain-Schutz)
  - `actions/checkout`, `docker/login-action`, `docker/setup-buildx-action`, `docker/build-push-action`, `azure/setup-helm`, `azure/setup-kubectl`
- [Security] **Least-Privilege Permissions** (2026-03-02)
  - `permissions: contents: read` — Workflow hat nur Lesezugriff auf Repo
- [Security] **Redis-Passwort aus Git entfernt** (2026-03-02)
  - War hardcoded in `values-dev.yaml` → jetzt über GitHub Secret `REDIS_PASSWORD`
- [Security] **Concurrency Control** (2026-03-02)
  - Max 1 Deploy pro Environment gleichzeitig, verhindert Race Conditions
- [Security] **Model Server Version gepinnt** (2026-03-02)
  - `v2.9.8` statt `:latest` — reproduzierbare Deployments

### Added
- [Infra] **TEST-Umgebung LIVE** (2026-03-03)
  - Node Pool auf 2 Nodes skaliert (DEV + TEST im shared Cluster)
  - PG Flex `vob-test` + Bucket `vob-test` provisioniert
  - Namespace `onyx-test`, GitHub Environment `test` + 5 Secrets
  - Helm Release `onyx-test`: 9 Pods Running, Health Check OK
  - Erreichbar unter `http://188.34.118.201`
  - Eigene IngressClass `nginx-test` (Conflict mit DEV vermieden)
  - Separate S3-Credentials für TEST erstellt (Enterprise-Trennung)
- [Infra] **TEST-Umgebung vorbereitet** (2026-03-02)
  - ADR-004: Umgebungstrennung DEV/TEST/PROD (Architekturentscheidung dokumentiert)
  - Terraform: Node Pool `devtest` auf 2 Nodes skaliert (1 pro Environment)
  - Terraform: Neues Modul `stackit-data` (PG + Bucket ohne Cluster) für TEST
  - Terraform: `environments/test/` mit eigener PG Flex Instanz + Bucket `vob-test`
  - Helm: `values-test.yaml` (analog DEV, eigene Credentials/Bucket)
  - CI/CD: Smoke Test für `deploy-test` Job ergänzt
  - Implementierungsplan: Phase 7 (TEST-Umgebung) mit 9 Schritten + Validierungstabelle
  - Infrastruktur-Referenz: Environments-Tabelle + Node Pool aktualisiert
- [Infra] **CI/CD Pipeline aktiviert** (2026-03-02)
  - GitHub Secrets konfiguriert (3 global + 4 per DEV Environment)
  - Container Registry Robot Account `github-ci` für CI/CD erstellt
  - Workflow `stackit-deploy.yml` überarbeitet: Secrets-Injection, Registry-Projektname, kubectl für alle Environments
  - Image Pull Secret auf Cluster mit Robot Account Credentials aktualisiert
  - Dokumentation: `docs/referenz/stackit-container-registry.md` (Konzepte, Auth, Secret-Mapping)
  - Implementierungsplan Phase 1.4 + 5 aktualisiert
- [Infra] **Phase 2: StackIT DEV-Infrastruktur (in Arbeit)**
  - StackIT CLI Setup + Service Account `voeb-terraform` mit API Key
  - Container Registry im Portal aktiviert
  - Terraform `init` + `plan` erfolgreich (SKE Cluster, PostgreSQL Flex, Object Storage)
  - Terraform-Code Fix: `default_region` für Provider v0.80+
  - Runbook-Struktur `docs/runbooks/` mit Index + erstem Runbook (Projekt-Setup)
  - Implementierungsplan aktualisiert mit verifizierten Befehlen
  - Blockiert: SA benötigt `project.admin`-Rolle (wartet auf Org-Admin)
- [Infra] **LLM-Konfiguration (StackIT AI Model Serving)** (2026-02-27)
  - GPT-OSS 120B als primäres Chat-Modell konfiguriert und verifiziert
  - Qwen3-VL 235B als zweites Chat-Modell konfiguriert und verifiziert
  - OpenAI-kompatible API via StackIT (Daten bleiben in DE)
  - Embedding-Modell: Wechsel auf Qwen3-VL-Embedding 8B blockiert (Upstream PR #7541). Fallback nomic-embed-text-v1 aktiv.
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
- [Infra] **CI/CD Pipeline auf Enterprise-Niveau gehärtet** (2026-03-02)
  - Backend + Frontend Build parallel (~8 Min statt ~38 Min sequentiell)
  - Model Server Build entfernt (nutzt Upstream Docker Hub Image)
  - Smoke Test nach Deploy (`/api/health` mit 120s Timeout)
  - `--atomic` für TEST/PROD (automatischer Rollback bei Fehler)
  - `--history-max 5` (Helm Release-Cleanup)
  - Fehlerbehandlung: `|| true` entfernt, echtes Error-Reporting mit `kubectl describe` + Logs
  - Verify-Steps mit `if: always()` (Pod-Status auch bei Fehler sichtbar)
  - Kubeconfig-Ablauf im Header dokumentiert (2026-05-28)
  - Runbook: `docs/runbooks/ci-cd-pipeline.md`

### Fixed
- [Bugfix] Core-Datei-Pfade in `.claude/rules/` und `.claude/hooks/` korrigiert (4 von 7 Pfade waren falsch)
- [Bugfix] **CI/CD Pipeline Helm-Fixes** (2026-03-02)
  - Run #1 fehlgeschlagen: `helm dependency build`-Step fehlte im Deploy-Job → Fix: `f3a22017f`
  - Run #2 fehlgeschlagen: Helm Repos nicht auf CI-Runner registriert → Fix: `64c9c7aca`
  - `helm repo add` für alle 6 Chart-Dependencies in allen 3 Deploy-Jobs (dev/test/prod)
  - 21 Onyx-Upstream-Workflows deaktiviert (irrelevant für Fork, erzeugten Fehler-E-Mails)
- [Bugfix] **API-Server EE-Crash behoben** (2026-03-02)
  - `LICENSE_ENFORCEMENT_ENABLED` hat in Onyx FOSS den Default `"true"` — aktiviert EE-Code-Pfade (`onyx.server.tenants`), die im FOSS-Fork nicht existieren → `ModuleNotFoundError` → CrashLoopBackOff
  - Fix: `LICENSE_ENFORCEMENT_ENABLED: "false"` explizit in `values-common.yaml` gesetzt
- [Bugfix] **Model Server ImagePullBackOff behoben** (2026-03-02)
  - Eigenes Image in StackIT Registry konnte nicht gepullt werden
  - Fix: Upstream Docker Hub Image (`docker.io/onyxdotapp/onyx-model-server:v2.9.8`) statt eigenem Build
- [Bugfix] **Helm Image-Tag-Konstruktion** (2026-03-02)
  - Repository und Tag wurden zusammen gesetzt → Helm erzeugte `repo:latest:sha` (ungültig)
  - Fix: `image.repository` und `image.tag` getrennt per `--set`
- [Bugfix] **Recreate-Strategie für Single-Node DEV** (2026-03-02)
  - RollingUpdate scheiterte auf g1a.4d (4 vCPU) — nicht genug CPU für alte + neue Pods gleichzeitig
  - Fix: kubectl-Patch auf Recreate-Strategie nach Helm Deploy

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
- [x] Infrastruktur Go-Live (DEV 2026-02-27, TEST 2026-03-03)
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

- Sicherheitskonzept: Infrastruktur-Details (Secrets-Management, WAF, etc.)
- Betriebskonzept: StackIT-spezifische Konfiguration
- Testkonzept: Testumgebungen nach Setup

### Dependencies

Dokumentation hängt ab von:
- StackIT Account und Konfiguration
- Entra ID Setup durch VÖB
- LLM Provider: StackIT AI Model Serving (GPT-OSS 120B + Qwen3-VL 235B konfiguriert)

---

## Zugehörige Dateien und Verweise

### Dokumentations-Struktur
```
docs/
├── README.md                                    (Main Index)
├── CHANGELOG.md                                 (This File)
├── sicherheitskonzept.md                        (Security Concept)
├── testkonzept.md                               (Test Strategy)
├── betriebskonzept.md                           (Operations Concept)
├── entra-id-kundenfragen.md                     (Entra ID Fragenkatalog)
├── technisches-feinkonzept/
│   ├── template-modulspezifikation.md           (Template)
│   └── ext-framework.md                         (Extension Framework Spec)
├── adr/
│   ├── adr-001-onyx-foss-als-basis.md           (Platform Choice)
│   ├── adr-002-extension-architektur.md         (Extension Architecture)
│   ├── adr-003-stackit-als-cloud-provider.md    (Cloud Provider)
│   └── adr-004-umgebungstrennung-dev-test-prod.md (Environment Separation)
├── abnahme/
│   ├── abnahmeprotokoll-template.md             (Acceptance Protocol)
│   └── meilensteinplan.md                       (Milestone Plan)
├── runbooks/
│   ├── README.md                                (Runbook Index)
│   ├── stackit-projekt-setup.md                 (StackIT Setup)
│   ├── stackit-postgresql.md                    (PostgreSQL Setup)
│   ├── helm-deploy.md                           (Helm Deploy)
│   ├── ci-cd-pipeline.md                        (CI/CD Pipeline)
│   ├── dns-tls-setup.md                         (DNS/TLS Setup)
│   └── llm-konfiguration.md                     (LLM-Konfiguration)
└── referenz/
    ├── stackit-implementierungsplan.md          (DEV+TEST Step-by-Step)
    ├── stackit-infrastruktur.md                 (Infra Specs + Sizing)
    └── stackit-container-registry.md            (Container Registry)
```

---

## Mitwirkende

- **CCJ**: Projektleitung und Governance
- **JNnovate**: [Scope in Klärung]
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

- **CCJ Projektleitung**: [AUSSTEHEND]
- **CCJ Technical Lead**: Nikolaj Ivanov

---

## Versionshistorie dieser Datei

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|-----------|
| 0.1 | [AUSSTEHEND] | [AUSSTEHEND] | Initial Release |

---

**Letzte Aktualisierung**: 2026-03-03
**Wartete durch**: [AUSSTEHEND]
**Nächste Überprüfung**: [AUSSTEHEND]
