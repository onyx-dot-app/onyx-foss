# ADR-003: StackIT als Cloud Provider

**Status**: Akzeptiert
**Aktualisiert**: 2026-03-04
**Author**: CCJ / Coffee Studios

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
- **StackIT** (Schwarz Digits / Schwarz-Gruppe, 100% German Cloud)
- Hetzner (Deutsche Server, aber weniger Enterprise-Features)
- OVH (Französisch)
- Ionos (Deutsch)

---

## Decision

**Wir wählen StackIT als Cloud Provider für den VÖB Service Chatbot.**

### StackIT – Überblick

**Unternehmen**: StackIT GmbH & Co. KG (Tochter der Schwarz Digits / Schwarz-Gruppe)
**Sitz**: Neckarsulm, Deutschland
**Rechenzentren**: Frankfurt DC10 (primär), München (via LEW TelNet), Ellhofen DC08 (seit 2017), Österreich (operativ), Berlin (geplant), Lübbenau (im Bau)
**Service**: Managed Kubernetes (SKE), PostgreSQL Flex, Object Storage, AI Model Serving, etc.

### Infrastruktur-Architektur auf StackIT

```
┌──────────────────────────────────────────────────────────────────┐
│ StackIT Cloud – Frankfurt Rechenzentrum                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Kubernetes Cluster (managed by StackIT)                   │ │
│  │                                                            │ │
│  │  Namespace: onyx-dev                                      │ │
│  │  ├── Pods: 10 (backend, web-server, background,         │ │
│  │  │         model-server x2, vespa, nginx-ingress,        │ │
│  │  │         redis-master, redis-replicas)                  │ │
│  │  ├── Replicas: 1 (DEV/TEST)                              │ │
│  │  ├── Services: LoadBalancer, Internal                     │ │
│  │  ├── Ingress: TLS, SSL Termination                        │ │
│  │  └── Network Policies: Egress/Ingress Rules              │ │
│  │                                                            │ │
│  │  Namespace: onyx-test                                     │ │
│  │  └── [identisch zu dev, eigene IngressClass]             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Managed Services                                           │ │
│  │                                                            │ │
│  │  PostgreSQL Flex (managed)                                │ │
│  │  ├── vob-dev (Flavor: Flex 2.4 Single, 2 CPU/4 GB)     │ │
│  │  ├── vob-test (Flavor: Flex 2.4 Single, 2 CPU/4 GB)    │ │
│  │  ├── Automated Backups (daily, 30 days retention)        │ │
│  │  └── SSL/TLS Encrypted Connections                       │ │
│  │                                                            │ │
│  │  S3-compatible Object Storage (for backups, assets)      │ │
│  │  ├── Bucket: vob-chatbot-backups                          │ │
│  │  ├── Bucket: vob-chatbot-assets                           │ │
│  │  ├── Lifecycle Policies (archive old data)                │ │
│  │  └── Encryption at rest (AES-256)                         │ │
│  │                                                            │ │
│  │  Observability & Monitoring (geplant)                     │ │
│  │  ├── Prometheus (geplant)                                 │ │
│  │  ├── Log-Aggregation (geplant)                            │ │
│  │  └── Alerting (geplant)                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Network & Security                                         │ │
│  │                                                            │ │
│  │  StackIT Network (OpenStack-basiert)                     │ │
│  │  ├── Kubernetes Nodes in SKE Cluster                      │ │
│  │  ├── PostgreSQL Flex ACL (IP-Allowlisting)               │ │
│  │  └── kubectl via kubeconfig (kein Bastion Host)           │ │
│  │                                                            │
│  │  Cloudflare DNS-only (kein StackIT-WAF/DDoS)            │ │
│  │  TLS/SSL Certificates (Let's Encrypt + cert-manager)     │ │
│  │  API Gateway (optional, for rate limiting)                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

        ↓ Internet/VPN

┌──────────────────────────────────────────────────────────────────┐
│ Endbenutzer / VÖB-Mitglieder                                     │
│ (Browser: dev.chatbot.voeb-service.de)                           │
└──────────────────────────────────────────────────────────────────┘
```

### Warum StackIT?

- **Datensouveränität**: 100% deutscher Betreiber (Schwarz-Gruppe), kein US-Zugriff (CLOUD Act)
- **BSI C5 / ISO 27001**: Zertifizierungen vorhanden, BAIT-konform
- **Managed Kubernetes (SKE)**: Produktionsreif, Terraform-provisionierbar
- **PostgreSQL Flex**: Managed DB mit ACL, Backups, SSL
- **AI Model Serving**: LLM-Hosting direkt auf StackIT (GPT-OSS 120B, Qwen3-VL 235B)
- **Region EU01 Frankfurt**: Geringe Latenz fuer deutsche Nutzer
- **Kosten**: DEV+TEST ~426 EUR/Monat (transparent, keine versteckten Gebuehren)

---

## Rationale

### Große Vorteile von StackIT

#### 1. Datenhoheit & Datensouveränität ⭐

- **Rechenzentren**: 100% in Deutschland/Österreich
  - Frankfurt DC10 (primär, operativ)
  - München (operativ, via LEW TelNet)
  - Ellhofen DC08 (operativ seit 2017)
  - Österreich (operativ), Berlin (geplant), Lübbenau (im Bau)
- **Kein Datenabfluss**: Keine US-basierte Infrastruktur
- **DSGVO-konform**: Vollständig, ohne Legal Workarounds
- **Vertrauen**: Schwarz-Gruppe (Schwarz Digits) als Mutterkonzern → deutsches Unternehmen

#### 2. Compliance & Regulierung ⭐

- **BSI C5**: Cloud Computing Compliance zertifiziert
- **ISO 27001**: Informationssicherheit zertifiziert
- **BAIT-relevant**: Erfüllt Banking-Anforderungen
- **Banking-Fokus**: Viele Fintech-Kunden (Verständnis der Anforderungen)

#### 3. Technische Qualität

- **Kubernetes**: Managed K8s, zuverlässig und skalierbar
- **Databases**: PostgreSQL Flex mit Backups, SSL, ACL
- **Storage**: S3-compatible Object Storage
- **Networking**: StackIT Network (OpenStack-basiert), PG ACL (IP-Allowlisting)
- **AI Model Serving**: LLM-Hosting (GPT-OSS 120B, Qwen3-VL 235B)
- **Observability**: Geplant (Prometheus, Log-Aggregation)

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

1. **Kleinere Cloud als AWS/Azure**
   - Mitigation: Für dieses Projekt ausreichend (nicht Google-Scale), stabile Plattform
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

Infrastruktur ist fuer DEV und TEST live. Details siehe `docs/referenz/stackit-implementierungsplan.md`.

1. **Phase 1**: StackIT Account + Service Account + Container Registry -- erledigt
2. **Phase 2**: SKE Cluster (Flavor g1a.4d, Region EU01 Frankfurt) via Terraform -- erledigt
3. **Phase 3**: PostgreSQL Flex (Flavor Flex 2.4 Single), Object Storage Buckets via Terraform -- erledigt
4. **Phase 4**: Namespace-Setup, Ingress (nginx), PG ACL (IP-Allowlisting) -- erledigt
5. **Phase 5**: Monitoring & Observability -- geplant (wird vor PROD-Deployment ergaenzt)
6. **Phase 6**: CI/CD Pipeline (GitHub Actions -> StackIT Registry -> Helm Deploy) -- erledigt

### Kostenschätzung

Aktuelle Kostenübersicht siehe `docs/referenz/stackit-implementierungsplan.md`, Abschnitt Kosten. DEV+TEST: ~426 EUR/Monat.

### Sicherheits-Konfiguration

Aktueller Stand: SEC-01 umgesetzt (PG ACL). SEC-02 bis SEC-07 geplant vor PROD. Details siehe `docs/sicherheitskonzept.md`.

1. **Network Policies**: Kubernetes Network Policies fuer Pod-Segmentierung -- implementiert (SEC-03, 2026-03-05)
2. **TLS/SSL**: cert-manager + Let's Encrypt (Cloudflare DNS-01), ECDSA P-384 (BSI TR-02102-2) -- in Umsetzung
3. **Secrets Management**: Kubernetes Secrets (Sealed Secrets vor PROD geplant)
4. **IAM**: StackIT Service Account + kubeconfig (kein Bastion Host)
5. **Audit Logging**: Geplant
6. **DDoS/WAF**: Kein StackIT-WAF verfuegbar; Cloudflare steht als DNS-only bereit, IP-Allowlisting fuer DEV/TEST empfohlen
7. **Backup-Encryption**: S3 Object Storage mit Encryption at rest
8. **PG ACL**: IP-Allowlisting auf Cluster-Egress + Admin-IP (SEC-01, umgesetzt)

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
| Infrastructure Lead (CCJ) | Nikolaj Ivanov | 2026-02-22 | __ |
| Cloud Architect | [TBD] | [TBD] | __ |
| Projektleiter (CCJ) | Nikolaj Ivanov | 2026-02-22 | __ |
| Auftraggeber (VÖB) | [TBD] | [TBD] | __ |
| Compliance Officer | [TBD] | [TBD] | __ |

---

**ADR Status**: Akzeptiert
**Letzte Aktualisierung**: 2026-03-04
**Version**: 1.1
