# Meilensteinplan – VÖB Service Chatbot

**Dokumentstatus**: In Vorbereitung
**Letzte Aktualisierung**: [Datum TBD]
**Version**: 0.1

---

## Überblick

Der Meilensteinplan definiert die **Liefergegenstände, Akzeptanzkriterien und Termine** für die formale Abnahme ("Abnahme") des VÖB Service Chatbot durch die VÖB.

Jeder Meilenstein (M1-M6) entspricht eine Projektphase und hat zugehörige Akzeptanzkriterien, die erfüllt sein müssen für Freigabe zur nächsten Phase.

---

## Meilenstein-Übersicht

| Meilenstein | Titel | Phasen | Geplanter Termin | Status |
|-------------|-------|--------|-----------------|--------|
| **M1** | Infrastruktur + Dev Environment | Phase 1-2 | [TBD] | Planned |
| **M2** | Authentifizierung + Extension Framework | Phase 3, 4a | [TBD] | Planned |
| **M3** | Token Limits + RBAC | Phase 4b, 4c | [TBD] | Planned |
| **M4** | Advanced Features (Analytics, Branding, Prompts) | Phase 4d, 4e, 4f | [TBD] | Planned |
| **M5** | Testing, QA & Go-Live Readiness | Phase 5 | [TBD] | Planned |
| **M6** | Production Go-Live | Phase 6 | [TBD] | Planned |

---

## M1: Infrastruktur + Development Environment

### Beschreibung

Die Infrastruktur ist auf StackIT bereitgestellt und das Development Environment ist einsatzbereit.

### Liefergegenstände

- **StackIT Kubernetes Cluster**
  - 3 Nodes (production-ready)
  - Network Policies konfiguriert
  - Load Balancer / Ingress Controller
  - TLS Certificates (Let's Encrypt)

- **Managed Services**
  - PostgreSQL RDS (Primary + Standby Replica)
  - Vespa Cluster (3 Nodes)
  - S3-Compatible Object Storage (Buckets erstellt)

- **Development Environment**
  - Docker Compose für lokale Entwicklung
  - Database Migrations System
  - CI/CD Pipeline Grundlagen (GitHub Actions)
  - VS Code Setup Guide

- **Dokumentation**
  - Infrastruktur-Runbook
  - Development Setup Guide
  - Architecture Documentation (Diagramme)

### Akzeptanzkriterien

| Nr. | Kriterium | Erfüllt? |
|-----|-----------|---------|
| M1-1 | Kubernetes Cluster läuft mit 3 Nodes | [ ] Ja [ ] Nein |
| M1-2 | PostgreSQL erreichbar und funktionsfähig | [ ] Ja [ ] Nein |
| M1-3 | Vespa Cluster deployed und indexierbar | [ ] Ja [ ] Nein |
| M1-4 | Object Storage funktioniert (Upload/Download) | [ ] Ja [ ] Nein |
| M1-5 | TLS/HTTPS aktiviert für alle Endpoints | [ ] Ja [ ] Nein |
| M1-6 | CI/CD Pipeline triggered automatisch bei Push | [ ] Ja [ ] Nein |
| M1-7 | Docker Compose lokal funktioniert | [ ] Ja [ ] Nein |
| M1-8 | Alle Dokumentation abgeschlossen | [ ] Ja [ ] Nein |
| M1-9 | 99.5% Verfügbarkeit über 7 Tage gemessen | [ ] Ja [ ] Nein |
| M1-10 | Security Baseline: Network Policies, Encryption | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **StackIT Infrastructure Team** | Cluster provisioning, managed Services |
| **JNnovate DevOps** | CI/CD, Development Environment, Monitoring |
| **CCJ Project Manager** | Koordination, Akzeptanztest |

### Geplanter Termin

**Start**: [TBD – Phase 1 Beginn]
**Abnahme**: [TBD – ~8 Wochen nach Start]

### Dependencies

Keine (Projekt Start)

### Risiken

- StackIT Capacity-Issues
  - Mitigation: Frühzeitig buchen
- Netzwerk-Komplexität
  - Mitigation: Simple Architektur in M1, komplexe Features später

---

## M2: Authentifizierung + Extension Framework

### Beschreibung

Entra ID Integration ist funktionsfähig. Extension-Architektur ist implementiert und getestet.

### Liefergegenstände

- **Authentifizierungs-Modul (ext_auth)**
  - Entra ID / OIDC Integration
  - JWT Token Management
  - Session Management
  - Login/Logout UI Components
  - API-Protection via Middleware

- **Extension Framework**
  - Extension Registry System
  - Route Registration Mechanism
  - Middleware Chain Extension
  - Database Migration System für Extensions
  - Component Injection Points

- **Core Modifications (7 Files)**
  - src/server/server.ts (Routes)
  - src/server/middleware.ts (Middleware)
  - src/migrations/index.ts (Migrations)
  - src/models/User.ts (User Extension Hooks)
  - src/types/index.ts (Type Extensions)
  - next.config.js (Module Resolution)
  - src/config/extensions.ts (NEW – Registry)

- **Testing**
  - Unit Tests (Auth Module)
  - Integration Tests (Auth + Core)
  - Security Tests (Prompt Injection Prevention)

- **Dokumentation**
  - Module Specification: Authentifizierung & Authorization
  - Extension Developer Guide
  - API Documentation (OpenAPI/Swagger)

### Akzeptanzkriterien

| Nr. | Kriterium | Erfüllt? |
|-----|-----------|---------|
| M2-1 | Benutzer können sich mit Entra ID anmelden | [ ] Ja [ ] Nein |
| M2-2 | JWT Tokens werden korrekt issued und validiert | [ ] Ja [ ] Nein |
| M2-3 | Session Timeout funktioniert (1 Stunde) | [ ] Ja [ ] Nein |
| M2-4 | Extension Registry lädt Extensions automatisch | [ ] Ja [ ] Nein |
| M2-5 | Neue Extension kann hinzugefügt werden ohne Core-Änderungen | [ ] Ja [ ] Nein |
| M2-6 | API Routes mit /api/vob/* Prefix funktionieren | [ ] Ja [ ] Nein |
| M2-7 | Middleware Chain arbeitet korrekt | [ ] Ja [ ] Nein |
| M2-8 | Database Migrations für Extensions funktionieren | [ ] Ja [ ] Nein |
| M2-9 | 80% Code Coverage für Auth Module erreicht | [ ] Ja [ ] Nein |
| M2-10 | Prompt Injection wird blockiert | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **JNnovate Backend Team** | Auth Implementation, Extension Framework |
| **JNnovate QA** | Testing, Security Tests |
| **CCJ / VÖB IT** | Entra ID Configuration, Akzeptanztest |

### Geplanter Termin

**Start**: Nach M1 Abnahme
**Dauer**: 6-8 Wochen
**Abnahme**: [TBD]

### Dependencies

- M1: Infrastruktur funktionsfähig
- Entra ID: VÖB muss Anmeldedaten bereitstellen

### Risiken

- Entra ID Integration komplizierter als erwartet
  - Mitigation: Spike-Story vor vollständiger Implementierung
- Core-Änderungen brechen etwas anderes
  - Mitigation: Gründliches Testing, Review

---

## M3: Token Limits + RBAC

### Beschreibung

Token Limits Management und Role-Based Access Control sind implementiert und getestet.

### Liefergegenstände

- **Token Limits Modul (ext_token_limits)**
  - Quota Management Pro User/Organization
  - Token Counting Logic
  - Rate Limiting Middleware
  - Alert System (bei 80% Nutzung)
  - Admin Dashboard für Quota Management
  - API Endpoints für Quota Verwaltung

- **RBAC Modul (ext_rbac)**
  - ext_user_groups Tabelle
  - Role-Based Access Control
  - User Group Management
  - Permissions-Checking Middleware
  - Admin UI für Group Management

- **Testing**
  - Unit Tests (beide Module)
  - Integration Tests (mit Auth)
  - Security Tests (Permission Bypasses)
  - Load Tests (Token Counting Performance)
  - E2E Tests (User Scenarios)

- **Dokumentation**
  - Module Specifications
  - User Guide (Quota Management)
  - Admin Guide (User Groups)

### Akzeptanzkriterien

| Nr. | Kriterium | Erfüllt? |
|-----|-----------|---------|
| M3-1 | Token Quota wird durchgesetzt (Request rejiziert bei Overflow) | [ ] Ja [ ] Nein |
| M3-2 | Token-Zählung ist akkurat (Vergleich mit OpenAI API) | [ ] Ja [ ] Nein |
| M3-3 | Alerts bei 80% Nutzung werden versendet | [ ] Ja [ ] Nein |
| M3-4 | Monatliches Quota-Reset funktioniert | [ ] Ja [ ] Nein |
| M3-5 | User-Gruppen können erstellt und Benutzer zugewiesen werden | [ ] Ja [ ] Nein |
| M3-6 | Berechtigungen werden basierend auf Gruppen durchgesetzt | [ ] Ja [ ] Nein |
| M3-7 | Nur Admins können Quotas ändern | [ ] Ja [ ] Nein |
| M3-8 | Performance: Token Count < 50ms pro Request | [ ] Ja [ ] Nein |
| M3-9 | Streaming Responses werden korrekt gezählt | [ ] Ja [ ] Nein |
| M3-10 | 85% Code Coverage für beide Module | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **JNnovate Backend** | Token Limits + RBAC Implementation |
| **JNnovate Frontend** | Admin UIs |
| **JNnovate QA** | Testing, Load Tests |
| **CCJ / VÖB** | Requirements Validation, Akzeptanztest |

### Geplanter Termin

**Start**: Nach M2 Abnahme
**Dauer**: 6-8 Wochen
**Abnahme**: [TBD]

### Dependencies

- M2: Authentifizierung + Extension Framework
- LLM Token-Zählung: Definierte Methode erforderlich

---

## M4: Advanced Features (Analytics, Branding, Prompts)

### Beschreibung

Analytics, Branding und System Prompts Management Module sind implementiert.

### Liefergegenstände

- **Branding Modul (ext_branding)**
  - Logo Management
  - Color Scheme Customization
  - Typography Options
  - Multi-Tenant Design Support
  - Admin UI für Branding Config

- **System Prompts Modul (ext_system_prompts)**
  - Prompt Template Management
  - A/B Testing Support
  - Prompt Versioning
  - RAG Context Ranking
  - Admin UI für Prompt Management

- **Analytics Modul (ext_analytics)**
  - Usage Metrics Collection
  - KPI Dashboards
  - User Activity Tracking
  - Chat Quality Metrics
  - Reports Export

- **Testing**
  - Unit Tests
  - Integration Tests
  - E2E Tests (User Scenarios)

- **Dokumentation**
  - Module Specifications
  - Admin Guides
  - User Analytics Guides

### Akzeptanzkriterien

| Nr. | Kriterium | Erfüllt? |
|-----|-----------|---------|
| M4-1 | Custom Logo wird in UI angezeigt | [ ] Ja [ ] Nein |
| M4-2 | Custom Farben werden angewendet | [ ] Ja [ ] Nein |
| M4-3 | System Prompts können erstellt/editiert werden | [ ] Ja [ ] Nein |
| M4-4 | A/B Testing funktioniert (Prompt Variants) | [ ] Ja [ ] Nein |
| M4-5 | Analytics Daten werden korrekt gesammelt | [ ] Ja [ ] Nein |
| M4-6 | Dashboards zeigen KPIs korrekt | [ ] Ja [ ] Nein |
| M4-7 | Reports können exportiert werden (CSV/PDF) | [ ] Ja [ ] Nein |
| M4-8 | Multi-Tenant Branding funktioniert | [ ] Ja [ ] Nein |
| M4-9 | RAG Context wird korrekt ranked | [ ] Ja [ ] Nein |
| M4-10 | 80% Code Coverage | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **JNnovate Backend** | Module Implementation |
| **JNnovate Frontend** | Branding UI, Dashboards |
| **JNnovate QA** | Testing |
| **CCJ / VÖB** | Requirements Validation |

### Geplanter Termin

**Start**: Nach M3 Abnahme
**Dauer**: 8-10 Wochen
**Abnahme**: [TBD]

### Dependencies

- M2: Extension Framework
- M3: Token Limits + RBAC (für Admin Permissions)

---

## M5: Testing, QA & Go-Live Readiness

### Beschreibung

Vollständige Testing durchgeführt. System ist Go-Live ready. Monitoring ist produktiv.

### Liefergegenstände

- **Testberichte**
  - Unit Test Report (80%+ Coverage)
  - Integration Test Report
  - Security Test Report (Pentest)
  - Performance Test Report (Load Tests)
  - UAT Report (VÖB Tester)

- **Monitoring & Operations**
  - Prometheus Monitoring Setup
  - Grafana Dashboards
  - Alert Rules konfiguriert
  - Logging Stack (ELK)
  - Runbooks (Deployment, Incident Response)

- **Documentation**
  - User Manual
  - Admin Manual
  - Operator Manual (Runbooks)
  - Troubleshooting Guide
  - API Documentation

- **Production Readiness**
  - Security Review
  - Compliance Check (DSGVO, BAIT)
  - Go-Live Checklist
  - Rollback Procedures

### Akzeptanzkriterien

| Nr. | Kriterium | Erfüllt? |
|-----|-----------|---------|
| M5-1 | All Tests bestanden (Unit, Integration, E2E, Security) | [ ] Ja [ ] Nein |
| M5-2 | Code Coverage >= 80% | [ ] Ja [ ] Nein |
| M5-3 | Zero Critical Security Issues (Post-Pentest) | [ ] Ja [ ] Nein |
| M5-4 | Performance Anforderungen erfüllt (p99 < 500ms) | [ ] Ja [ ] Nein |
| M5-5 | Monitoring & Alerting Setup abgeschlossen | [ ] Ja [ ] Nein |
| M5-6 | Runbooks geschrieben und getestet | [ ] Ja [ ] Nein |
| M5-7 | DSGVO-Compliance bestätigt | [ ] Ja [ ] Nein |
| M5-8 | BAIT-Anforderungen erfüllt | [ ] Ja [ ] Nein |
| M5-9 | Alle Dokumentation abgeschlossen | [ ] Ja [ ] Nein |
| M5-10 | Go-Live Checklist 100% erfüllt | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **JNnovate QA Lead** | Testing, Test Reports |
| **JNnovate DevOps** | Monitoring, Runbooks |
| **JNnovate Tech Writer** | Documentation |
| **External Security** | Penetration Test |
| **CCJ / VÖB** | UAT, Compliance Check |

### Geplanter Termin

**Start**: Nach M4 Abnahme
**Dauer**: 6-8 Wochen
**Abnahme**: [TBD]

### Dependencies

- M1-M4: Alle Features implementiert und getestet

---

## M6: Production Go-Live

### Beschreibung

System ist produktiv deployed und läuft.

### Liefergegenstände

- **Production Deployment**
  - Docker Images deployed zu Kubernetes
  - Database ist produktiv
  - Monitoring läuft
  - Backups funktionieren

- **Handover**
  - Knowledge Transfer Sessions
  - Operations Team Training
  - Support Contacts etabliert

- **Go-Live Validation**
  - Health Checks bestanden
  - Smoke Tests erfolgreich
  - Monitoring Alerts funktionieren

### Akzeptanzkriterien

| Nr. | Kriterium | Erfüllt? |
|-----|-----------|---------|
| M6-1 | System läuft produktiv (chatbot.vob.example.com) | [ ] Ja [ ] Nein |
| M6-2 | Alle Health Checks green | [ ] Ja [ ] Nein |
| M6-3 | Monitoring sendet Metriken | [ ] Ja [ ] Nein |
| M6-4 | Alerts funktionieren | [ ] Ja [ ] Nein |
| M6-5 | Benutzer können sich anmelden | [ ] Ja [ ] Nein |
| M6-6 | Chat funktioniert | [ ] Ja [ ] Nein |
| M6-7 | Operations Team hat Zugriff | [ ] Ja [ ] Nein |
| M6-8 | Support Prozess etabliert | [ ] Ja [ ] Nein |
| M6-9 | 99.9% Uptime gemessen über 7 Tage | [ ] Ja [ ] Nein |
| M6-10 | Keine Critical Issues im Production Monitoring | [ ] Ja [ ] Nein |

### Verantwortlichkeiten

| Rolle | Aufgaben |
|-------|----------|
| **JNnovate DevOps** | Deployment, Monitoring |
| **StackIT Operations** | Infrastructure Support |
| **CCJ Project Manager** | Go-Live Coordination |
| **VÖB Operations** | Production Operations |

### Geplanter Termin

**Start**: Nach M5 Abnahme
**Dauer**: 2 Wochen (Deployment + Stabilisierung)
**Abnahme**: [TBD]

### Dependencies

- M5: Alle Tests bestanden, Monitoring ready

---

## Gesamt-Timeline (Gantt-Style)

```
Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6
        |         |         |         |         |
  M1    |   M1    |   M2    |   M3 M4 |   M5    |   M6
  +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
  |████████████|
  |                ████████|
  |                        |████████|
  |                                |████████████████|
  |                                                |████████|
  |                                                        |████|

  Week 1      Week 8      Week 14     Week 22     Week 28     Week 30
```

---

## Status & Governance

### Abnahme-Prozess

1. **Vorbereitung** (1 Woche vor geplant Termin)
   - Alle Kriterien testen
   - Test Reports vorbereiten
   - Stakeholder einladen

2. **Abnahme-Meeting**
   - Alle Kriterien durchgehen
   - Mängel dokumentieren (falls vorhanden)
   - Entscheidung: Abnahme ja/nein

3. **Unterschriften**
   - Abnahmeprotokoll unterzeichnet
   - Mängel-Nachbearbeitung (falls erforderlich)

4. **Freigabe**
   - System für nächste Phase freigegeben
   - oder Projekt go-live freigegeben

### Eskalation

Falls Abnahme verweigert wird:
- Mangel-Liste mit Prioritäten erstellen
- Auftragnehmer erstellt Fix-Plan
- Neue Abnahme geplant (1-2 Wochen später)

---

## Kontakt & Weitere Informationen

- **Abnahmeprotokoll-Template**: [06-abnahme/abnahmeprotokoll-template.md](./abnahmeprotokoll-template.md)
- **Testkonzept**: [03-testkonzept/testkonzept.md](../03-testkonzept/testkonzept.md)
- **Technisches Feinkonzept**: [01-technisches-feinkonzept/README.md](../01-technisches-feinkonzept/README.md)

---

**Dokumentstatus**: In Vorbereitung
**Letzte Aktualisierung**: [Datum TBD]
**Version**: 0.1
