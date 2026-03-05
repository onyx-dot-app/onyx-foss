# ADR-004: Umgebungstrennung DEV / TEST / PROD

**Status**: Akzeptiert
**Aktualisiert**: 2026-03-03
**Author**: CCJ / Coffee Studios (Nikolaj Ivanov)

---

## Context

### Ausgangslage

Mit der erfolgreichen Inbetriebnahme der DEV-Umgebung (Phase 2, 2026-02-27) und der produktionsreifen CI/CD-Pipeline (Run #5, 2026-03-02) steht der nächste Schritt an: **Eine TEST-Umgebung für den Kunden (VÖB) bereitstellen**, damit dieser die Lösung eigenständig evaluieren kann.

### Anforderungen

1. **Umgebungsisolation** — DEV-Aktivitäten (Entwicklung, Debugging, Load-Tests) dürfen TEST nicht beeinflussen
2. **Unabhängige Datenhaltung** — Jede Umgebung braucht eigene Datenbank und Storage (unabhängig resettbar)
3. **Kosteneffizienz** — VÖB erwartet keine Produktionskosten für Vorproduktionsumgebungen
4. **BAIT/BSI-Konformität** — Nachvollziehbare Umgebungstrennung für Audit-Zwecke
5. **Deployment-Pipeline** — Kontrollierte Promotion von Code über Stages hinweg
6. **PROD-Vorbereitung** — Die Architektur muss auf eine spätere PROD-Umgebung skalieren

### Bestehendes Setup (DEV)

- 1× SKE-Cluster `vob-chatbot` (Node Pool `devtest`, 1× g1a.4d: 4 vCPU, 16 GB RAM)
- 1× PostgreSQL Flex `vob-dev` (2 CPU, 4 GB RAM, Single)
- 1× Object Storage Bucket `vob-dev`
- Namespace `onyx-dev` mit 10 Pods (~1850m CPU Requests, ~5.2 Gi RAM Requests)
- CI/CD: `deploy-dev` (automatisch), `deploy-test` und `deploy-prod` (manuell) vorbereitet

### Ursprünglicher Plan vs. Realität

`stackit-infrastruktur.md` plante DEV+TEST auf **einem geteilten Node**. Die CPU-Analyse zeigt jedoch, dass ein g1a.4d (~3700m allocatable CPU) für zwei Onyx-Instanzen (~3700m Requests zusammen) bei 100% Auslastung wäre. Unter Last wird CPU-Throttling unvermeidbar — für eine Kundenumgebung nicht akzeptabel.

---

## Decision

### Compute: Gleicher Cluster, eigene Nodes pro Umgebung

```
┌─────────────────────────────────────────────────────────┐
│ SKE Cluster "vob-chatbot" (shared, Frankfurt EU01)      │
│                                                         │
│  Node Pool "devtest" (2× g1a.4d)                        │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │ Node 1              │  │ Node 2                  │  │
│  │ Namespace: onyx-dev │  │ Namespace: onyx-test    │  │
│  │ 10 Pods             │  │ 9 Pods                  │  │
│  │ ~1850m CPU Req.     │  │ ~1850m CPU Req.         │  │
│  │ ~5.2 Gi RAM Req.    │  │ ~5.2 Gi RAM Req.        │  │
│  └─────────────────────┘  └─────────────────────────┘  │
│                                                         │
│  (Später: separater PROD-Cluster)                       │
└─────────────────────────────────────────────────────────┘
```

- Node Pool `devtest`: `min_count: 2`, `max_count: 2` (von aktuell min=1, max=1)
- Kubernetes-Scheduler verteilt Pods via Namespace auf die Nodes
- Kein Dedicated-Node-Affinity nötig — der Scheduler balanciert automatisch

### Daten: Eigene PG-Instanz + Bucket pro Umgebung

```
┌──────────────────────────────────────────────────────┐
│ Managed Services (StackIT, Frankfurt EU01)           │
│                                                      │
│  PostgreSQL Flex                Object Storage       │
│  ┌────────────────────┐        ┌─────────────┐      │
│  │ vob-dev            │        │ vob-dev     │      │
│  │ Flex 2.4 Single    │        └─────────────┘      │
│  │ 2 CPU, 4 GB        │                              │
│  └────────────────────┘        ┌─────────────┐      │
│  ┌────────────────────┐        │ vob-test    │      │
│  │ vob-test (NEU)     │        └─────────────┘      │
│  │ Flex 2.4 Single    │                              │
│  │ 2 CPU, 4 GB        │                              │
│  └────────────────────┘                              │
└──────────────────────────────────────────────────────┘
```

### Deployment-Pipeline: Kontrollierte Promotion

```
main Branch ──push──→ DEV (automatisch)
                           │
                    workflow_dispatch
                           │
                           ▼
                         TEST (manuell, --atomic)
                           │
                    workflow_dispatch + GitHub Environment Approval
                           │
                           ▼
                         PROD (manuell, --atomic, Review erforderlich)
```

### PROD: Eigener Cluster (spätere Phase)

PROD wird in einem **separaten SKE-Cluster** betrieben:
- Eigener Node Pool (2-3× g1a.4d)
- Eigene PG Flex 4.8 Replica (3-Node HA)
- Eigene Network Policies mit Egress-Rules
- Begründung: Blast-Radius-Minimierung, eigenes Maintenance-Window, strengere Security

---

## Rationale

### Warum gleicher Cluster für DEV+TEST?

1. **Kosteneffizienz** — Kein zweiter Cluster-Overhead (Management, Monitoring, Kubeconfig)
2. **Einfache Verwaltung** — Eine Kubeconfig, ein `helm upgrade` pro Environment
3. **Ausreichende Isolation** — Namespace-Trennung + eigene Nodes = keine Ressourcen-Konkurrenz
4. **Vorproduktionsumgebungen** — DEV und TEST sind interne/Evaluierungsumgebungen, keine Kundendaten in Produktion

### Warum 2 Nodes statt größerer Node?

1. **Hardware-Isolation** — Node-Ausfall betrifft nur eine Umgebung, nicht beide
2. **Vorhersagbare Performance** — Keine CPU-Konkurrenz zwischen Umgebungen
3. **Skalierungsmuster** — "Eine Umgebung = eigene Nodes" ist das Pattern, das wir auch für PROD verwenden
4. **Kostenäquivalenz** — 2× g1a.4d ≈ 1× g1a.8d (gleiche Gesamtkapazität, ~500 EUR/Monat)

### Warum eigene PG-Instanz statt zweite DB auf gleicher Instanz?

1. **Isolation** — DEV-Datenmüll (Testdaten, fehlerhafte Migrationen) beeinflusst TEST nicht
2. **Unabhängig resettbar** — TEST-DB löschen ohne DEV-Impact
3. **Eigene Credentials** — Saubere Secrets-Trennung pro GitHub Environment
4. **Eigenes Backup** — Restore möglich ohne die andere Umgebung zu beeinflussen
5. **Banking-Standard** — Bei BAIT-Audit nachweisbare Datentrennung

### Warum PROD in eigenem Cluster?

1. **Blast Radius** — DEV/TEST-Fehler (kaputte Network Policy, versehentliches `kubectl delete ns`) dürfen PROD nie beeinflussen
2. **Maintenance Window** — PROD-K8s-Upgrades unabhängig von DEV/TEST planbar
3. **Security** — Strengere RBAC, Network Policies, Audit Logging nur für PROD
4. **Compliance** — BAIT fordert nachweisbare Trennung von Produktiv- und Testumgebungen
5. **Kubeconfig-Trennung** — Verschiedene Credentials, verschiedene Zugriffsrechte

---

## Alternatives Considered

### Alternative 1: Beide Umgebungen auf einem Node (g1a.4d)

**Ansatz**: DEV + TEST im gleichen Namespace-isolierten Node (wie ursprünglich geplant)

**Vorteile**:
- Geringste Kosten (~250 EUR/Monat statt ~500 EUR)
- Einfachstes Setup

**Nachteile**:
- CPU-Requests: ~3700m von ~3700m allocatable = **100% Auslastung bei Requests allein**
- Unter Last: CPU-Throttling in beiden Umgebungen
- Kunde (VÖB) würde Performanceprobleme bemerken, wenn DEV unter Last steht
- Node-Ausfall = **beide Umgebungen gleichzeitig down**

**Entscheidung**: Abgelehnt wegen unzureichender Kapazität und mangelnder Isolation

### Alternative 2: Upgrade auf g1a.8d (ein größerer Node)

**Ansatz**: Statt 2× g1a.4d ein einzelner g1a.8d (8 vCPU, 32 GB RAM)

**Vorteile**:
- ~50-100 EUR/Monat günstiger als 2× g1a.4d
- Einfacheres Node-Management

**Nachteile**:
- **Keine Hardware-Isolation** — Node-Ausfall = beide Umgebungen down
- CPU-Konkurrenz zwischen DEV und TEST (Burst-Szenarien)
- Kein Skalierungspfad — bei PROD müsste man Pattern wechseln

**Entscheidung**: Abgelehnt wegen fehlender Ausfallsicherheit und Isolation

### Alternative 3: Separater Cluster für TEST

**Ansatz**: Eigener SKE-Cluster für TEST (wie für PROD geplant)

**Vorteile**:
- Maximale Isolation
- Eigenes Maintenance-Window

**Nachteile**:
- **Overkill** für eine Vorproduktions-Testumgebung
- Doppelter Management-Overhead (zweite Kubeconfig, zweites Monitoring)
- ~100 EUR/Monat extra Cluster-Overhead ohne Mehrwert
- Gleiche Isolation bereits durch Node-Trennung erreichbar

**Entscheidung**: Abgelehnt wegen unnötigem Overhead für Vorproduktionsumgebung

### Alternative 4: Gemeinsame PG-Instanz mit separater Datenbank

**Ansatz**: Auf der bestehenden PG-Instanz `vob-dev` eine zweite DB `onyx_test` anlegen

**Vorteile**:
- ~30-50 EUR/Monat Ersparnis
- Weniger Terraform-Ressourcen

**Nachteile**:
- Ressourcen-Konkurrenz (CPU/RAM der PG-Instanz geteilt)
- Kein unabhängiges Backup/Restore
- DEV-Fehler (z.B. fehlerhafte Migration) könnte gesamte Instanz beeinflussen
- Bei Banking-Audit schwerer zu argumentieren als physisch getrennte Instanzen

**Entscheidung**: Abgelehnt wegen unzureichender Datentrennung für Banking-Kontext

---

## Consequences

### Positive Auswirkungen

1. **Kunden-Testbarkeit** — VÖB kann unabhängig von DEV-Aktivitäten evaluieren
2. **Performance-Isolation** — Keine CPU/RAM-Konkurrenz zwischen Umgebungen
3. **Ausfallsicherheit** — Node-Ausfall betrifft nur eine Umgebung
4. **Saubere Datentrennung** — Eigene PG + Bucket = unabhängig resettbar
5. **Audit-konform** — Nachweisbare Umgebungstrennung (BAIT/BSI)
6. **PROD-ready Pattern** — Skaliert natürlich zu eigenem PROD-Cluster

### Negative Auswirkungen / Mitigation

1. **Höhere Kosten (~+300 EUR/Monat für TEST)**
   - Mitigation: Notwendig für Enterprise-Qualität; ~550 EUR/Monat gesamt (DEV+TEST) immer noch kosteneffizient
   - Impact: Akzeptabel im Projektbudget

2. **Mehr Terraform-Ressourcen zu verwalten**
   - Mitigation: Gleiche Module wiederverwendet, nur neue `environments/test/main.tf`
   - Impact: Minimal, ~30 Minuten zusätzlicher Setup

3. **Zwei Nodes statt einem = mehr Patching-Surface**
   - Mitigation: SKE Maintenance-Window handled Auto-Updates (02:00–04:00 UTC)
   - Impact: Kein manueller Aufwand

---

## Implementation Notes

### Schritt 1: Terraform (Node Pool + TEST-Ressourcen)

```bash
# Node Pool auf 2 Nodes skalieren
# deployment/terraform/environments/dev/main.tf
node_pool.minimum = 2
node_pool.maximum = 2

# Neue TEST-Ressourcen
# deployment/terraform/environments/test/main.tf
# → Eigene PG Flex Instanz (vob-test, Flex 2.4 Single)
# → Eigener Object Storage Bucket (vob-test)
```

### Schritt 2: Helm Values

```bash
# Neues File: deployment/helm/values/values-test.yaml
# → Eigene PG-Credentials (aus Terraform Output)
# → Eigener Bucket (vob-test)
# → Namespace: onyx-test
# → AUTH_TYPE: basic (bis Entra ID verfügbar)
# → WEB_DOMAIN: http://<LoadBalancer-IP> (bis DNS verfügbar)
```

### Schritt 3: GitHub Secrets

```
Environment: test
Secrets: POSTGRES_PASSWORD, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY,
         DB_READONLY_PASSWORD, REDIS_PASSWORD
```

### Schritt 4: Deploy + Validierung

```bash
# Manueller workflow_dispatch auf main → Environment: test
# Validierung: kubectl get pods -n onyx-test, /api/health
```

### Kosten-Übersicht (nach Implementation)

| Ressource | DEV | TEST | Gesamt |
|-----------|-----|------|--------|
| Node Pool (2× g1a.4d) | ~125 EUR | ~125 EUR | ~250 EUR |
| PostgreSQL Flex 2.4 | ~50 EUR | ~50 EUR | ~100 EUR |
| Object Storage | ~5 EUR | ~5 EUR | ~10 EUR |
| Load Balancer (shared) | — | — | ~50 EUR |
| **Gesamt** | **~180 EUR** | **~180 EUR** | **~410 EUR** |

> Hinweis: Node Pool wird als Einheit abgerechnet. Die Aufteilung DEV/TEST ist logisch, nicht kaufmännisch.

---

## Related ADRs

- **ADR-001**: Onyx FOSS als Basis — Was deployed wird
- **ADR-002**: Extension-Architektur — Wie Extensions über Environments migriert werden
- **ADR-003**: StackIT als Cloud Provider — Warum diese Infrastruktur

---

## Approval & Sign-off

| Rolle | Name | Datum | Signatur |
|-------|------|-------|----------|
| Tech Lead (CCJ) | Nikolaj Ivanov | 2026-03-02 | __ |
| Auftraggeber (VÖB) | [TBD] | [TBD] | __ |

---

**ADR Status**: Akzeptiert
**Letzte Aktualisierung**: 2026-03-03
**Version**: 1.0
