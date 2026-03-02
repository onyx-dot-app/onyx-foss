# ADR-003: StackIT als Cloud Provider

**Status**: Akzeptiert
**Aktualisiert**: [Datum TBD]
**Author**: Infrastruktur-Team (StackIT + JNnovate)

---

## Context

Basierend auf **ADR-001** und **ADR-002** benötigen wir einen Cloud Provider für die Infrastruktur des VÖB Service Chatbot.

### Anforderungen aus Banking-Sektor

1. **Datenhoheit & Datensouveränität**
   - Daten müssen in Deutschland/EU bleiben (DSGVO)
   - Keine US-basierte Cloud (Privacy Shield / Standard Contractual Clauses kritisch)
   - Audit Trail auf deutschen Servern

2. **Compliance & Regulierung**
   - BAIT (Banking Information Security Guidance) und Banking-Standards
   - BSI C5 (Cloud Computing Compliance Control Catalogue)
   - BaFin-Anforderungen für FinTech-Lösungen
   - Möglicherweise ISO 27001 oder ähnliche Zertifizierung

3. **Datenschutz**
   - DSGVO-konform (Artikel 32 – technische/organisatorische Maßnahmen)
   - Datenverarbeitungsverträge (DPA) möglich
   - Transparenz über Datenverarbeitung

4. **Performance & Zuverlässigkeit**
   - Gute Performance für deutsche/europäische Nutzer
   - Hohe Verfügbarkeit (99.9%+ SLA)
   - Schnelle Incident Response

5. **Technische Anforderungen**
   - Kubernetes-Support
   - PostgreSQL Managed Service
   - Object Storage (S3-compatible)
   - Networking & Security Controls

### Cloud Provider Markt in Deutschland/EU

**Große Provider**:
- AWS (US-basiert, aber hat EU-Region Frankfurt)
- Microsoft Azure (US-basiert, aber hat EU-Regionen)
- Google Cloud (US-basiert, aber hat EU-Regionen)

**Deutsche/EU Provider**:
- **StackIT** (Deutsche Telekom, 100% German Cloud)
- Hetzner (Deutsche Server, aber weniger Enterprise-Features)
- OVH (Französisch)
- Ionos (Deutsch)

---

## Decision

**Wir wählen StackIT als Cloud Provider für den VÖB Service Chatbot.**

### StackIT – Überblick

**Unternehmen**: StackIT GmbH (Tochter der Deutschen Telekom)
**Sitz**: Deutschland
**Rechenzentren**: Deutschland (Frankfurt, München, Berlin geplant)
**Service**: Managed Kubernetes, DBaaS, Object Storage, etc.

### Infrastruktur-Architektur auf StackIT

```
┌──────────────────────────────────────────────────────────────────┐
│ StackIT Cloud – Frankfurt Rechenzentrum                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Kubernetes Cluster (managed by StackIT)                   │ │
│  │                                                            │ │
│  │  Namespace: vob-chatbot-prod                              │ │
│  │  ├── Pods: chatbot-frontend (replicas: 3)                │ │
│  │  ├── Pods: chatbot-backend (replicas: 3)                 │ │
│  │  ├── Pods: vespa-cluster (nodes: 3)                      │ │
│  │  ├── Services: LoadBalancer, Internal                     │ │
│  │  ├── Ingress: TLS, SSL Termination                        │ │
│  │  └── Network Policies: Egress/Ingress Rules              │ │
│  │                                                            │ │
│  │  Namespace: vob-chatbot-staging                           │ │
│  │  └── [identisch zu prod, für Testing]                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Managed Services                                           │ │
│  │                                                            │ │
│  │  PostgreSQL RDS (managed)                                 │ │
│  │  ├── vob-chatbot-prod (instance: db.standard.2)          │ │
│  │  ├── vob-chatbot-staging (instance: db.standard.1)       │ │
│  │  ├── Automated Backups (daily, 30 days retention)        │ │
│  │  └── SSL/TLS Encrypted Connections                       │ │
│  │                                                            │ │
│  │  S3-compatible Object Storage (for backups, assets)      │ │
│  │  ├── Bucket: vob-chatbot-backups                          │ │
│  │  ├── Bucket: vob-chatbot-assets                           │ │
│  │  ├── Lifecycle Policies (archive old data)                │ │
│  │  └── Encryption at rest (AES-256)                         │ │
│  │                                                            │ │
│  │  Observability & Monitoring                               │ │
│  │  ├── Prometheus (metrics)                                 │ │
│  │  ├── ELK Stack or similar (logs)                          │ │
│  │  └── Alerting (PagerDuty integration)                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Network & Security                                         │ │
│  │                                                            │ │
│  │  VPC / Private Network                                    │ │
│  │  ├── Kubernetes Nodes in Private Subnet                   │ │
│  │  ├── RDS in Private Subnet                                │ │
│  │  └── Bastion Host for SSH Access                          │ │
│  │                                                            │
│  │  WAF / DDoS Protection (StackIT-provided)                │ │
│  │  TLS/SSL Certificates (Let's Encrypt or CA)              │ │
│  │  API Gateway (optional, for rate limiting)                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

        ↓ Internet/VPN

┌──────────────────────────────────────────────────────────────────┐
│ Endbenutzer / VÖB-Mitglieder                                     │
│ (Browser: chatbot.vob.example.com)                               │
└──────────────────────────────────────────────────────────────────┘
```

### Warum StackIT?

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

---

## Rationale

### Große Vorteile von StackIT

#### 1. Datenhoheit & Datensouveränität ⭐

- **Rechenzentren**: 100% in Deutschland
  - Frankfurt (primary)
  - München, Berlin (geplant)
- **Kein Datenabfluss**: Keine US-basierte Infrastruktur
- **DSGVO-konform**: Vollständig, ohne Legal Workarounds
- **Vertrauen**: Deutsche Telekom als Mutterkonzern → Vertrauen in Banking-Sektor

#### 2. Compliance & Regulierung ⭐

- **BSI C5**: Cloud Computing Compliance zertifiziert
- **ISO 27001**: Informationssicherheit zertifiziert
- **BAIT-relevant**: Erfüllt Banking-Anforderungen
- **Banking-Fokus**: Viele Fintech-Kunden (Verständnis der Anforderungen)

#### 3. Technische Qualität

- **Kubernetes**: Managed K8s, zuverlässig und skalierbar
- **Databases**: PostgreSQL managed service mit Backups, HA
- **Storage**: S3-compatible Object Storage
- **Networking**: VPC, Private Subnets, Security Groups
- **Observability**: Prometheus, ELK Stack (oder ähnlich)

#### 4. Kosten

- **Transparentes Pricing**: Keine versteckten Gebühren
- **Competitive**: Mit AWS/Azure auf Pro-Modul-Basis vergleichbar
- **Frühe Kundin**: VÖB ist potentielle Referenz (möglicherweise Rabatt verhandelt)

#### 5. Support

- **Deutsch Support**: Sprache, Zeitzone, Kultur
- **Schnelle Response**: Nicht über ticketing system in US
- **Local Expertise**: Kennt Banking-Sektor in Deutschland

### Überwindung von Nachteilen

**Herausforderung 1**: Kleinerer als AWS/Azure
- **Mitigation**: Für dieses Projekt ausreichend (nicht Google-Scale)
- **Impact**: Minimales Risiko, StackIT hat stabile Plattform

**Herausforderung 2**: Weniger Drittanbieter-Integrationen
- **Mitigation**: Core Services (K8s, DB, Storage) sind verfügbar
- **Impact**: Keine Show-Stopper für dieses Projekt

**Herausforderung 3**: Eventueller Vendor Lock-In bei StackIT
- **Mitigation**: Kubernetes ist Standard, Container-basiert → portabel
- **Impact**: Können später (wenn nötig) zu anderem Provider migrieren

---

## Alternatives Considered

### Alternative 1: AWS (Frankfurt Region)

**Ansatz**: AWS mit EU-Region Frankfurt

**Vorteile**:
- Größte Cloud-Anbieterin
- Unendlich viele Services und Integrationen
- Massive Community & Support
- Höchste Zuverlässigkeit

**Nachteile für Banking-Sektor**:
- **Datenhoheit**: Daten ist immer noch US-Unternehmen (selbst mit Frankfurt)
  - AWS = US Company, unterliegt US-Gesetzen
  - US CLOUD Act könnte Zugriff ermöglichen
  - DSGVO-Bedenken für Banken
- **Compliance**: Zwar EU-Anforderungen erfüllbar, aber mit Umwegen
- **Kosten**: Teurer als StackIT (für deutsche Workloads)
- **Psychology**: Deutsche Banken zögern bei US-Cloud (auch wenn legal möglich)

**Entscheidung**: Abgelehnt wegen Banking-Sektor Bedenken und Datensouveränität

---

### Alternative 2: Microsoft Azure (Amsterdam/Frankfurt)

**Ansatz**: Azure mit EU-Regionen

**Vorteile**:
- Große, etablierte Cloud-Plattform
- Gutes Kubernetes-Support (AKS)
- Microsoft-Integration (Entra ID – relevant für uns!)

**Nachteile**:
- **Datenhoheit**: Microsoft = US Company, ähnliche Bedenken wie AWS
  - US Patriot Act, Cloud Act
  - DSGVO-Diskussionen für EU-Regulatoren
- **Compliance**: Besser als AWS, aber immer noch Fragen
- **Kosten**: Ähnlich wie AWS, teuer
- **Banking-Psychologie**: Zögern bei US-Cloud (auch wenn Entra ID relevant ist)

**Entscheidung**: Abgelehnt wegen Datenhoheit, trotz Entra ID Synergien

---

### Alternative 3: Hetzner (deutsche Server)

**Ansatz**: Hetzner als IaaS Provider für VMs

**Vorteile**:
- Deutsche Server, gutes Vertrauen
- Preiswert
- Flexibel

**Nachteile**:
- **Kein Kubernetes**: Nur VMs, müssten selbst Kubernetes deployen
  - Große Operational Burden (Node Management, Updates, Security Patches)
- **Weniger Managed Services**: Keine managed PostgreSQL, Object Storage
  - Müssen selbst betreiben (mehr Ops-Aufwand)
- **Skalierbarkeit**: Nicht für große Nutzerbasen ausgelegt
- **Enterprise-Features**: WAF, DDoS-Protection nicht vorhanden

**Entscheidung**: Abgelehnt wegen fehlender Enterprise-Features und Managed Services

---

### Alternative 4: On-Premise / Private Cloud

**Ansatz**: Eigene Infrastruktur bei VÖB oder Partner

**Vorteile**:
- **Volle Kontrolle**: 100% deine Infrastruktur
- **Datenhoheit**: Maximale Kontrolle

**Nachteile**:
- **Capex-Kosten**: Massive Hardware-Investition
- **Opex**: Team zur Verwaltung (Kubernetes, Backups, Security)
- **Skalierbarkeit**: Schwer zu skalieren (Hardware-Procurement lange)
- **Disaster Recovery**: Eigene DR-Strategy implementieren
- **Expertise**: VÖB hat wahrscheinlich kein Kubernetes-Team

**Entscheidung**: Abgelehnt wegen Kosten, Komplexität und Zeitmangel

---

## Consequences

### Positive Auswirkungen

1. **Datenhoheit**: 100% in Deutschland, DSGVO-konform ✅
2. **Compliance**: Banking-Standards einfach erfüllt ✅
3. **Schnellerer Go-Live**: Managed Services, nicht viel Ops-Setup ✅
4. **Deutsche Support**: Sprache, Timezone, Kultur ✅
5. **Transparente Kosten**: Klare Pricing, keine versteckten Gebühren ✅

### Negative Auswirkungen / Mitigation

1. **Größere Cloud als AWS/Azure**
   - Mitigation: Für dieses Projekt großer als nötig, Redundanz ist gut
   - Impact: Minimal

2. **Weniger Third-Party Integrationen**
   - Mitigation: Wir brauchen keine exotischen Services (Standard K8s, DB, Storage)
   - Impact: Keine Show-Stopper

3. **Potentieller Vendor Lock-In**
   - Mitigation: Kubernetes ist portabel, Container-Standard
   - Impact: Können später migrieren, wenn nötig

---

## Implementation Notes

### StackIT Account Setup

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

1. **Phase 1**: StackIT Account erstellen, Billing-Setup
2. **Phase 2**: Kubernetes Cluster bereitstellen (Frankfurt)
3. **Phase 3**: PostgreSQL RDS instanzieren, Object Storage buckets
4. **Phase 4**: Networking (VPC, Security Groups), TLS Certificates
5. **Phase 5**: Monitoring & Observability Stack (Prometheus, ELK)
6. **Phase 6**: CI/CD Pipeline Integration (GitHub Actions → StackIT)

### Kostenschätzung

[ENTWURF — Details nach StackIT Angebot ergänzen]

Beispielhafte monatliche Kosten (für Referenz):
- **Kubernetes Cluster** (3 nodes, 4 CPU, 8 GB RAM): €300-500
- **PostgreSQL RDS** (db.standard.2, HA): €200-300
- **Vespa Cluster** (3 nodes, Search): €400-600
- **Object Storage**: €50-100 (backups)
- **Network/Data Transfer**: €100-200
- **Monitoring/Observability**: €50-100
- **Support** (optional): €100-200

**Geschätzt gesamt**: €1,200 - €2,000 / Monat (Production)

**Staging**: ~50% des Production-Costs

### Sicherheits-Konfiguration

[ENTWURF — Details nach Infrastruktur-Setup ergänzen]

1. **Network Policies**: Kubernetes Network Policies für Pod-Segmentierung
2. **TLS/SSL**: Certificates für alle APIs (Let's Encrypt or CA)
3. **Secrets Management**: HashiCorp Vault oder Kubernetes Secrets
4. **IAM**: StackIT IAM für Benutzer-Zugriff (Bastion, K8s API)
5. **Audit Logging**: Alle AWS/StackIT API-Calls geloggt
6. **DDoS Protection**: StackIT-bereitgestellter WAF/DDoS-Schutz
7. **Backup-Encryption**: S3 Object Storage mit Encryption at rest

---

## Related ADRs

- **ADR-001**: Onyx FOSS als Basis
  - Was auf StackIT deployed wird
- **ADR-002**: Extension-Architektur
  - Wie Extensions auf StackIT skaliert werden

---

## Approval & Sign-off

| Rolle | Name | Datum | Signatur |
|-------|------|-------|----------|
| Infrastructure Lead (StackIT/JNnovate) | [TBD] | [TBD] | __ |
| Cloud Architect | [TBD] | [TBD] | __ |
| Projektleiter (CCJ) | [TBD] | [TBD] | __ |
| Auftraggeber (VÖB) | [TBD] | [TBD] | __ |
| Compliance Officer | [TBD] | [TBD] | __ |

---

**ADR Status**: Akzeptiert
**Letzte Aktualisierung**: [Datum TBD]
**Version**: 1.0
