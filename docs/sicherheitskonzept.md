# Sicherheitskonzept -- VÖB Service Chatbot

**Dokumentstatus**: Entwurf (teilweise implementiert)
**Letzte Aktualisierung**: 2026-03-07
**Version**: 0.4
**Nächste Überprüfung**: 2026-04-03

---

## Änderungshistorie

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|------------|
| 0.1 | 2026-02 | Nikolaj Ivanov | Initialer Entwurf |
| 0.2 | 2026-03-03 | Nikolaj Ivanov | Überarbeitung auf tatsächlichen Infrastruktur-Stand (DEV + TEST live), Security-Audit-Findings SEC-01 bis SEC-07 integriert, Code-Beispiele korrigiert (Python/FastAPI), Secrets Management aktualisiert |
| 0.3 | 2026-03-05 | Nikolaj Ivanov | Cloud-Infrastruktur-Audit (2026-03-04) referenziert, SEC-03 als ERLEDIGT (NetworkPolicies DEV+TEST), 3 Quick Wins dokumentiert: C6 (DB_READONLY→K8s Secret), H8 (Security-Header), H11 (Script Injection Fix), Audit-Datum korrigiert |
| 0.4 | 2026-03-05 | Nikolaj Ivanov | Zugriffsmatrix (M-CM-3) hinzugefügt, 4-Augen-Prinzip (M-CM-2) dokumentiert mit BAIT-Referenz, Interims-Lösung und geplanten GitHub-Protection-Maßnahmen |

---

## Einleitung und Geltungsbereich

Das vorliegende Sicherheitskonzept beschreibt die sicherheitstechnischen Maßnahmen und Kontrollen des **VÖB Service Chatbot**, einer Enterprise-AI-Chatbot-Lösung auf Basis von Onyx FOSS für die deutsche Bankenwirtschaft.

### Geltungsbereich

Dieses Konzept gilt für:
- Alle Komponenten des VÖB Service Chatbot (Onyx Core + Extension Layer in `backend/ext/` und `web/src/ext/`)
- Die Cloud-Infrastruktur auf StackIT (SKE Kubernetes, PostgreSQL Flex, Object Storage -- Region EU01 Frankfurt)
- Integrationspunkte mit externen Services (Microsoft Entra ID, StackIT AI Model Serving)
- Entwicklungs- (DEV), Test- (TEST) und Produktionsumgebungen (PROD, geplant)

### Zielgruppe
- IT-Sicherheitsteam (CCJ / Coffee Studios)
- Auftraggeber und Stakeholder (VÖB)
- Infrastruktur-Team (StackIT)
- Interne und externe Auditor:innen

### Aktueller Implementierungsstand

| Umgebung | Status | URL | Auth |
|----------|--------|-----|------|
| DEV | LIVE seit 2026-02-27 | `http://188.34.74.187` | Onyx-interne E-Mail/Passwort-Authentifizierung (`AUTH_TYPE: basic`), kein HTTP Basic Auth |
| TEST | LIVE seit 2026-03-03 | `http://188.34.118.201` | Onyx-interne E-Mail/Passwort-Authentifizierung (`AUTH_TYPE: basic`), kein HTTP Basic Auth |
| PROD | Geplant | -- | Entra ID (OIDC) |

> **Hinweis:** Dieses Dokument trennt klar zwischen **IMPLEMENTIERT** (verifiziert in DEV/TEST) und **GEPLANT** (offen, für PROD). Abschnitte die mangels Informationen von VÖB nicht finalisiert werden können, sind mit `[AUSSTEHEND -- Klärung mit VÖB]` markiert.

---

## Schutzziele (CIA)

Die Sicherheitsarchitektur folgt den klassischen Schutzzielen:

### 1. Vertraulichkeit (Confidentiality)
**Ziel**: Sicherstellen, dass nur autorisierte Personen auf sensible Daten zugreifen können.

**Anforderungen und Status**:

| Anforderung | Status | Details |
|-------------|--------|---------|
| Verschlüsselte Datenübertragung (TLS 1.2+) | OFFEN | Aktuell HTTP only (DEV/TEST). TLS geplant nach DNS-Setup |
| Sichere Verwaltung von Credentials | IMPLEMENTIERT | Kubernetes Secrets + GitHub Actions Secrets (environment-getrennt) |
| Zugriffskontrollen (Authentifizierung) | TEILWEISE | Basic Auth aktiv (DEV/TEST). Entra ID (OIDC) geplant (Phase 3) |
| Datenbankzugriffskontrolle | IMPLEMENTIERT | PostgreSQL ACL auf Cluster-Egress-IP eingeschränkt (SEC-01) |
| Minimales Privilege Principle | TEILWEISE | PG-User `onyx_app` hat nur `login` + `createdb`. Kubernetes RBAC: ein globaler Kubeconfig (SEC-05 offen) |

### 2. Integrität (Integrity)
**Ziel**: Gewährleisten, dass Daten nicht unbefugt verändert werden.

**Anforderungen und Status**:

| Anforderung | Status | Details |
|-------------|--------|---------|
| Input-Validierung auf allen Ebenen | IMPLEMENTIERT | Pydantic-Modelle (FastAPI) für alle API-Endpunkte |
| Audit Logs für Änderungen | TEILWEISE | Onyx-internes Logging aktiv. Erweitertes Audit-Logging geplant |
| Supply-Chain-Integrität (CI/CD) | IMPLEMENTIERT | SHA-gepinnte GitHub Actions, Model Server Version gepinnt |
| Datenbank-Constraints | IMPLEMENTIERT | SQLAlchemy ORM + Alembic-Migrationen mit Foreign Keys, NOT NULL etc. |

### 3. Verfügbarkeit (Availability)
**Ziel**: Gewährleisten, dass Systeme und Daten autorisiertem Personal verfügbar sind.

**Anforderungen und Status**:

| Anforderung | Status | Details |
|-------------|--------|---------|
| Kubernetes-Orchestrierung | IMPLEMENTIERT | SKE Cluster mit automatischem Pod-Restart |
| Datenbank-Backups | IMPLEMENTIERT | PG Flex: tägliches Backup (DEV 02:00 UTC, TEST 03:00 UTC, StackIT Managed) |
| Monitoring und Alerting | GEPLANT | Prometheus/Grafana Stack geplant (Phase M5) |
| DDoS-Mitigation | OFFEN | Kein Rate Limiting und keine WAF implementiert |
| Hochverfügbarkeit | OFFEN (DEV/TEST) | Single-Replica pro Service. HA geplant für PROD |

---

## Authentifizierung und Autorisierung

### Aktueller Stand: Onyx-interne E-Mail/Passwort-Authentifizierung (DEV/TEST)

**IMPLEMENTIERT** in DEV und TEST:

Die Authentifizierung ist über die Umgebungsvariable `AUTH_TYPE` konfiguriert. `AUTH_TYPE: "basic"` bezeichnet Onyx-eigene E-Mail/Passwort-Authentifizierung (Session-Cookie-basiert), **nicht** HTTP Basic Auth nach RFC 7617. Aktuell:

```yaml
# values-dev.yaml / values-test.yaml
configMap:
  AUTH_TYPE: "basic"
  REQUIRE_EMAIL_VERIFICATION: "false"
```

Onyx unterstützt folgende Auth-Typen nativ (Enum `AuthType` in `backend/onyx/configs/constants.py`):
- `basic` -- E-Mail + Passwort (aktuell aktiv)
- `oidc` -- OpenID Connect (geplant für Phase 3, Entra ID)
- `google_oauth` -- Google OAuth2 (nicht relevant)
- `saml` -- SAML (nicht relevant)
- `cloud` -- Google Auth + Basic kombiniert (nicht relevant für VÖB-Deployment)

**Onyx RBAC-Rollen** (nativ, `backend/onyx/auth/schemas.py`):

| Rolle | Beschreibung |
|-------|-------------|
| `admin` | Volle Admin-Rechte (erster Login-User wird automatisch Admin) |
| `basic` | Standard-Benutzer |
| `curator` | Admin-Rechte für zugewiesene Gruppen |
| `global_curator` | Admin-Rechte für alle Gruppen |
| `limited` | Eingeschränkter API-Zugang |
| `slack_user` | Slack-Integration-Benutzer (nicht genutzt in VÖB-Deployment) |
| `ext_perm_user` | External Permission User (nicht genutzt in VÖB-Deployment) |

### Geplant: Microsoft Entra ID (OIDC) -- Phase 3

**Status: BLOCKIERT** -- wartet auf Entra ID Zugangsdaten von VÖB IT.

Onyx unterstützt OIDC nativ. Die Konfiguration erfolgt über Umgebungsvariablen:

```yaml
# Geplante Konfiguration (values-prod.yaml)
configMap:
  AUTH_TYPE: "oidc"
  OPENID_CONFIG_URL: "https://login.microsoftonline.com/<TENANT_ID>/v2.0/.well-known/openid-configuration"
  OAUTH_CLIENT_ID: "<CLIENT_ID>"        # → Kubernetes Secret
  OAUTH_CLIENT_SECRET: "<CLIENT_SECRET>" # → Kubernetes Secret
```

**Geplanter Flow (Standard OIDC Authorization Code Flow)**:
```
1. Benutzer öffnet Chatbot → Umleitung zu Microsoft Login
2. Benutzer authentifiziert sich bei Entra ID
3. Entra ID sendet Authorization Code an /auth/oidc/callback
4. Onyx-Backend tauscht Code gegen ID Token + Access Token
5. Onyx erstellt Session (Cookie-basiert)
6. Zugriff auf geschützte Ressourcen
```

**Benötigte Informationen von VÖB** (siehe `docs/entra-id-kundenfragen.md`):

| Information | Status |
|-------------|--------|
| Tenant ID | [AUSSTEHEND -- Klärung mit VÖB] |
| Client ID + Secret | [AUSSTEHEND -- Klärung mit VÖB] |
| Redirect URI / Domain | [AUSSTEHEND -- Klärung mit VÖB] |
| User-Scope (alle oder bestimmte Gruppen) | [AUSSTEHEND -- Klärung mit VÖB] |
| Session-Policy (Standard vs. Strikt) | [AUSSTEHEND -- Klärung mit VÖB] |
| Conditional Access Policies | [AUSSTEHEND -- Klärung mit VÖB] |

### Autorisierung (RBAC)

**IMPLEMENTIERT (Onyx-nativ)**:
Onyx bringt ein rollenbasiertes Zugangskontrollsystem mit (siehe Rollen oben). Rollen werden pro User in der PostgreSQL-Datenbank gespeichert.

**GEPLANT (Extension Layer)**:
Erweitertes RBAC über das Extension-Modul `ext-rbac` (Phase 4b) mit:
- Organisation-basierter Zugriffskontrolle
- Token-Quotas pro Organisation
- Erweiterte Rollen (VÖB Admin, Org Admin, Content Manager)

Details werden in der Modulspezifikation für Phase 4b definiert.

### Zugriffsmatrix

Die folgende Matrix dokumentiert alle Zugriffsrechte auf Infrastruktur- und Anwendungsressourcen.

#### GitHub Repository & CI/CD

| Ressource | Rolle | Zugriff | Bemerkung |
|-----------|-------|---------|-----------|
| GitHub Repository | Tech Lead (Nikolaj Ivanov, CCJ) | Admin (Write, Merge, Settings) | Einziger Admin aktuell |
| GitHub Repository | VÖB | Read | Einsicht in Code, PRs, Issues |
| GitHub Environment `dev` | CI/CD Pipeline (auto) | Deploy | Automatisch bei Push auf `main` |
| GitHub Environment `test` | Tech Lead | Deploy (workflow_dispatch) | Manueller Trigger |
| GitHub Environment `prod` | Tech Lead + Reviewer | Deploy (workflow_dispatch + Approval) | 4-Augen-Prinzip (geplant) |
| GitHub Actions Secrets (global) | Repository Admin | Read/Write | STACKIT_REGISTRY_*, STACKIT_KUBECONFIG |
| GitHub Actions Secrets (per env) | Environment Admin | Read/Write | PG, Redis, S3, DB_READONLY Passwörter |

#### Kubernetes Cluster

| Ressource | Rolle | Zugriff | Bemerkung |
|-----------|-------|---------|-----------|
| SKE Cluster `vob-chatbot` | Tech Lead | Cluster-Admin (Kubeconfig) | SEC-05: Separate Kubeconfigs geplant |
| SKE Cluster `vob-chatbot` | CI/CD Pipeline | Cluster-Admin (Kubeconfig) | Selber Kubeconfig wie Tech Lead |
| Namespace `onyx-dev` | Tech Lead / CI/CD | Full Access | Deployment, Secrets, ConfigMaps |
| Namespace `onyx-test` | Tech Lead / CI/CD | Full Access | Deployment, Secrets, ConfigMaps |
| Namespace `onyx-prod` | Tech Lead + Reviewer | Full Access | Geplant: Namespace-scoped RBAC (SEC-05) |
| SKE Cluster API | Alle (Internet) | Zugriff mit Kubeconfig | **OPS-01: ACL auf Cluster-Egress-IP einschränken (vor PROD)** |

#### Datenbanken & Storage

| Ressource | Rolle / User | Zugriff | Bemerkung |
|-----------|-------------|---------|-----------|
| PostgreSQL DEV (`vob-dev`) | `onyx_app` | Read/Write (login, createdb) | ACL: Cluster-Egress-IP (SEC-01) |
| PostgreSQL DEV (`vob-dev`) | `db_readonly_user` | Read-Only | Knowledge Graph, Terraform-verwaltet |
| PostgreSQL TEST (`vob-test`) | `onyx_app` | Read/Write | Eigene Instanz, ACL identisch |
| PostgreSQL TEST (`vob-test`) | `db_readonly_user` | Read-Only | Knowledge Graph, Terraform-verwaltet |
| PostgreSQL (Admin) | Tech Lead | Full Access (via Admin-IP) | `109.41.112.160/32` in PG ACL |
| Object Storage DEV (`vob-dev`) | Anwendung | Read/Write (S3 API) | Access Key in K8s Secret |
| Object Storage TEST (`vob-test`) | Anwendung | Read/Write (S3 API) | Access Key in K8s Secret |
| Container Registry | CI/CD Robot Account | Push/Pull | `robot$voeb-chatbot+github-ci` |

#### Infrastructure as Code

| Ressource | Rolle | Zugriff | Bemerkung |
|-----------|-------|---------|-----------|
| Terraform State | Tech Lead (lokal) | Read/Write | SEC-04: Remote State geplant |
| Terraform SA (`voeb-terraform`) | Tech Lead | StackIT Project Admin | Service Account Credentials lokal |
| StackIT Console | Tech Lead | Projekt-Admin | Web-UI für Managed Services |

#### Externe Services & APIs

| Ressource | Rolle / Zugang | Zugriff | Bemerkung |
|-----------|---------------|---------|-----------|
| StackIT AI Model Serving (LLM) | Anwendung (API Token) | HTTPS API Calls | Token in Onyx Admin UI (DB), Rotation 90d empfohlen |
| StackIT Console | Tech Lead | Projekt-Admin (Web-UI) | Managed-Service-Verwaltung (PG, S3, SKE) |
| Cloudflare DNS (`voeb-service.de`) | VÖB IT (Leif Rasch) | Zone Admin | DNS-Records und API Token für cert-manager |
| cert-manager (K8s) | ClusterIssuer | Cloudflare API Token (K8s Secret in NS `cert-manager`) | Für Let's Encrypt DNS-01 Challenge |
| Docker Hub | Anwendung (public) | Pull (kein Auth) | Model Server `onyxdotapp/onyx-model-server:v2.9.8` |
| Microsoft Entra ID | VÖB IT (geplant) | OIDC Provider | Phase 3, Zugangsdaten ausstehend |

#### Geplante Änderungen

| Maßnahme | Betrifft | Priorität | Status |
|----------|----------|-----------|--------|
| SEC-05: Namespace-scoped ServiceAccounts | Kubernetes RBAC | ~~P1~~ → P3 | **ZURÜCKGESTELLT** (2026-03-08) — PROD = eigener Cluster |
| SEC-04: Remote State Backend | Terraform | ~~P1~~ → P3 | **ZURÜCKGESTELLT** (2026-03-08) — Solo-Dev, FileVault |
| SEC-06: Container SecurityContext | Helm Values | ~~P2~~ → **P1** | Offen — `privileged: true` entfernen |
| Branch Protection auf `main` | GitHub | P1 (vor PROD) | **ERLEDIGT** (2026-03-07): PR required, 3 Status Checks, kein Review (Solo-Dev) |
| Environment Protection auf `prod` | GitHub | P1 (vor PROD) | Offen |
| VÖB als Required Reviewer | GitHub Environment `prod` | Langfristig | Offen |

### 4-Augen-Prinzip (BAIT Kap. 8.6)

**Anforderung**: BAIT fordert, dass keine Änderung an der Produktionsumgebung ohne dokumentierte zweite Freigabe erfolgt. Dies betrifft insbesondere Code-Änderungen, Konfigurationsänderungen und Infrastrukturänderungen.

**Aktueller Stand** (1-Person-Entwicklungsteam):

Das Projekt wird aktuell von einem einzelnen Tech Lead (Nikolaj Ivanov, CCJ) entwickelt und betrieben. Eine vollständige Umsetzung des 4-Augen-Prinzips mit zwei unabhängigen Personen ist daher noch nicht möglich.

**Implementierte Maßnahmen**:

| Maßnahme | Status | Beschreibung |
|----------|--------|-------------|
| Feature-Branch + PR Pflicht | Implementiert | Jede Änderung läuft über einen Feature-Branch und wird per Pull Request gemergt |
| PR-Checkliste | Implementiert | Dokumentierte Checkliste vor jedem Commit (Tests, Lint, Types, Doku) |
| Explizite Commit-Freigabe | Implementiert | Tech Lead gibt jeden Commit explizit frei (Self-Review-Prozess) |
| CHANGELOG-Dokumentation | Implementiert | Jede Änderung wird im Changelog erfasst |

**Implementierte Maßnahmen**:

| Maßnahme | Konfiguration | Effekt | Status |
|----------|--------------|--------|--------|
| GitHub Branch Protection auf `main` | Require Pull Request, 3 Required Status Checks (helm-validate, build-backend, build-frontend) | Kein direkter Push auf `main` möglich. Review-Requirement entfernt (Solo-Dev, 2026-03-07). | **ERLEDIGT** |

**Geplante Maßnahmen** (vor PROD):

| Maßnahme | Konfiguration | Effekt |
|----------|--------------|--------|
| GitHub Environment Protection auf `prod` | Required Reviewers (Tech Lead + VÖB-Kontakt) | Kein PROD-Deploy ohne zweite Freigabe |
| Wait Timer auf `prod` | Optional: 10 Min Bedenkzeit | Versehentliche Freigabe verhindern |

**Langfristige Lösung**: VÖB-Stakeholder oder ein zweiter CCJ-Mitarbeiter wird als Required Reviewer für das GitHub Environment `prod` hinterlegt. Damit ist das 4-Augen-Prinzip für alle Produktionsänderungen technisch erzwungen.

> **Querverweise**: Change-Management-Prozess in `docs/betriebskonzept.md`, Abschnitt "Change Management".

---

## Datenverschlüsselung

### Verschlüsselung im Transit (In Transit)

#### TLS/HTTPS

**Status: NICHT IMPLEMENTIERT (DEV/TEST)**

Aktuell kommunizieren DEV und TEST über HTTP:
- DEV: `http://188.34.74.187`
- TEST: `http://188.34.118.201`

**Geplant (nach DNS-Setup)**:
- TLS-Terminierung am NGINX Ingress Controller (in-cluster)
- Let's Encrypt Zertifikate via cert-manager
- Voraussetzung: DNS-Einträge müssen von VÖB IT gesetzt werden

```yaml
# Aktuelle Konfiguration (DEV + TEST)
letsencrypt:
  enabled: false  # Kein TLS bis DNS verfügbar
```

**DNS-Status (2026-03-05)**: A-Records gesetzt (`dev.chatbot.voeb-service.de` → `188.34.74.187`, `test.chatbot.voeb-service.de` → `188.34.118.201`). Cloudflare Proxy auf DNS-only (graue Wolke) umgestellt und verifiziert (2026-03-05). **Ausstehend:** TLS-Zertifikate via cert-manager + Let's Encrypt (Cloudflare API Token Authentifizierungsproblem, wartet auf Token-Fix).

#### Interne Kommunikation (Cluster-intern)

**Status: NICHT VERSCHLÜSSELT**

Die Kommunikation zwischen Pods innerhalb des Kubernetes-Clusters (z.B. API → Vespa, API → Redis, API → PostgreSQL) erfolgt unverschlüsselt über das Cluster-interne Netzwerk. Dies ist in Kubernetes-Deployments Standard, da das Cluster-Netzwerk als vertrauenswürdig gilt.

- PostgreSQL-Verbindung: TLS wird von StackIT Managed PG Flex unterstützt, ist aber aktuell nicht erzwungen
- Redis: Passwort-geschützt, aber kein TLS
- Vespa: Cluster-intern, kein TLS

#### StackIT AI Model Serving (LLM-API)

**IMPLEMENTIERT**: Die Verbindung zum LLM-Provider erfolgt über HTTPS:
```
API Base: https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1
```

### Verschlüsselung im Ruhezustand (At Rest)

#### PostgreSQL Datenbank (StackIT Managed Flex)

- **Backup-Verschlüsselung**: StackIT Managed Service -- Details zur Verschlüsselung at-rest müssen bei StackIT verifiziert werden (SEC-07)
- **Backup-Schedule**: Täglich (DEV: 02:00 UTC, TEST: 03:00 UTC, konfiguriert per Terraform)
- **Column-Level Encryption**: Nicht implementiert. API Keys werden von Onyx im Klartext in der DB gespeichert (Onyx-Standardverhalten)

#### Vespa Index (Vektorspeicher)

- Läuft in-cluster als StatefulSet mit PersistentVolume (20 Gi)
- Verschlüsselung abhängig vom StackIT Volume-Provider (`premium-perf2-stackit`)
- [AUSSTEHEND -- Verifizierung ob StackIT Storage Classes Encryption-at-Rest bieten (SEC-07)]

#### Object Storage (StackIT S3-kompatibel)

- Buckets: `vob-dev` (DEV), `vob-test` (TEST)
- Zugriff über Access Key / Secret Key (pro Environment getrennt)
- [AUSSTEHEND -- Verifizierung ob StackIT Object Storage Encryption-at-Rest bietet (SEC-07)]

### Geheimnismanagement

**IMPLEMENTIERT: Kubernetes Secrets + GitHub Actions Secrets**

Es wird **kein** HashiCorp Vault eingesetzt. Die Secrets-Verwaltung erfolgt über:

1. **GitHub Actions Secrets** (CI/CD-Pipeline):
   - Global (Repository-weit): `STACKIT_REGISTRY_USER`, `STACKIT_REGISTRY_PASSWORD`, `STACKIT_KUBECONFIG`
   - Per Environment (`dev`, `test`, `prod`): `POSTGRES_PASSWORD`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `DB_READONLY_PASSWORD`, `REDIS_PASSWORD`
   - Environment-Trennung stellt sicher, dass DEV-Secrets nicht in TEST/PROD verwendet werden

2. **Kubernetes Secrets** (Runtime):
   - `onyx-postgresql` (DB-Credentials)
   - `onyx-redis` (Redis-Passwort)
   - `onyx-dbreadonly` (DB Readonly-Passwort, seit C6-Fix 2026-03-05)
   - `onyx-objectstorage` (S3-Credentials)
   - `stackit-registry` (Image Pull Secret)
   - Secrets werden per Helm `--set` aus GitHub Actions injiziert (nicht in Git)

3. **Terraform State** (Infrastruktur-Credentials):
   - **WARNUNG**: Terraform State liegt aktuell lokal auf dem Entwickler-Laptop und enthält Klartext-Passwörter (PG-Credentials)
   - Migration zu Remote State (StackIT Object Storage) geplant (SEC-04)

**Verwaltete Geheimnisse**:

| Geheimnis | Speicherort | Rotation |
|-----------|-------------|----------|
| PostgreSQL-Passwort (App) | GitHub Secret → K8s Secret | Manuell |
| PostgreSQL-Passwort (Readonly) | GitHub Secret → K8s Secret | Manuell |
| Redis-Passwort | GitHub Secret → K8s Secret | Manuell |
| S3 Access Key + Secret | GitHub Secret → K8s Secret | Manuell |
| Container Registry Token | GitHub Secret | Manuell |
| Kubeconfig | GitHub Secret (base64) | Ablauf: 2026-05-28 |
| StackIT AI Model Serving Token | Onyx Admin UI (in DB) | Manuell (90d empfohlen) |
| Terraform SA Key | `~/.stackit/` (lokal, chmod 600) | Manuell |

> **Offener Punkt (SEC-04):** Automatische Secret-Rotation ist nicht implementiert. Für PROD muss ein Rotationskonzept definiert werden.

---

## Netzwerksicherheit

### Kubernetes-Architektur

**IMPLEMENTIERT**:

```
Internet
  │
  ├─→ NGINX Ingress (LoadBalancer)
  │     DEV: 188.34.74.187 (IngressClass: nginx)
  │     TEST: 188.34.118.201 (IngressClass: nginx-test)
  │
  ├─→ [onyx-dev Namespace]
  │     API Server → Vespa, Redis, Celery
  │     Web Server (Frontend)
  │     Model Server (Inference + Indexing)
  │
  └─→ [onyx-test Namespace]
        API Server → Vespa, Redis, Celery
        Web Server (Frontend)
        Model Server (Inference + Indexing)

Externe Services (über Internet):
  - StackIT PostgreSQL Flex (DEV + TEST: eigene Instanzen)
  - StackIT Object Storage (S3)
  - StackIT AI Model Serving (LLM API, HTTPS)
```

**Cluster-Details**:
- SKE Cluster `vob-chatbot` in StackIT Region EU01 (Frankfurt)
- Node Pool `devtest`: 2x g1a.8d (8 vCPU, 32 GB RAM)
- Flatcar OS
- Maintenance-Window: 02:00-04:00 UTC (automatische K8s + OS Updates)
- Cluster-Egress-IP (NAT Gateway): `188.34.93.194` (fest für Cluster-Lifecycle)

### Kubernetes Network Policies

**Status: IMPLEMENTIERT (SEC-03, 2026-03-05)**

5 NetworkPolicies auf DEV + TEST applied (Zero-Trust Baseline):
- `01-default-deny-all`: Default-Deny für allen Ingress + Egress
- `02-allow-dns-egress`: DNS-Egress Port 53 + 8053 (StackIT/Gardener CoreDNS)
- `03-allow-intra-namespace`: Intra-Namespace-Kommunikation erlaubt
- `04-allow-external-ingress-nginx`: Ingress nur über NGINX Controller
- `05-allow-external-egress`: Egress für PostgreSQL (5432) und HTTPS (443)

Cross-Namespace-Isolation verifiziert (DEV ↔ TEST). Details: `docs/audit/networkpolicy-analyse.md`

### PostgreSQL Netzwerk-ACL

**IMPLEMENTIERT (SEC-01)**:

Die PostgreSQL-Instanzen sind auf Netzwerkebene eingeschränkt:

```hcl
# Terraform: pg_acl in beiden Environments
pg_acl = [
  "188.34.93.194/32",   # Cluster-Egress-IP (NAT Gateway)
  "109.41.112.160/32"   # Admin-IP (Nikolaj Ivanov, Debugging)
]
```

- Die `pg_acl`-Variable hat **keinen Default** mehr -- jedes Environment muss seine erlaubten CIDRs explizit angeben
- Zugriff von außerhalb der erlaubten CIDRs wird auf Netzwerkebene abgelehnt

### Ingress & TLS

**IMPLEMENTIERT (ohne TLS)**:

- NGINX Ingress Controller läuft in-cluster (Helm Subchart)
- DEV: IngressClass `nginx`, LoadBalancer-IP `188.34.74.187`
- TEST: Eigene IngressClass `nginx-test`, LoadBalancer-IP `188.34.118.201` (Konflikt-Vermeidung im Shared Cluster)
- TLS: **Nicht aktiv** (`letsencrypt.enabled: false`)

**Implementierte Security-Header** (H8, 2026-03-05):
- `X-Content-Type-Options: nosniff` — verhindert MIME-Type-Sniffing
- `X-Frame-Options: DENY` — verhindert Clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin` — beschränkt Referrer-Informationen
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` — deaktiviert unnötige Browser-APIs
- Konfiguriert via `http-snippet` in `values-common.yaml`

**Geplant (nach DNS-Setup)**:
- cert-manager mit Let's Encrypt via Cloudflare DNS-01 Challenge (BSI TR-02102-2: ECDSA P-384 Pflicht, RSA 2048 von LE Standard erfüllt BSI nicht). Details: `docs/runbooks/dns-tls-setup.md`
- HSTS-Header (benötigt aktives HTTPS)
- SSL-Redirect

### WAF (Web Application Firewall)

**Status: NICHT IMPLEMENTIERT**

Aktuell ist keine WAF im Einsatz. Für PROD muss evaluiert werden, ob StackIT eine WAF-Lösung anbietet oder ob eine Ingress-basierte Lösung (z.B. ModSecurity) eingesetzt wird.

---

## API-Sicherheit

### Input Validation

**IMPLEMENTIERT (Onyx-nativ)**:

Onyx nutzt **Pydantic-Modelle** (Python) für die Input-Validierung auf allen API-Endpunkten. FastAPI erzwingt automatisch die Schema-Validierung bei jedem Request.

```python
# Beispiel: Onyx Chat-Message Validierung (Pydantic BaseModel)
from pydantic import BaseModel, Field

class CreateChatMessageRequest(BaseModel):
    chat_session_id: uuid.UUID
    message: str
    parent_message_id: int | None = None
    # ... weitere Felder mit Typ-Validierung
```

Ungültige Requests werden mit HTTP 422 (Validation Error) abgelehnt, bevor sie die Business-Logik erreichen.

### CORS (Cross-Origin Resource Sharing)

**IMPLEMENTIERT (Onyx-nativ)**:

CORS ist in `backend/onyx/main.py` konfiguriert:

```python
application.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGIN,  # Konfigurierbar via Umgebungsvariable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> **Bekannte Einschränkung:** Die aktuelle CORS-Konfiguration ist permissiv (`allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`). Für PROD sollte evaluiert werden, ob `allow_methods` auf die tatsächlich genutzten HTTP-Methoden (GET, POST, PUT, DELETE, PATCH) und `allow_headers` auf die benötigten Header eingeschränkt werden können. Ebenso sollte `CORS_ALLOWED_ORIGIN` auf die tatsächliche Produktions-Domain beschränkt werden (z.B. `https://chatbot.voeb-service.de`).

### Route-Auth-Prüfung

**IMPLEMENTIERT (Onyx-nativ)**:

Onyx prüft beim App-Start, dass alle API-Routen entweder eine Authentifizierung erfordern oder explizit als öffentlich markiert sind:

```python
# backend/onyx/main.py
check_router_auth(application)
```

### Rate Limiting

**Status: NICHT IMPLEMENTIERT**

Aktuell ist kein Rate Limiting auf Anwendungsebene implementiert. Das LLM-Backend (StackIT AI Model Serving) hat eigene Rate Limits:
- TPM: 200.000 Tokens/Minute (Output-Tokens 5x gewichtet)
- RPM: 30-600 Requests/Minute (modellabhängig)

Für PROD sollte Rate Limiting auf Ingress-Ebene (NGINX) oder Anwendungsebene evaluiert werden.

### CSRF Protection

**TEILWEISE IMPLEMENTIERT (Onyx-nativ)**:

Onyx nutzt Cookie-basierte Sessions (via `fastapi-users`). CSRF-Schutz wird über SameSite-Cookies und Origin-Header-Prüfung realisiert.

---

## CI/CD Security

### Pipeline-Architektur

**IMPLEMENTIERT** (`.github/workflows/stackit-deploy.yml`):

```
prepare (6s)          → Git SHA als Image Tag
  ├── build-backend   → ~6 Min (parallel)  → StackIT Registry
  └── build-frontend  → ~8 Min (parallel)  → StackIT Registry
deploy-{env}          → ~2 Min (Helm upgrade + Smoke Test)
```

### Sicherheitsmaßnahmen (Enterprise-Härtung)

| Maßnahme | Status | Details |
|----------|--------|---------|
| SHA-gepinnte GitHub Actions | IMPLEMENTIERT | Alle 6 Actions auf Commit-Hash fixiert (Supply-Chain-Schutz gegen kompromittierte Action-Tags) |
| Least-Privilege Permissions | IMPLEMENTIERT | `permissions: contents: read` -- Pipeline hat nur Lesezugriff auf Repo |
| Concurrency Control | IMPLEMENTIERT | Max 1 Deploy pro Environment gleichzeitig, cancel-in-progress bei neuem Push |
| Environment-getrennte Secrets | IMPLEMENTIERT | GitHub Environments `dev`, `test`, `prod` mit jeweils eigenen Secrets |
| Gepinnte Image-Versionen | IMPLEMENTIERT | Model Server auf `v2.9.8` fixiert (nicht `:latest`) |
| Required Reviewers (PROD) | GEPLANT | In GitHub Environment Settings für `prod` zu aktivieren |
| Container Security Scanning | OFFEN | Kein Trivy/Snyk-Scan in der Pipeline (kein SEC-Finding, aber empfohlen für PROD) |

**SHA-gepinnte Actions (verifiziert)**:

```yaml
# Alle Actions sind auf Commit-Hash gepinnt, nicht auf Tags:
actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5        # v4
docker/login-action@c94ce9fb468520275223c153574b00df6fe4bcc9     # v3
docker/setup-buildx-action@8d2750c68a42422c14e847fe6c8ac0403b4cbd6f  # v3
docker/build-push-action@10e90e3645eae34f1e60eeb005ba3a3d33f178e8    # v6
azure/setup-helm@bf6a7d304bc2fdb57e0331155b7ebf2c504acf0a        # v4
azure/setup-kubectl@c0c8b32d33a5244f1e5947304550403b63930415     # v4
```

**Input-Sanitierung** (H11, 2026-03-05):
- `inputs.image_tag` wird als Environment-Variable übergeben (nicht direkt in Shell interpoliert)
- Docker-Tag-Regex-Validierung: `[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}`
- `set -euo pipefail` in allen Shell-Schritten

### Deploy-Verhalten pro Environment

| Feature | DEV | TEST | PROD |
|---------|-----|------|------|
| Trigger | `main`-Push oder manuell | Nur manuell (`workflow_dispatch`) | Nur manuell (`workflow_dispatch`) |
| Helm Rollback | Manuell | `--atomic` (automatisch) | `--atomic` (automatisch) |
| Smoke Test | `/api/health` (120s Timeout) | `/api/health` (120s Timeout) | `/api/health` (180s Timeout, 18 Attempts) |
| Required Reviewers | Nein | Nein | Ja (GitHub Settings) |

### Container Registry

- **Registry**: `registry.onstackit.cloud` (StackIT, Region EU01 Frankfurt)
- **Projekt**: `voeb-chatbot`
- **Zugang**: Robot Account (`robot$voeb-chatbot+github-ci`) -- Push- und Pull-Rechte (CI/CD Push + Kubernetes Image Pull)
- **Datensouveränität**: Images werden in StackIT Registry gespeichert, nicht auf Docker Hub (Ausnahme: Model Server, siehe unten)

### Image-Strategie

| Dienst | Image-Quelle | Tag-Strategie |
|--------|-------------|---------------|
| Backend (API + Celery) | StackIT Registry | Git SHA (z.B. `ea70a11`) |
| Frontend (Web) | StackIT Registry | Git SHA |
| Model Server | Docker Hub (Upstream Onyx) | Gepinnt auf `v2.9.8` |

> **Hinweis:** Der Model Server wird nicht von uns gebaut. Er ist identisch mit Upstream Onyx und wird direkt von Docker Hub gepullt. Für PROD sollte evaluiert werden, ob das Image in die StackIT Registry gespiegelt wird (Datensouveränität).

---

## LLM-spezifische Sicherheit

### LLM-Provider: StackIT AI Model Serving

**IMPLEMENTIERT (DEV + TEST seit 2026-03-03)**:

| Aspekt | Details |
|--------|---------|
| Provider | StackIT AI Model Serving (vLLM-Backend) |
| API-Protokoll | OpenAI-kompatible API über HTTPS |
| Region | EU01 Frankfurt (Daten bleiben in Deutschland) |
| Chat-Modelle | GPT-OSS 120B (131K Kontext), Qwen3-VL 235B (218K Kontext) |
| Embedding-Modell | nomic-embed-text-v1 (self-hosted, aktiv). Ziel: Qwen3-VL-Embedding 8B (Blocker aufgehoben (Upstream PR #9005)) |
| Auth | Token-basiert (StackIT AI Model Serving Token) |
| Preise | 0,45 EUR / 1M Input-Tokens, 0,65 EUR / 1M Output-Tokens |

**Datensouveränität**: Die LLM-Verarbeitung findet vollständig auf StackIT-Infrastruktur in Frankfurt statt. Es werden keine Daten an OpenAI, Google oder andere externe LLM-Provider gesendet.

### Prompt Injection Prevention

**TEILWEISE IMPLEMENTIERT (Onyx-nativ)**:

Onyx bietet System-Prompt-Konfiguration über die Admin UI. Der Extension Layer (`ext-prompts`, Phase 4) wird Custom Prompt Injection für VÖB-spezifische Guardrails ermöglichen.

Aktuell implementierte Schutzmaßnahmen:
- System Prompts werden vor User-Input platziert (Onyx-Standard)
- Input-Validierung über Pydantic-Modelle (Längenbegrenzung)

**Geplant** (Phase 4 Extension Module):
- Custom System Prompt Injection über Hook in `backend/onyx/chat/prompt_utils.py`
- Token Limits Management (pro User/Organisation) über `ext-token`-Modul
- Output-Filterung für sensible Daten (IBAN, Kreditkartennummern etc.)

### Token Limits als Kostenschutz

**GEPLANT (Phase 4b)**:

Das **Token Limits Management Modul** (`ext-token`) wird implementieren:
- Pro-User und Pro-Organisation Quotas
- Real-Time Token-Tracking
- Pre-Request Validation (Request-Ablehnung bei Quota-Überschreitung)
- Hard Stops bei Überschreitung

Aktuell gibt es keine Token-Limitierung auf Anwendungsebene. Die StackIT-seitigen Rate Limits (200K TPM, 30-600 RPM) bieten einen grundlegenden Schutz.

---

## Datenschutz und DSGVO

### Rechtsgrundlage und Compliance

Der VÖB Service Chatbot muss mit folgenden Regelwerken konform sein:
- **DSGVO** (Datenschutz-Grundverordnung EU)
- **BDSG** (Bundesdatenschutzgesetz Deutschland)
- **BAIT** (Bankaufsichtliche Anforderungen an die IT)
- **BSI-Grundschutz** (IT-Grundschutz-Kompendium)

**Status der Compliance**:

| Regelwerk | Anforderung | Status |
|-----------|-------------|--------|
| DSGVO | Datenverarbeitung in EU | ERFÜLLT (StackIT EU01 Frankfurt) |
| DSGVO | Keine Drittland-Übermittlung | ERFÜLLT (LLM auf StackIT, kein OpenAI) |
| DSGVO | Löschkonzept | GEPLANT (Onyx unterstützt User-Löschung nativ) |
| DSGVO | Datenschutzerklärung | [AUSSTEHEND -- Klärung mit VÖB] |
| DSGVO | AVV (Auftragsverarbeitungsvertrag) | [AUSSTEHEND -- Klärung mit VÖB] |
| BAIT | Verschlüsselung im Transit | OFFEN (kein TLS, siehe oben) |
| BAIT | Zugangskontrolle | TEILWEISE (Basic Auth, Entra ID geplant) |
| BAIT | Netzwerksegmentierung | ERFÜLLT (SEC-03: 5 NetworkPolicies, DEV+TEST, 2026-03-05) |
| BSI-Grundschutz | Container-Härtung | OFFEN (SEC-06: keine SecurityContexts) |
| BSI-Grundschutz | Verschlüsselung at-rest | OFFEN (SEC-07: nicht verifiziert) |

### Personenbezogene Daten (PII)

| Datenkategorie | Beispiele | Sensibilität | Speicherort |
|---|---|---|---|
| Identitätsdaten | Name, Email | Hoch | PostgreSQL (StackIT Managed) |
| Konversationsdaten | Chat Messages, Prompts | Mittel | PostgreSQL + Vespa (in-cluster) |
| Dokumente / Embeddings | Hochgeladene Dateien, Vektoren | Mittel | Object Storage + Vespa |
| API Keys / Tokens | LLM-Token, Session-Cookies | Kritisch | PostgreSQL (Onyx-DB) |
| Nutzungsmetriken | Login-Zeit, Features genutzt | Niedrig | PostgreSQL |

### Aufbewahrungsfristen

[AUSSTEHEND -- Klärung mit VÖB]

Aufbewahrungsfristen müssen in Abstimmung mit VÖB Compliance / Datenschutzbeauftragtem definiert werden.

### Datenverarbeitungsverträge (DPA / AVV)

[AUSSTEHEND -- Klärung mit VÖB]

Erforderlich zwischen:
- VÖB (Verantwortlicher) ↔ CCJ / Coffee Studios (Auftragsverarbeiter)
- VÖB / CCJ ↔ StackIT (Unterauftragsverarbeiter: Infrastruktur, KI-Modelle)

> **Hinweis**: Es gibt **keinen** Vertrag mit OpenAI oder anderen externen LLM-Providern. Die gesamte LLM-Verarbeitung erfolgt über StackIT AI Model Serving in Deutschland.

---

## Logging und Audit Trail

### Aktueller Stand

**IMPLEMENTIERT (Onyx-nativ)**:

Onyx loggt auf verschiedenen Ebenen:
- API-Server-Logs (FastAPI, konfigurierbar über `LOG_LEVEL: "INFO"`)
- Celery-Worker-Logs (Background Jobs)
- Kubernetes Pod-Logs (stdout/stderr, von Kubelet verwaltet)

**NICHT IMPLEMENTIERT**:
- Zentralisiertes Log-Management (ELK Stack, Loki o.ä.)
- SIEM-Integration
- Strukturiertes Audit-Logging für Sicherheitsereignisse
- Log-Retention-Policies

### Log-Retention

Kubernetes Pod-Logs werden standardmäßig bei Pod-Restart gelöscht. Ohne zentralisierte Log-Aggregation gehen Logs bei Pod-Neustarts verloren.

**Geplant** (Phase M5):
- Prometheus + Grafana für Metriken und Dashboards
- Evaluation einer Log-Aggregations-Lösung

---

## Schwachstellenmanagement

### Dependency Management

**TEILWEISE IMPLEMENTIERT**:

| Aspekt | Status | Details |
|--------|--------|---------|
| Python-Dependencies | Onyx-verwaltet | `backend/requirements/` (pip, gepinnte Versionen) |
| Node.js-Dependencies | Onyx-verwaltet | `web/package.json` (npm/yarn, lock-file) |
| Container-Image-Scanning | OFFEN | Kein Trivy/Snyk in CI/CD (empfohlen für PROD) |
| Automatische Updates | OFFEN | Kein Dependabot konfiguriert |
| Upstream-Sync | IMPLEMENTIERT | `.github/workflows/upstream-check.yml` -- wöchentlicher Merge-Kompatibilitäts-Check gegen Onyx FOSS |

### Patch Management

| Severity | SLA | Prozess |
|----------|-----|---------|
| Critical (CVSS >= 9.0) | 24 Stunden | Sofortiger Patch, Test, Deployment |
| High (7.0-8.9) | 7 Tage | Patch vorbereiten, in nächstem Release deployen |
| Medium (4.0-6.9) | 30 Tage | Sammeln mit anderen Updates |
| Low (0.1-3.9) | 90 Tage | Nächster Maintenance-Zyklus |

---

## Security-Audit Findings (SEC-01 bis SEC-07)

> **Quelle**: Enterprise-Audit der Infrastruktur (2026-03-04). Priorisierung: P0 = vor TEST-Deploy, P1 = vor PROD, P2 = vor VÖB-Abnahme.

| ID | Finding | Priorität | Status |
|----|---------|-----------|--------|
| SEC-01 | PostgreSQL ACL auf Cluster-Egress-IP einschränken | P0 | **ERLEDIGT** (2026-03-03) |
| SEC-02 | Node Affinity erzwingen (DEV/TEST auf eigenen Nodes) | ~~P1~~ | **ZURÜCKGESTELLT** — Begründung siehe unten |
| SEC-03 | Kubernetes NetworkPolicies (Namespace-Isolation) | P1 | **ERLEDIGT** (2026-03-05) |
| SEC-04 | Terraform Remote State (Secrets im Klartext lokal) | ~~P1~~ → P3 | **ZURÜCKGESTELLT** — Quick Win `chmod 600` umgesetzt, Remote State optional |
| SEC-05 | Separate Kubeconfigs pro Environment (RBAC) | ~~P1~~ → P3 | **ZURÜCKGESTELLT** — PROD = eigener Cluster (ADR-004), löst sich automatisch |
| SEC-06 | Container SecurityContext (`privileged: true` entfernen) | ~~P2~~ → **P1** | OFFEN — `privileged: true` auf Celery/Model Server/Vespa ist inakzeptabel |
| SEC-07 | Encryption-at-Rest verifizieren (PG, S3, Volumes) | P2 | **ERLEDIGT** (2026-03-08) — StackIT Default |

### SEC-01: PostgreSQL ACL (ERLEDIGT)

**Problem**: `pg_acl = ["0.0.0.0/0"]` -- PostgreSQL war für das gesamte Internet erreichbar.

**Lösung (implementiert 2026-03-03)**:
- `pg_acl` Default in Terraform-Modulen entfernt (erzwingt explizite Angabe)
- DEV + TEST: `pg_acl = ["188.34.93.194/32", "109.41.112.160/32"]`
- `188.34.93.194` = Cluster-Egress-IP (NAT Gateway, fest für Cluster-Lifecycle)
- `109.41.112.160` = Admin-IP (für direkten DB-Zugriff bei Debugging)

### SEC-02: Node Affinity — ZURÜCKGESTELLT (2026-03-08)

**Ursprüngliches Finding**: `nodeSelector` in Helm Values erzwingen, damit DEV- und TEST-Pods jeweils auf eigenen Nodes laufen.

**Entscheidung: Zurückgestellt — kein akuter Handlungsbedarf.** Begründung:

1. **ADR-004 sagt explizit**: "Kein Dedicated-Node-Affinity nötig — der Scheduler balanciert automatisch" (Zeile 61). Die eigene Architekturentscheidung stuft Node Affinity als unnötig ein.
2. **Bestehende Isolation ist ausreichend**: Namespace-Isolation + NetworkPolicies (SEC-03, 5 Policies pro Namespace, Cross-NS-Traffic verifiziert blockiert) + separate PG-Instanzen + separate S3-Buckets + separate Secrets + separate LoadBalancer-IPs. BAIT und BSI IT-Grundschutz fordern nachweisbare Umgebungstrennung, aber nicht explizit auf Node-Ebene.
3. **DEV/TEST enthalten keine Produktionsdaten** — das Restrisiko bei Pod-Kolokation (Container Escape, Resource Exhaustion) ist gering und durch Resource Limits bereits mitigiert.
4. **PROD wird ein eigener Cluster** (ADR-004) — dort ist Node Affinity irrelevant, da keine Shared-Node-Situation entsteht.
5. **Technische Einschränkung**: Der aktuelle Node Pool (`devtest`) ist ein einzelner Pool mit 2 Nodes. Persistente Labels per Terraform erfordern **separate Node Pools** (einer für DEV, einer für TEST), was eine größere Infrastrukturänderung mit Kostenimpact wäre. Manuelle `kubectl label`-Labels überleben keine Node-Replacements (Scaling, Maintenance).

**Risikobewertung**: Gering. Der Kubernetes-Scheduler verteilt Pods natürlich über verfügbare Nodes (Bin-Packing). Bei ~3,5 CPU Requests pro Environment und ~7,9 CPU Allocatable pro Node ist eine einseitige Verteilung unwahrscheinlich. Selbst im Worst Case (alle Pods auf einem Node) greifen Namespace-Isolation und NetworkPolicies.

**Wiederaufnahme-Kriterium**: Nur relevant, falls VÖB-Audit explizit Node-Level-Isolation fordert oder falls ein dritter Tenant auf denselben Cluster kommt.

### SEC-04: Terraform Remote State — ZURÜCKGESTELLT (2026-03-08)

**Ursprüngliches Finding**: Terraform State liegt lokal mit Klartext-Passwörtern. Kein Backup, kein Audit-Trail.

**Entscheidung: Herabgestuft von P1 auf P3 (Nice-to-have).** Begründung:

1. **Solo-Entwickler** — kein Risiko durch Team-Kollisionen, kein State-Locking nötig (StackIT S3 bietet ohnehin kein DynamoDB-Äquivalent)
2. **FileVault aktiv** — volle Festplattenverschlüsselung auf dem Entwickler-Laptop, State ist at-rest verschlüsselt
3. **State ist gitignored** — `*.tfstate` und `*.tfstate.*` in `.gitignore`, kein Risiko eines versehentlichen Commits
4. **CI/CD nutzt kein Terraform** — nur Helm/kubectl. Terraform wird ausschließlich lokal ausgeführt
5. **PG ACL als Defense-in-Depth** — selbst bei Passwort-Leak ist DB-Zugang auf Cluster-Egress-IP + Admin-IP beschränkt
6. **Remote State löst das Problem nicht vollständig** — S3-Credentials für den Bucket-Zugriff müssten wiederum lokal gespeichert werden
7. **Kein BAIT/BSI-Requirement** — keine regulatorische Vorschrift für Remote IaC State

**Quick Win umgesetzt**: `chmod 600` auf alle State-Dateien (war `644` = world-readable).

**Kosten bei Umsetzung**: 0,03 EUR/Monat (StackIT Object Storage, reine GB-Abrechnung, kein Bucket-Grundpreis). Umsetzung ~2h, kann opportunistisch bei PROD-Vorbereitung erfolgen.

**Wiederaufnahme**: Bei Teamvergrößerung (mehrere Terraform-Operatoren) oder bei expliziter Audit-Anforderung.

### SEC-05: Separate Kubeconfigs — ZURÜCKGESTELLT (2026-03-08)

**Ursprüngliches Finding**: Ein globaler `STACKIT_KUBECONFIG` GitHub Secret für alle Environments. Kompromittierter DEV-Workflow kann TEST/PROD manipulieren.

**Entscheidung: Herabgestuft von P1 auf P3 (Nice-to-have).** Begründung:

1. **PROD wird ein eigener Cluster** (ADR-004) — separates Kubeconfig ergibt sich automatisch. Die Blast-Radius-Reduktion (das einzige starke Argument) ist architektonisch gelöst.
2. **Solo-Entwickler** — derselbe Operator deployt auf alle Environments. Namespace-scoped RBAC isoliert ihn vor sich selbst, was bei einem 1-Personen-Team keinen praktischen Nutzen hat.
3. **CI/CD ist bereits gehärtet** — SHA-gepinnte Actions, `permissions: contents: read`, Environment-gated Deploys (TEST/PROD nur per `workflow_dispatch`)
4. **Kein BAIT/BSI-Requirement** für Pre-Production — BAIT Kap. 8.6 (4-Augen-Prinzip) gilt explizit für Produktionsumgebung, nicht für DEV/TEST bei Solo-Dev
5. **DEV/TEST enthalten keine Kundendaten** — Worst Case (Cluster-Admin Leak auf DEV/TEST-Cluster) betrifft nur Testdaten

**Opportunistische Umsetzung**: Kann beim Kubeconfig-Renewal (Ablauf 2026-05-28) kostenneutral mitgemacht werden — neue ServiceAccounts + namespace-scoped RoleBindings statt erneuter Cluster-Admin-Kubeconfig.

### SEC-06: Container SecurityContext — P1 (vor PROD)

**Kritisches Finding (2026-03-08):** Analyse der Onyx Helm Chart Templates ergab, dass mehrere Komponenten mit `privileged: true` + `runAsUser: 0` laufen — die höchstmögliche Privilegierung. Ein privilegierter Container hat vollen Zugriff auf den Host-Kernel, Devices und kann Host-Filesysteme mounten.

**Betroffene Komponenten:**

| Komponente | Aktueller Zustand | Risiko |
|------------|-------------------|--------|
| Celery (alle 8 Worker) | `privileged: true`, `runAsUser: 0` | **HOCH** — Host-Kernel-Zugriff |
| Model Server (inference + index) | `privileged: true`, `runAsUser: 0` | **HOCH** — Host-Kernel-Zugriff |
| Vespa | `privileged: true`, `runAsUser: 0` (Chart überschreibt Subchart-Default) | **HOCH** — Host-Kernel-Zugriff |
| API Server | `runAsUser: 0` (Root, aber nicht privileged) | Mittel |
| Web Server (Next.js) | `USER nextjs` (UID 1001) | OK — bereits non-root |
| NGINX Ingress | `runAsNonRoot: true`, UID 101, no privilege escalation | OK — bereits gehärtet |

**BSI-Relevanz**: SYS.1.6.A10: "Privileged Mode SOLLTE NICHT verwendet werden." (SOLLTE = dringende Empfehlung). In einem Banking-Kontext würde dies als Finding in jedem Audit markiert.

**Geplante Umsetzung (Stufenplan):**
1. **Phase 1 (Quick Win, 1-2h):** `privileged: false` für Celery, Model Server, Vespa via `values-common.yaml`. `runAsUser: 0` erstmal beibehalten. Eliminiert das schlimmste Finding mit minimalem Risiko — `privileged` wird fast nie tatsächlich benötigt.
2. **Phase 2 (vor PROD, 4-6h):** `runAsUser: 1001` + `runAsNonRoot: true` für API, Celery, Model Server. `emptyDir` für `/tmp` wo nötig. Vespa als dokumentierte Ausnahme (Upstream-Limitation: benötigt ggf. Root für `vm.max_map_count`).
3. **Phase 3 (optional, vor Abnahme):** `readOnlyRootFilesystem: true` mit vollständigem emptyDir-Mapping. Diminishing Returns für den Aufwand.

**Technischer Hinweis**: Alle Onyx Chart Templates unterstützen `securityContext`-Overrides via Values (`{{- toYaml .Values.<component>.securityContext | nindent 12 }}`). Kein Chart-Umbau nötig — Änderungen ausschließlich in `values-common.yaml`.

### SEC-07: Encryption-at-Rest (ERLEDIGT)

**Verifiziert (2026-03-08)**: StackIT Managed Services bieten Encryption-at-Rest standardmäßig — nicht deaktivierbar.

- **PostgreSQL Flex**: Verschlüsselte SSD-Volumes (AES-256)
- **Object Storage**: Server-Side Encryption (SSE) als Default
- **Status**: Kein Handlungsbedarf, Verschlüsselung ist plattformseitig garantiert

---

## Incident Response

### Incident Classification

| Severity | Beispiele | Response Time |
|----------|----------|---------------|
| P1 (Critical) | Data Breach, vollständiger Ausfall | 15 Minuten |
| P2 (High) | Teilausfall, Security Misconfiguration | 1 Stunde |
| P3 (Medium) | API-Fehler, Performance-Probleme | 4 Stunden |
| P4 (Low) | Minor Bug, Feature Request | 24 Stunden |

### Incident Response Plan

```
Phase 1: ERKENNUNG
├─ Aktuell: Manuelle Erkennung (kein automatisiertes Monitoring)
├─ Geplant: Prometheus/Grafana Alerting (Phase M5)
└─ Smoke Tests in CI/CD (implementiert)

Phase 2: EINDÄMMUNG
├─ Betroffene Pods isolieren (kubectl)
├─ Namespace-Level: Helm Rollback (--atomic bei TEST/PROD)
└─ Datenbankebene: PG ACL kann auf [] gesetzt werden

Phase 3: UNTERSUCHUNG
├─ Pod-Logs (kubectl logs)
├─ Kubernetes Events (kubectl describe)
└─ Terraform State (Infrastruktur-Änderungen)

Phase 4: BEHEBUNG
├─ Patch entwickeln und testen
├─ Deployment über CI/CD-Pipeline
└─ Verifizierung über Smoke Tests

Phase 5: KOMMUNIKATION
├─ VÖB informieren (bei P1/P2)
├─ DSGVO-Meldepflicht prüfen (72h bei Datenschutzverletzung)
└─ Dokumentation im Changelog

Phase 6: NACHBEREITUNG
├─ Root Cause Analysis
├─ Runbook aktualisieren
└─ Security-Konzept aktualisieren
```

### Incident Contact List

| Rolle | Name | Kontakt |
|------|------|---------|
| Tech Lead / CCJ | Nikolaj Ivanov | [AUSSTEHEND -- Klärung mit VÖB] |
| VÖB IT / CISO | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] |
| StackIT Support | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] |

---

## Infrastruktur-Übersicht

### StackIT Cloud (Datensouveränität)

| Aspekt | Details |
|--------|---------|
| Provider | StackIT (Schwarz IT, Teil der Schwarz Gruppe) |
| Region | EU01 (Frankfurt am Main, Deutschland) |
| Datensouveränität | Daten verlassen Deutschland nicht |
| Rechenzentrum | Betrieben unter deutschem Recht |
| Container Registry | StackIT eigene Registry (`registry.onstackit.cloud`) |
| LLM-Verarbeitung | StackIT AI Model Serving (in-region) |

### Ressourcen-Übersicht

| Ressource | DEV | TEST | PROD (geplant) |
|-----------|-----|------|-----------------|
| SKE Cluster | Shared (`vob-chatbot`) | Shared (`vob-chatbot`) | Eigener Cluster |
| Node Pool | `devtest` (2 Nodes, g1a.8d) | `devtest` (shared) | Eigener Pool (2x g1a.8d) |
| PostgreSQL | Flex 2.4 Single (`vob-dev`) | Flex 2.4 Single (`vob-test`) | Flex 4.8 HA (3 Replicas) |
| Object Storage | `vob-dev` | `vob-test` | `vob-prod` |
| Namespace | `onyx-dev` | `onyx-test` | `onyx-prod` |

### Telemetrie

**DEAKTIVIERT**: Onyx-Telemetrie ist explizit ausgeschaltet:

```yaml
# values-common.yaml
configMap:
  DISABLE_TELEMETRY: "true"
```

---

## Referenzen

### Deutsche Regulatorische Standards

- **DSGVO**: https://dsgvo-gesetz.de/
- **BDSG**: https://www.gesetze-im-internet.de/bdsg_2018/
- **BSI-Grundschutz**: https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierungen/IT-Grundschutz/it-grundschutz_node.html
- **BAIT**: Bankaufsichtliche Anforderungen an die IT (BaFin)

### Sicherheits-Frameworks

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CIS Benchmarks für Kubernetes**: https://www.cisecurity.org/cis-benchmarks/

### Projekt-Dokumentation

- Implementierungsplan: `docs/referenz/stackit-implementierungsplan.md`
- Technische Referenz: `docs/referenz/stackit-infrastruktur.md`
- ADR-004 (Umgebungstrennung): `docs/adr/adr-004-umgebungstrennung-dev-test-prod.md`
- CI/CD Runbook: `docs/runbooks/ci-cd-pipeline.md`
- DNS/TLS-Runbook: `docs/runbooks/dns-tls-setup.md`
- LLM-Konfiguration Runbook: `docs/runbooks/llm-konfiguration.md`
- Entra ID Fragenkatalog: `docs/entra-id-kundenfragen.md`

---

## Nächste Schritte

### Vor PROD-Deployment (P1)

1. ~~**SEC-02**: Node Affinity erzwingen~~ → **ZURÜCKGESTELLT** (2026-03-08)
2. ~~**SEC-03**: Kubernetes NetworkPolicies implementieren~~ → **ERLEDIGT** (2026-03-05)
3. ~~**SEC-04**: Terraform Remote State~~ → **ZURÜCKGESTELLT** (2026-03-08, herabgestuft auf P3)
4. ~~**SEC-05**: Separate Kubeconfigs~~ → **ZURÜCKGESTELLT** (2026-03-08, herabgestuft auf P3)
5. **SEC-06**: Container SecurityContext — `privileged: true` entfernen (hochgestuft von P2 auf P1)
6. **M7**: Cluster-API-ACL (`cluster_acl`) von `0.0.0.0/0` auf Cluster-Egress-IP einschränken (analog SEC-01 für PG)
7. **TLS**: DNS-Einträge von VÖB IT, dann Let's Encrypt aktivieren
8. **Entra ID**: App Registration + Credentials von VÖB IT

### Vor VÖB-Abnahme (P2)

9. ~~**SEC-07**: Encryption-at-Rest bei StackIT verifizieren~~ → **ERLEDIGT** (2026-03-08, StackIT Default)
10. **SEC-06 Phase 2**: `runAsNonRoot: true` + `runAsUser: 1001` für alle Komponenten (außer Vespa)
11. **Penetration Test**: Externe Durchführung
12. **DSGVO-Assessment (C5)**: Datenschutz-Folgenabschätzung (DSFA), Auftragsverarbeitungsvertrag (AVV), Löschkonzept erstellen

### Opportunistisch (P3 — Nice-to-have)

13. **SEC-04**: Terraform Remote State (bei Teamvergrößerung oder Audit-Anforderung)
14. **SEC-05**: Separate Kubeconfigs (beim Kubeconfig-Renewal 2026-05-28)
15. **SEC-06 Phase 3**: `readOnlyRootFilesystem: true` (diminishing returns)
11. **BAIT-Compliance-Check (M2)**: Vollständige Prüfung gegen BAIT-Anforderungen, Lücken im Sicherheitskonzept schließen
12. **IP-Ownership (M3)**: In ADR-001 "CCJ oder VÖB" eindeutig klären

### Dokumentations-Finalisierung

13. Incident Contact List vervollständigen
14. Aufbewahrungsfristen mit VÖB definieren
15. Dieses Dokument auf Version 1.0 bringen (nach Umsetzung aller P1-Items)

---

**Dokumentstatus**: Entwurf (teilweise implementiert)
**Version**: 0.4
**Letzte Aktualisierung**: 2026-03-07
**Nächste Überprüfung**: 2026-04-03
