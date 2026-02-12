# Betriebskonzept – VÖB Service Chatbot

**Dokumentstatus**: Entwurf
**Letzte Aktualisierung**: [Datum TBD]
**Version**: 0.1

---

## Einleitung und Geltungsbereich

Das Betriebskonzept beschreibt die operativen Anforderungen, Prozesse und Richtlinien für den Betrieb des VÖB Service Chatbot in der Production-Umgebung und darüber hinaus.

### Zielgruppe
- Operations / DevOps Team (StackIT + JNnovate)
- Incident Management / On-Call Team
- Auftraggeber (VÖB Operations)
- Stakeholder und Führungskräfte

---

## Systemübersicht

### Architektur-Diagramm

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

```
┌────────────────────────────────────────────────────────────────┐
│ Internet / Benutzer                                            │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓ HTTPS (TLS 1.2+)

┌────────────────────────────────────────────────────────────────┐
│ StackIT Cloud – Frankfurt                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Kubernetes Cluster (vob-chatbot-prod)                   │ │
│  │                                                          │ │
│  │  Ingress + TLS Termination                              │ │
│  │  ├── Domain: chatbot.vob.example.com                    │ │
│  │  └── Certificate: Let's Encrypt or CA                   │ │
│  │                                                          │ │
│  │  Pods (Frontend)                                        │ │
│  │  ├── Replicas: 3 (HA)                                   │ │
│  │  ├── Image: vob-chatbot-frontend:latest                │ │
│  │  └── Port: 3000                                         │ │
│  │                                                          │ │
│  │  Pods (Backend)                                         │ │
│  │  ├── Replicas: 3 (HA)                                   │ │
│  │  ├── Image: vob-chatbot-backend:latest                 │ │
│  │  └── Port: 8080                                         │ │
│  │                                                          │ │
│  │  Pods (Vespa Vector Store)                             │ │
│  │  ├── Nodes: 3 (HA)                                      │ │
│  │  ├── Storage: Persistent Volumes                        │ │
│  │  └── Port: 8081                                         │ │
│  │                                                          │ │
│  │  Pods (Monitoring)                                      │ │
│  │  ├── Prometheus (metrics scraping)                      │ │
│  │  ├── ELK Stack (log aggregation)                        │ │
│  │  └── AlertManager (alerts)                              │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│              ↓ Internal Networking                            │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Managed PostgreSQL (RDS)                                 │ │
│  │                                                          │ │
│  │  Primary: db.standard.2 (HA, Multi-AZ)                 │ │
│  │  Replicas: 1 Read Replica (Standby)                    │ │
│  │  Storage: 500 GB (SSD)                                  │ │
│  │  Backup: Daily snapshots (30 days retention)           │ │
│  │  TLS: Encrypted connections (mandatory)                │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│              ↓                                                 │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ S3-Compatible Object Storage                            │ │
│  │                                                          │ │
│  │  Buckets:                                               │ │
│  │  - vob-chatbot-backups (Database Backups)              │ │
│  │  - vob-chatbot-assets (User Uploads, Logos, etc.)      │ │
│  │  - vob-chatbot-logs-archive (Log Archival)             │ │
│  │                                                          │ │
│  │  Lifecycle: Auto-archive old objects to cold storage    │ │
│  │  Encryption: AES-256 at rest                           │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Komponenten-Übersicht

| Komponente | Technologie | Zweck | HA | Backup |
|-----------|------------|-------|----|----|
| Frontend | Next.js / React | Web UI | 3 Replicas | None |
| Backend API | Node.js / Express | API Server | 3 Replicas | Git (Code) |
| Vespa | Search Engine | RAG + Vector Store | 3 Nodes | Snapshots |
| PostgreSQL | RDS Managed | Relational Data | Primary + Standby | Daily Snapshots |
| Object Storage | S3-Compatible | Backups + Assets | Replicated | Versioning |

---

## Deployment-Prozess

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

### CI/CD Pipeline

```
Git Push (Feature Branch)
  ↓
GitHub Actions Workflow
  ├── Run Tests (Unit + Integration)
  ├── Build Docker Images
  │   ├── vob-chatbot-frontend:commit-hash
  │   └── vob-chatbot-backend:commit-hash
  ├── Push to Container Registry (StackIT)
  └── Create PR (manual review required)

PR Approved
  ↓
Merge to Main Branch
  ↓
GitHub Actions (Main)
  ├── Run Full Test Suite
  ├── Build Release Images
  │   ├── vob-chatbot-frontend:v1.2.3
  │   └── vob-chatbot-backend:v1.2.3
  ├── Push to Container Registry
  ├── Create GitHub Release
  ├── Deploy to Staging (automatic)
  └── Wait for Manual Approval

Manual Approval to Production
  ↓
Deploy to Production
  ├── Run Database Migrations
  ├── Deploy new Pods (rolling update)
  ├── Health Checks
  └── Smoke Tests

Production Live
  ↓
Monitor for Issues
```

### Helm-basiertes Deployment

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

```bash
# Structure
helm/
├── vob-chatbot/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-staging.yaml
│   ├── values-prod.yaml
│   ├── templates/
│   │   ├── deployment-frontend.yaml
│   │   ├── deployment-backend.yaml
│   │   ├── service-frontend.yaml
│   │   ├── service-backend.yaml
│   │   ├── ingress.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   └── hpa.yaml (HorizontalPodAutoscaler)

# Deployment Commands
helm install vob-chatbot ./helm/vob-chatbot \
  -n vob-chatbot-prod \
  -f helm/vob-chatbot/values-prod.yaml

# Upgrade
helm upgrade vob-chatbot ./helm/vob-chatbot \
  -n vob-chatbot-prod \
  -f helm/vob-chatbot/values-prod.yaml
```

### Rollback-Strategie

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

**Szenarien**:

1. **Fehlerhafte Deployment (vor Health Check)**
   - Automated Rollback via Kubernetes Deployment
   - Original Replicas werden neu gestartet
   - RTO: ~5 Minuten

2. **Laufzeitfehler (nach Deployment)**
   - Alerting erkennt Issue
   - Manual Rollback via Helm
   - `helm rollback vob-chatbot -n vob-chatbot-prod`
   - RTO: ~10 Minuten

3. **Datenbankmigrationen Problem**
   - Pre-Migration Backup erstellen
   - Migration testen in Staging
   - Nur mit Approval in Prod deployen
   - Reverse Migration vorbereitet

---

## Monitoring und Alerting

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

### Health Checks

#### Liveness Probe (Pod am Leben?)
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

#### Readiness Probe (Pod bereit für Traffic?)
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 2
```

### Metriken (Prometheus)

**Zu überwachen**:

| Metrik | Schwellwert | Aktion |
|--------|------------|--------|
| API Response Time (p99) | > 1000ms | Warning Alert |
| Pod Restart Count | > 0 in 5 Min | Critical Alert |
| Memory Usage | > 80% | Scaling Trigger |
| CPU Usage | > 70% | Scaling Trigger |
| Request Error Rate | > 1% | Warning Alert |
| Database Connections | > 80% of Pool | Warning Alert |
| Disk Usage | > 85% | Warning Alert |
| Vespa Index Size | > 100GB | Monitoring |

### Dashboards

**Prometheus/Grafana Dashboards**:
- System Overview (CPU, Memory, Disk)
- API Performance (Latency, Throughput, Errors)
- Database Health (Connections, Replication, Backups)
- LLM Integration (Token Usage, Model Performance)
- User Activity (MAU, Daily Users, Feature Usage)

### Alerting Rules

```yaml
# Example Alert Rule (Prometheus)
groups:
  - name: vob-chatbot-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: PodRestartingTooOften
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: warning
```

---

## Backup und Recovery

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

### Backup-Strategie (3-2-1 Rule)

```
┌─────────────────────────────────────────────────────────────────┐
│ 3 Kopien der Daten                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Produktiv-Datenbank (Frankfurt RDS)                         │
│    └─ RTO: <1 Min (Failover zu Read Replica)                  │
│    └─ RPO: ~30 Sekunden (replication lag)                     │
│                                                                 │
│ 2. Automated Snapshots (StackIT S3)                            │
│    ├─ Tägliche Snapshots (30 days retention)                   │
│    ├─ Wöchentliche Snapshots (12 weeks retention)             │
│    └─ Monatliche Snapshots (1 Jahr retention)                 │
│    └─ RTO: ~2 Stunden (Restore aus Snapshot)                 │
│    └─ RPO: ~24 Stunden                                        │
│                                                                 │
│ 3. Offsite Backup (Cold Storage)                               │
│    ├─ Monatliche Backups zu StackIT Cold Storage              │
│    ├─ Archiviert für 7 Jahre (Compliance)                     │
│    └─ RTO: >24 Stunden (Restore-Prozess komplex)             │
│    └─ RPO: ~1 Monat                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### RTO/RPO Targets

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

| Szenario | RTO (Recovery Time) | RPO (Data Loss) |
|----------|-----------------|--------|
| Einzelner Pod Fehler | 1-2 Min | 0 (stateless) |
| Datenbank-Failover | <1 Min | ~30 Sec |
| Region-Ausfall | TBD | TBD |
| Kompletter Datenverlust | 2-4 Stunden | 24 Stunden |

### Disaster Recovery Prozess

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

1. **Detection**: Automated Alerting erkennt Ausfall
2. **Incident Response**: On-Call Team wird aufgefordert
3. **Assessment**: Bestandsaufnahme des Schadens
4. **Recovery Plan**: Entscheidung über Recovery-Strategie
5. **Execution**: Restore aus Backup durchführen
6. **Validation**: Daten-Integrität prüfen
7. **Notification**: VÖB informieren über Status
8. **Post-Incident**: Root Cause Analysis

---

## Update-Prozess

### Upstream Merges (Onyx Updates)

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

**Frequenz**: Jeden Quarter oder bei kritischen Security Updates

**Prozess**:

```
1. Fetch Upstream
   git fetch upstream main

2. Create Branch
   git checkout -b feature/upstream-merge-v2.1.0

3. Merge
   git merge upstream/main

4. Resolve Conflicts
   - Nur in Core-Files möglich (7 Files)
   - Extensions sollten keine Konflikte haben

5. Test in Staging
   - Run Full Test Suite
   - Deploy to Staging Environment
   - Smoke Tests

6. Deploy to Production
   - Scheduled Maintenance Window
   - Rolling Update (3 Replicas staggered)
   - Monitor für Issues

7. Merge PR
   git merge --squash feature/upstream-merge-v2.1.0
```

### Extension Updates

**Häufigkeit**: Bei neuen Features, Bug Fixes, Security Patches

**Prozess**: Standard Git Workflow
1. Feature Branch
2. PR mit Tests
3. Code Review + Approval
4. CI/CD Testing
5. Deploy to Staging
6. Deploy to Production (if approved)

### Database Migrations

**Strategie**: Zero-Downtime Migrations

1. **Backward Compatible**: New Schema muss mit alte App-Version funktionieren
2. **Deploy Application**: Update App-Version zuerst
3. **Run Migrations**: Dann DB-Migrations durchführen
4. **Verify**: Schema ist konsistent

**Rollback**: Reverse Migrations vorbereitet

---

## Skalierung

### Horizontal Scaling (mehr Pods)

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

```yaml
# HorizontalPodAutoscaler for Frontend
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chatbot-frontend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chatbot-frontend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Triggerbedingungen**:
- CPU > 70%: Scale up (max +2 Pods per minute)
- Memory > 80%: Scale up
- Traffic > 1000 req/sec: Scale up

**Limits**:
- Frontend: Min 3, Max 10 Pods
- Backend: Min 3, Max 15 Pods
- Vespa: Min 3, Max 7 Nodes (fixed, nur vertical scaling)

### Vertical Scaling (größere Instanzen)

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

**Wenn Horizontal-Scaling nicht ausreicht**:
- PostgreSQL: Upgrade Node Size (db.standard.2 → db.standard.4)
- Vespa: Mehr Memory pro Node (wenn HPA maxed out)
- Kubernetes Nodes: Größere Instance Types

**RTO**: ~30 Min (Rolling Update mit Blue-Green Deployment)

---

## Wartungsfenster

### Geplante Wartungen

| Zeitfenster | Frequenz | Dauer | Aktivitäten |
|---|---|---|---|
| Mittwoch 02:00-04:00 CEST | Wöchentlich | 2 Stunden | Patch Management, Security Updates |
| Zweiter Samstag, 22:00-06:00 | Monatlich | 8 Stunden | Major Updates, Kernel Patches |

**Benachrichtigungen**:
- 2 Wochen vorher: Ankündigung an Stakeholder
- 1 Tag vorher: Reminder
- 30 Min vorher: Kurz vor Wartung-Start

**User Communication**:
- Statusseite: chatbot-status.vob.example.com
- Email an Admins
- In-App Banner (wenn möglich)

---

## Incident Management

### Severity Levels

| Level | Auswirkung | Response Time | Resolution Target |
|-------|-----------|---|---|
| P1 (Critical) | Produktionssystem down | 15 Minuten | 2 Stunden |
| P2 (High) | Funktionalität beeinträchtigt | 1 Stunde | 4 Stunden |
| P3 (Medium) | Gering Impact, Workaround existiert | 4 Stunden | 1 Tag |
| P4 (Low) | Cosmetic issue, kein Impact | 24 Stunden | 1 Woche |

### Eskalationspfade

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

```
Incident Detection
  ↓
Automated Alert (Slack/Email)
  ↓
On-Call Engineer Page
  ↓
5 Min keine Response?
  ├─→ Escalate to Team Lead
  │   5 Min keine Response?
  │   └─→ Escalate to Manager
  │       5 Min keine Response?
  │       └─→ Escalate to Director + VÖB Notify
  └─→ Parallel: Incident Commander + War Room (Slack)
```

### Incident Log Template

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

```markdown
# Incident: [Title]

## Timeline
- **2024-01-15 14:30 UTC**: Alert fired (API Error Rate > 5%)
- **2024-01-15 14:35 UTC**: On-Call Engineer acknowledged
- **2024-01-15 14:45 UTC**: Root Cause Identified (Memory Leak in Frontend)
- **2024-01-15 14:55 UTC**: Rollback deployed
- **2024-01-15 15:00 UTC**: Service recovered, P1 resolved

## Root Cause
[Analysis]

## Mitigation
[What was done]

## Prevention
[What will prevent recurrence]

## Post-Mortem
[Scheduled for 24 hours later]
```

---

## SLA-Definitionen

[ENTWURF — Abhängig von Vereinbarung mit VÖB – TBD]

### Vorgeschlagene SLAs

| Metrik | Zielwert | Bemerkung |
|--------|---------|----------|
| **Verfügbarkeit** | 99.9% (43 Min Downtime/Monat) | Außer geplante Wartung |
| **API Response Time (p99)** | < 500ms | 99% aller Requests |
| **API Success Rate** | > 99.5% | Weniger als 0.5% Fehler |
| **Data Loss** | RPO 24 Stunden | Mit Backups Recovery möglich |
| **Incident Response** | P1: 15 Min, P2: 1 Hr | Vom Alert bis On-Call |
| **Patch Management** | 30 Tage für Non-Critical | 24 Stunden für Critical |

### Ausnahmen von SLA

- Geplante Wartungsfenster
- DDoS Attacken (außerhalb normaler Lasten)
- Externe Dependencies (LLM Provider, Entra ID)
- Major Version Upgrades

---

## Kontaktliste

[ENTWURF — Zu ergänzen mit echten Kontakten]

| Rolle | Name | Email | Phone | Notizen |
|-------|------|-------|-------|---------|
| **Projektleiter (CCJ)** | [TBD] | [TBD] | [TBD] | Geschäftszeiten |
| **Tech Lead (JNnovate)** | [TBD] | [TBD] | [TBD] | 24/7 on-call |
| **DevOps Lead** | [TBD] | [TBD] | [TBD] | 24/7 on-call |
| **StackIT Support** | [Contact] | [TBD] | [TBD] | Offizielle Eskalation |
| **VÖB Operations Lead** | [TBD] | [TBD] | [TBD] | Für Notifications |
| **VÖB CISO** | [TBD] | [TBD] | [TBD] | Für Security Incidents |

---

## Dokumentation & Runbooks

Runbooks werden in `docs/runbooks/` gepflegt. Jedes Runbook ist ein eigenständiges, verifiziertes Step-by-Step-Dokument.

**Siehe [Runbook-Index](./runbooks/README.md) für die vollständige Übersicht.**

### Vorhandene Runbooks

| Runbook | Status |
|---------|--------|
| [StackIT Projekt-Setup](./runbooks/stackit-projekt-setup.md) | Verifiziert |
| StackIT Terraform Deploy | Ausstehend |
| K8s Namespace Setup | Ausstehend |
| Helm Deploy | Ausstehend |
| CI/CD Pipeline | Ausstehend |
| Troubleshooting | Ausstehend |

### Geplante Runbooks (nach Go-Live)

1. **Incident Response Runbooks**
   - P1 Incident Response
   - Database Corruption Recovery
   - Data Breach Response

2. **Maintenance Runbook**
   - Patch Management Prozess
   - Database Maintenance (Vacuuming, Reindexing)
   - Log Archival

3. **Scaling Runbook**
   - Wann zu skalieren ist
   - Wie HPA manuell zu justieren ist
   - Kapazitätsplanung

---

**Dokumentstatus**: Entwurf
**Letzte Aktualisierung**: [Datum TBD]
**Version**: 0.1
