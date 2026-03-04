# Meilensteinplan -- VÖB Service Chatbot

**Dokumentstatus**: In Bearbeitung
**Letzte Aktualisierung**: 2026-03-03
**Version**: 0.2

---

## Überblick

Der Meilensteinplan definiert die **Liefergegenstände, Akzeptanzkriterien und Termine** für die formale Abnahme des VÖB Service Chatbot durch die VÖB.

Jeder Meilenstein (M1-M6) entspricht einer Projektphase und hat zugehörige Akzeptanzkriterien, die erfüllt sein müssen für die Freigabe zur nächsten Phase.

**Auftraggeber:** VÖB (Bundesverband Öffentlicher Banken Deutschlands)
**Auftragnehmer:** CCJ / Coffee Studios (Tech Lead: Nikolaj Ivanov)
**Cloud:** StackIT (Kubernetes, Datensouveränität, Region EU01 Frankfurt)
**Basis:** Fork von Onyx FOSS (MIT-Lizenz) mit Custom Extension Layer

---

## Meilenstein-Übersicht

| Meilenstein | Titel | Phasen | Termin | Status |
|-------------|-------|--------|--------|--------|
| **M1** | Infrastruktur + DEV/TEST | Phase 0-2 | 2026-02-27 (DEV) / 2026-03-03 (TEST) | Abgeschlossen |
| **M2** | Authentifizierung (Entra ID) + Extension Framework | Phase 3, 4a | [TBD] | Blockiert (Entra ID) |
| **M3** | Token Limits + RBAC | Phase 4b, 4c | [TBD] | Geplant |
| **M4** | Advanced Features (Analytics, Branding, Prompts) | Phase 4d, 4e, 4f | [TBD] | Geplant |
| **M5** | Testing, Security Hardening + Go-Live Readiness | Phase 5 | [TBD] | Geplant |
| **M6** | Production Go-Live | Phase 6 | [TBD] | Geplant |

---

## M1: Infrastruktur + DEV/TEST Environment

### Beschreibung

Die Cloud-Infrastruktur ist auf StackIT provisioniert, DEV- und TEST-Umgebung sind betriebsbereit, die CI/CD-Pipeline ist produktionsreif, und LLM-Modelle sind konfiguriert.

### Status: Abgeschlossen

- **DEV LIVE**: 2026-02-27 (`http://188.34.74.187`)
- **TEST LIVE**: 2026-03-03 (`http://188.34.118.201`)
- **CI/CD produktionsreif**: 2026-03-02 (Run #5 gruen)

### Liefergegenstände

- **StackIT Kubernetes Cluster (SKE)**
  - 1 Cluster `vob-chatbot`, Node Pool `devtest` mit 2x g1a.4d (4 vCPU, 16 GB RAM je)
  - Kubernetes v1.32.12, Flatcar OS
  - Ingress Controller (NGINX) je Umgebung (DEV: `nginx`, TEST: `nginx-test`)
  - Load Balancer: DEV `188.34.74.187`, TEST `188.34.118.201`
  - Architekturentscheidung: [ADR-004](../adr/adr-004-umgebungstrennung-dev-test-prod.md)

- **Managed Services**
  - 2x PostgreSQL Flex 2.4 Single (2 CPU, 4 GB RAM, 20 GB SSD): `vob-dev` + `vob-test`
  - PostgreSQL ACL eingeschraenkt auf Cluster-Egress-IP `188.34.93.194/32` (SEC-01)
  - 2x Object Storage Bucket: `vob-dev` + `vob-test` (S3-kompatibel)
  - Vespa (in-cluster, je Namespace)
  - Redis (in-cluster, je Namespace)

- **LLM-Integration (StackIT AI Model Serving)**
  - Chat-Modell: GPT-OSS 120B (131K Kontext) -- verifiziert 2026-02-27
  - Chat-Modell: Qwen3-VL 235B (218K Kontext) -- verifiziert 2026-02-27
  - Embedding-Modell: nomic-embed-text-v1 aktiv (Fallback). Wechsel auf Qwen3-VL-Embedding 8B blockiert (Upstream PR #7541).
  - Konfiguration: OpenAI-kompatible API via LiteLLM, reine Admin-UI-Konfiguration

- **CI/CD Pipeline (GitHub Actions)**
  - Workflow: `.github/workflows/stackit-deploy.yml`
  - Parallel-Build Backend + Frontend (~10 Min gesamt)
  - Model Server: Docker Hub Upstream `v2.9.8` (gepinnt)
  - DEV: automatisch bei `develop`-Push. TEST/PROD: manuell via `workflow_dispatch`
  - SHA-gepinnte GitHub Actions (Supply-Chain-Schutz)
  - Concurrency Control, Least-Privilege Permissions
  - Smoke Test (`/api/health`, 120s Timeout) -- nur fuer DEV + TEST. PROD: `kubectl rollout status` Verify-Step
  - `--atomic` fuer TEST/PROD (automatischer Rollback)

- **Development Environment**
  - Docker Compose fuer lokale Entwicklung
  - Extension Framework Basis (Phase 4a, vorgezogen): `backend/ext/`, Feature Flags, Health Endpoint
  - Database Migrations System (Alembic)

- **Dokumentation**
  - Infrastruktur-Runbooks: [Projekt-Setup](../runbooks/stackit-projekt-setup.md), [PostgreSQL](../runbooks/stackit-postgresql.md), [Helm Deploy](../runbooks/helm-deploy.md), [CI/CD Pipeline](../runbooks/ci-cd-pipeline.md)
  - [Implementierungsplan](../referenz/stackit-implementierungsplan.md)
  - [Technische Infrastruktur-Referenz](../referenz/stackit-infrastruktur.md)
  - [Container Registry Dokumentation](../referenz/stackit-container-registry.md)
  - ADR-001 bis ADR-004

### Akzeptanzkriterien

| Nr. | Kriterium | Status |
|-----|-----------|--------|
| M1-1 | Kubernetes Cluster laeuft mit 2 Nodes (g1a.4d) | [x] Ja |
| M1-2 | DEV: PostgreSQL erreichbar und funktionsfaehig | [x] Ja |
| M1-3 | DEV: Vespa deployed und lauffaehig | [x] Ja |
| M1-4 | DEV: Object Storage Bucket `vob-dev` funktioniert | [x] Ja |
| M1-5 | DEV: Alle 10 Pods Running in `onyx-dev` | [x] Ja |
| M1-6 | DEV: API Health Check `http://188.34.74.187/api/health` OK | [x] Ja |
| M1-7 | DEV: LLM Chat-Modell antwortet korrekt (GPT-OSS 120B) | [x] Ja |
| M1-8 | TEST: PostgreSQL erreichbar (eigene Instanz `vob-test`) | [x] Ja |
| M1-9 | TEST: Object Storage Bucket `vob-test` funktioniert | [x] Ja |
| M1-10 | TEST: Pods Running in `onyx-test`, Health Check OK | [x] Ja |
| M1-11 | CI/CD Pipeline funktioniert (Push triggert Build + Deploy) | [x] Ja |
| M1-12 | SEC-01: PostgreSQL ACL eingeschraenkt (nicht 0.0.0.0/0) | [x] Ja |
| M1-13 | Alle Runbooks vorhanden und verifiziert | [x] Ja |

### Offen / Nacharbeiten

| Nr. | Thema | Status |
|-----|-------|--------|
| M1-N1 | DNS-Eintraege (`dev.chatbot.voeb-service.de` / `test.chatbot.voeb-service.de`) | Blockiert (VÖB IT, Leif) |
| M1-N2 | TLS/HTTPS (nach DNS-Setup) | Blockiert (DNS) |
| M1-N3 | Embedding-Modell (Qwen3-VL-Embedding 8B) konfigurieren | ⚠️ Blockiert (Upstream PR #7541). Fallback nomic-embed-text-v1 aktiv, RAG funktional. |
| M1-N4 | LLM in TEST Admin UI konfigurieren | ✅ Erledigt (2026-03-03) |
| M1-N5 | CI/CD `workflow_dispatch` fuer TEST verifizieren | ✅ Erledigt (2026-03-03) |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **CCJ / Nikolaj Ivanov** | Terraform, Helm, CI/CD, LLM-Konfiguration, Runbooks, komplette technische Umsetzung |
| **VÖB IT** | DNS-Eintraege bereitstellen |
| **StackIT** | Managed Services (SKE, PostgreSQL Flex, Object Storage, AI Model Serving) |

### Termine

**Start**: Phase 0-1 (Dokumentation, lokale Entwicklung)
**DEV LIVE**: 2026-02-27
**CI/CD produktionsreif**: 2026-03-02
**TEST LIVE**: 2026-03-03

### Dependencies

Keine (Projekt Start)

### Risiken (eingetreten und geloest)

- **CPU Insufficient bei Rolling Update auf Single-Node** -- geloest mit Recreate-Strategie
- **EE-Crash** (`LICENSE_ENFORCEMENT_ENABLED` Default `true`) -- geloest mit explizitem `"false"` in values-common.yaml
- **Model Server ImagePullBackOff** -- geloest mit Upstream Docker Hub Image statt eigenem Build
- **IngressClass Conflict** (DEV + TEST im selben Cluster) -- geloest mit eigener IngressClass `nginx-test`

---

## M2: Authentifizierung (Entra ID) + Extension Framework

### Beschreibung

Entra ID / OIDC Integration ist funktionsfaehig. Das Extension Framework ist implementiert und getestet (Phase 4a bereits abgeschlossen).

### Status: Blockiert

Phase 4a (Extension Framework Basis) ist bereits abgeschlossen. Die Entra ID Integration wartet auf Zugangsdaten von VÖB.

### Liefergegenstände

- **Extension Framework (Phase 4a)** -- bereits implementiert
  - `backend/ext/` Paketstruktur mit Feature Flags (`config.py`)
  - Router-Registrierung via Hook in `backend/onyx/main.py` (einzige Core-Datei-Aenderung bisher)
  - Health Endpoint `GET /api/ext/health` (authentifiziert)
  - Docker-Deployment: `docker-compose.voeb.yml` + `Dockerfile.voeb`
  - 10 Unit-Tests (5x Config Flags, 5x Health Endpoint)
  - Modulspezifikation: [ext-framework.md](../technisches-feinkonzept/ext-framework.md)

- **Authentifizierungs-Integration (Entra ID)**
  - Onyx unterstuetzt OIDC nativ (`AUTH_TYPE: oidc` in Helm Values)
  - Entra ID OIDC Konfiguration in Helm Values
  - Session Management (Onyx-nativ)
  - Login/Logout ueber Onyx UI

- **Core-Aenderungen (7 erlaubte Dateien)**
  - `backend/onyx/main.py` -- Router-Registrierung (bereits implementiert in Phase 4a)
  - `backend/onyx/llm/multi_llm.py` -- Token Hook (Phase 4b)
  - `backend/onyx/access/access.py` -- RBAC Check (Phase 4c)
  - `backend/onyx/chat/prompt_utils.py` -- Prompt Injection (Phase 4f)
  - `web/src/app/layout.tsx` -- Navigation (Phase 4d+)
  - `web/src/components/header/` -- Branding (Phase 4e)
  - `web/src/lib/constants.ts` -- CSS Variables (Phase 4e)

- **Testing**
  - Unit Tests (Extension Framework)
  - Integration Tests (Auth + Extension Framework)

- **Dokumentation**
  - Modulspezifikation: Authentifizierung
  - Extension Developer Guide
  - API Documentation

### Akzeptanzkriterien

| Nr. | Kriterium | Erfuellt? |
|-----|-----------|---------|
| M2-1 | Benutzer koennen sich mit Entra ID anmelden | [ ] Ja [ ] Nein |
| M2-2 | Session Management funktioniert (Timeout) | [ ] Ja [ ] Nein |
| M2-3 | Extension Framework: Feature Flags funktionieren | [x] Ja (Phase 4a) |
| M2-4 | Extension Framework: Neue Extension kann hinzugefuegt werden ohne weitere Core-Aenderungen | [x] Ja (Phase 4a) |
| M2-5 | API Routes mit `/api/ext/*` Prefix funktionieren | [x] Ja (Phase 4a) |
| M2-6 | Health Endpoint zeigt Status aller Module | [x] Ja (Phase 4a) |
| M2-7 | Hook-Pattern: `try/except ImportError` bricht Onyx nie | [x] Ja (Phase 4a) |
| M2-8 | Unit Tests fuer Extension Framework bestanden | [x] Ja (Phase 4a) |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **CCJ / Nikolaj Ivanov** | Auth-Konfiguration (Helm Values), Extension Framework (abgeschlossen) |
| **VÖB IT** | Entra ID Zugangsdaten bereitstellen (OIDC Client ID, Tenant ID, Client Secret) |

### Termine

**Extension Framework (Phase 4a)**: Abgeschlossen (2026-02-12)
**Entra ID Integration**: [TBD] -- blockiert durch fehlende Zugangsdaten von VÖB

### Dependencies

- M1: Infrastruktur funktionsfaehig -- erfuellt
- Entra ID: VÖB muss Zugangsdaten bereitstellen -- **Blocker**

### Risiken

- Entra ID Zugangsdaten verzoegern sich weiter
  - Mitigation: System laeuft mit `AUTH_TYPE: basic` bis Entra ID verfuegbar
- Onyx OIDC-Integration erfordert Anpassungen
  - Mitigation: Onyx unterstuetzt OIDC nativ, Spike-Story vor vollstaendiger Konfiguration

---

## M3: Token Limits + RBAC

### Beschreibung

Token Limits Management und Role-Based Access Control sind implementiert und getestet.

### Liefergegenstände

- **Token Limits Modul (`ext_token_limits`)**
  - Token Hook in `backend/onyx/llm/multi_llm.py` (Core-Datei #2)
  - Quota Management pro User/Organisation
  - Token Counting Logic
  - Alert System (bei hoher Nutzung)
  - Admin-Endpunkte fuer Quota-Verwaltung
  - DB-Tabellen: `ext_limits_quota`, `ext_limits_usage_log`, `ext_limits_alerts`

- **RBAC Modul (`ext_user_groups`)**
  - Additiver Permission-Check in `backend/onyx/access/access.py` (Core-Datei #3)
  - DB-Tabelle: `ext_user_groups`
  - User Group Management
  - Admin-Endpunkte fuer Group Management

- **Testing**
  - Unit Tests (beide Module)
  - Integration Tests (mit Auth)
  - Performance Tests (Token Counting)

- **Dokumentation**
  - Modulspezifikationen (Token Limits, RBAC)
  - Admin Guide

### Akzeptanzkriterien

| Nr. | Kriterium | Erfuellt? |
|-----|-----------|---------|
| M3-1 | Token Quota wird durchgesetzt (Request abgelehnt bei Ueberschreitung) | [ ] Ja [ ] Nein |
| M3-2 | Token-Zaehlung ist akkurat | [ ] Ja [ ] Nein |
| M3-3 | Monatliches Quota-Reset funktioniert | [ ] Ja [ ] Nein |
| M3-4 | User-Gruppen koennen erstellt und Benutzer zugewiesen werden | [ ] Ja [ ] Nein |
| M3-5 | Berechtigungen werden basierend auf Gruppen durchgesetzt | [ ] Ja [ ] Nein |
| M3-6 | Nur Admins koennen Quotas und Gruppen aendern | [ ] Ja [ ] Nein |
| M3-7 | Streaming Responses werden korrekt gezaehlt | [ ] Ja [ ] Nein |
| M3-8 | Hook-Pattern: Fehler in ext bricht Onyx nie | [ ] Ja [ ] Nein |
| M3-9 | Feature Flags: Module einzeln ein-/ausschaltbar | [ ] Ja [ ] Nein |
| M3-10 | Unit + Integration Tests bestanden | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **CCJ / Nikolaj Ivanov** | Token Limits + RBAC Implementation (Backend + Frontend) |
| **VÖB** | Requirements Validation, Akzeptanztest |

### Termine

**Start**: Nach M2 Abnahme
**Abnahme**: [TBD]

### Dependencies

- M2: Authentifizierung + Extension Framework
- LLM Token-Zaehlung: StackIT AI Model Serving gibt Token-Counts in Response zurueck (OpenAI-kompatibel)

---

## M4: Advanced Features (Analytics, Branding, Prompts)

### Beschreibung

Analytics, Branding und System Prompts Management Module sind implementiert.

### Liefergegenstände

- **Branding Modul (`ext_branding`)**
  - Logo/Titel via Config in `web/src/components/header/` (Core-Datei #5) mit Fallback auf Original
  - CSS Variables mit `--ext-` Prefix in `web/src/lib/constants.ts` (Core-Datei #6)
  - Nav-Items in `web/src/app/layout.tsx` (Core-Datei #4)
  - DB-Tabelle: `ext_branding_config`

- **System Prompts Modul (`ext_custom_prompts`)**
  - Prompt Injection Hook in `backend/onyx/chat/prompt_utils.py` (Core-Datei #7)
  - Prompt Template Management
  - Prompt Versioning
  - Admin-Endpunkte fuer Prompt Management

- **Analytics Modul (`ext_analytics`)**
  - Usage Metrics Collection
  - DB-Tabelle: `ext_analytics_events`
  - Reports Export

- **Testing**
  - Unit Tests
  - Integration Tests

- **Dokumentation**
  - Modulspezifikationen (Branding, Prompts, Analytics)
  - Admin Guides

### Akzeptanzkriterien

| Nr. | Kriterium | Erfuellt? |
|-----|-----------|---------|
| M4-1 | Custom Logo wird in UI angezeigt (mit Fallback auf Original) | [ ] Ja [ ] Nein |
| M4-2 | CSS Variables mit `--ext-` Prefix werden angewendet | [ ] Ja [ ] Nein |
| M4-3 | System Prompts koennen erstellt/editiert/versioniert werden | [ ] Ja [ ] Nein |
| M4-4 | Prompt Injection (prepend) funktioniert ohne bestehenden Prompt-Flow zu veraendern | [ ] Ja [ ] Nein |
| M4-5 | Analytics Daten werden korrekt gesammelt | [ ] Ja [ ] Nein |
| M4-6 | Reports koennen exportiert werden | [ ] Ja [ ] Nein |
| M4-7 | Alle Module hinter Feature Flags (`EXT_BRANDING_ENABLED`, etc.) | [ ] Ja [ ] Nein |
| M4-8 | Hook-Pattern: Fehler in ext bricht Onyx nie | [ ] Ja [ ] Nein |
| M4-9 | Unit + Integration Tests bestanden | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **CCJ / Nikolaj Ivanov** | Module Implementation (Backend + Frontend) |
| **VÖB** | Requirements Validation, Branding-Assets bereitstellen |

### Termine

**Start**: Nach M3 Abnahme
**Abnahme**: [TBD]

### Dependencies

- M2: Extension Framework (fuer Router-Registrierung + Feature Flags)
- M3: Token Limits + RBAC (fuer Admin Permissions)

---

## M5: Testing, Security Hardening + Go-Live Readiness

### Beschreibung

Vollstaendiges Testing durchgefuehrt. Security-Haertung abgeschlossen. System ist Go-Live ready.

### Liefergegenstände

- **Security-Haertung (P1 -- vor PROD)**
  - SEC-02: Node Affinity erzwingen (DEV/TEST auf eigene Nodes)
  - SEC-03: Kubernetes NetworkPolicies (Namespace-Isolation auf Netzwerkebene)
  - SEC-04: Terraform Remote State (State-Bucket statt lokaler State)
  - SEC-05: Separate Kubeconfigs pro Environment (Least-Privilege CI/CD)

- **Security-Haertung (P2 -- vor Abnahme)**
  - SEC-06: Container SecurityContext (`runAsNonRoot`, `readOnlyRootFilesystem`)
  - SEC-07: Encryption-at-Rest verifizieren (PG Flex + Object Storage)

- **Testberichte**
  - Unit Test Report
  - Integration Test Report
  - Security Test Report (Pentest)
  - Performance Test Report
  - UAT Report (VÖB Tester)

- **PROD Cluster provisionieren**
  - Eigener SKE-Cluster (ADR-004: separater Cluster fuer Blast-Radius-Minimierung)
  - 2-3x g1a.4d Nodes
  - PostgreSQL Flex 4.8 Replica (HA, 3 Nodes)
  - Eigene Network Policies, strengere Security
  - Eigenes Maintenance-Window

- **Monitoring + Operations**
  - Prometheus/Grafana Stack
  - Alert Rules
  - Runbooks (Deployment, Incident Response)

- **Dokumentation**
  - [Sicherheitskonzept](../sicherheitskonzept.md) finalisiert
  - [Testkonzept](../testkonzept.md) mit Testergebnissen
  - [Betriebskonzept](../betriebskonzept.md) finalisiert
  - DSGVO-/BAIT-Compliance-Nachweis

- **Production Readiness**
  - DNS konfiguriert (VÖB IT)
  - TLS/HTTPS aktiviert
  - Go-Live Checklist
  - Rollback Procedures

### Akzeptanzkriterien

| Nr. | Kriterium | Erfuellt? |
|-----|-----------|---------|
| M5-1 | Alle Tests bestanden (Unit, Integration, Security) | [ ] Ja [ ] Nein |
| M5-2 | Zero Critical Security Issues (Post-Pentest) | [ ] Ja [ ] Nein |
| M5-3 | SEC-02 bis SEC-07 umgesetzt | [ ] Ja [ ] Nein |
| M5-4 | PROD-Cluster provisioniert und validiert | [ ] Ja [ ] Nein |
| M5-5 | Monitoring + Alerting funktionsfaehig | [ ] Ja [ ] Nein |
| M5-6 | DNS konfiguriert, TLS/HTTPS aktiv | [ ] Ja [ ] Nein |
| M5-7 | DSGVO-Compliance bestaetigt | [ ] Ja [ ] Nein |
| M5-8 | BAIT-Anforderungen erfuellt | [ ] Ja [ ] Nein |
| M5-9 | Alle Dokumentation abgeschlossen | [ ] Ja [ ] Nein |
| M5-10 | Go-Live Checklist 100% erfuellt | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **CCJ / Nikolaj Ivanov** | Security-Haertung, PROD-Cluster, Testing, Monitoring |
| **VÖB** | UAT, Compliance-Pruefung, DNS-Eintraege |
| **Externer Dienstleister** | Penetration Test (falls beauftragt) |

### Termine

**Start**: Nach M4 Abnahme
**Abnahme**: [TBD]

### Dependencies

- M1-M4: Alle Features implementiert und getestet
- DNS: VÖB IT muss Eintraege bereitstellen

---

## M6: Production Go-Live

### Beschreibung

System ist produktiv deployed, validiert und an VÖB uebergeben.

### Liefergegenstände

- **Production Deployment**
  - Helm Deploy auf PROD-Cluster
  - Datenbank produktiv
  - Monitoring laeuft
  - Backups funktionieren (PG Flex taegliches Backup)

- **Handover**
  - Knowledge Transfer Sessions
  - Admin-Schulung (LLM-Konfiguration, User Management, Extension Module)
  - Support-Kontakte etabliert

- **Go-Live Validation**
  - Health Checks bestanden
  - Smoke Tests erfolgreich
  - Monitoring Alerts funktionieren
  - Entra ID Login in Production verifiziert

### Akzeptanzkriterien

| Nr. | Kriterium | Erfuellt? |
|-----|-----------|---------|
| M6-1 | System laeuft produktiv unter PROD-Domain | [ ] Ja [ ] Nein |
| M6-2 | Alle Health Checks gruen | [ ] Ja [ ] Nein |
| M6-3 | Monitoring sendet Metriken | [ ] Ja [ ] Nein |
| M6-4 | Alerts funktionieren | [ ] Ja [ ] Nein |
| M6-5 | Benutzer koennen sich mit Entra ID anmelden | [ ] Ja [ ] Nein |
| M6-6 | Chat funktioniert (LLM via StackIT AI Model Serving) | [ ] Ja [ ] Nein |
| M6-7 | Token Limits und RBAC aktiv | [ ] Ja [ ] Nein |
| M6-8 | VÖB Admin-Team hat Zugriff und Schulung erhalten | [ ] Ja [ ] Nein |
| M6-9 | Support-Prozess etabliert | [ ] Ja [ ] Nein |
| M6-10 | Keine Critical Issues im Production Monitoring ueber 7 Tage | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **CCJ / Nikolaj Ivanov** | Deployment, Monitoring, Schulung |
| **StackIT** | Infrastructure Support |
| **VÖB** | Production Operations, Abnahme |

### Termine

**Start**: Nach M5 Abnahme
**Dauer**: 2 Wochen (Deployment + Stabilisierung)
**Abnahme**: [TBD]

### Dependencies

- M5: Alle Tests bestanden, PROD-Cluster ready, Monitoring funktionsfaehig

---

## Aktive Blocker

| Blocker | Wartet auf | Impact |
|---------|-----------|--------|
| Entra ID Zugangsdaten | VÖB IT | Blockiert M2 (Auth) |
| JNnovate Scope | JNnovate | Aufgabenverteilung unklar |
| DNS-Eintraege | VÖB IT | Blockiert TLS/HTTPS |

---

## Erledigte Meilensteine -- Zusammenfassung

### M1 (Abgeschlossen)

| Datum | Ereignis |
|-------|----------|
| 2026-02-12 | Phase 1: StackIT Projekt eingerichtet (CLI, SA, Container Registry) |
| 2026-02-12 | Phase 4a: Extension Framework Basis implementiert (vorgezogen) |
| 2026-02-22 | Phase 2: Terraform apply DEV (SKE Cluster, PG Flex, Object Storage) |
| 2026-02-27 | Phase 2: Helm Deploy DEV -- 10 Pods Running, API Health OK |
| 2026-02-27 | Phase 2: LLM konfiguriert (GPT-OSS 120B + Qwen3-VL 235B) |
| 2026-03-02 | CI/CD Pipeline produktionsreif (Run #5 gruen, ~10 Min) |
| 2026-03-02 | 21 Onyx-Upstream-Workflows deaktiviert |
| 2026-03-03 | SEC-01: PostgreSQL ACL eingeschraenkt |
| 2026-03-03 | TEST LIVE: Node Pool 2 Nodes, PG `vob-test`, Bucket `vob-test`, 9 Pods Running |

---

## Status & Governance

### Abnahme-Prozess

1. **Vorbereitung** (1 Woche vor geplantem Termin)
   - Alle Kriterien testen
   - Test Reports vorbereiten
   - Stakeholder einladen

2. **Abnahme-Meeting**
   - Alle Kriterien durchgehen
   - Maengel dokumentieren (falls vorhanden)
   - Entscheidung: Abnahme ja/nein

3. **Unterschriften**
   - Abnahmeprotokoll unterzeichnet (Template: [abnahmeprotokoll-template.md](./abnahmeprotokoll-template.md))
   - Maengel-Nachbearbeitung (falls erforderlich)

4. **Freigabe**
   - System fuer naechste Phase freigegeben
   - oder Projekt Go-Live freigegeben

### Eskalation

Falls Abnahme verweigert wird:
- Mangel-Liste mit Prioritaeten erstellen
- Auftragnehmer erstellt Fix-Plan
- Neue Abnahme geplant (1-2 Wochen spaeter)

---

## Referenz-Dokumente

| Dokument | Pfad |
|----------|------|
| Abnahmeprotokoll-Template | [abnahmeprotokoll-template.md](./abnahmeprotokoll-template.md) |
| Testkonzept | [testkonzept.md](../testkonzept.md) |
| Sicherheitskonzept | [sicherheitskonzept.md](../sicherheitskonzept.md) |
| Betriebskonzept | [betriebskonzept.md](../betriebskonzept.md) |
| Implementierungsplan | [stackit-implementierungsplan.md](../referenz/stackit-implementierungsplan.md) |
| Extension Framework Spec | [ext-framework.md](../technisches-feinkonzept/ext-framework.md) |
| ADR-001: Onyx FOSS | [adr-001](../adr/adr-001-onyx-foss-als-basis.md) |
| ADR-002: Extension-Architektur | [adr-002](../adr/adr-002-extension-architektur.md) |
| ADR-003: StackIT Cloud | [adr-003](../adr/adr-003-stackit-als-cloud-provider.md) |
| ADR-004: Umgebungstrennung | [adr-004](../adr/adr-004-umgebungstrennung-dev-test-prod.md) |

---

**Dokumentstatus**: In Bearbeitung
**Letzte Aktualisierung**: 2026-03-03
**Version**: 0.2
