# Betriebskonzept -- VÖB Service Chatbot

**Dokumentstatus**: Entwurf (teilweise verifiziert)
**Letzte Aktualisierung**: 2026-03-07
**Version**: 0.5

---

## Einleitung und Geltungsbereich

Das Betriebskonzept beschreibt die operativen Anforderungen, Prozesse und Richtlinien für den Betrieb des VÖB Service Chatbot. Es umfasst die aktuell aktiven Umgebungen (DEV, TEST) sowie die geplante Produktionsumgebung.

**Basis-Software**: Enterprise-Fork von [Onyx](https://github.com/onyx-dot-app/onyx) (FOSS, MIT-Lizenz) mit Custom Extension Layer (`backend/ext/`, `web/src/ext/`).

### Zielgruppe
- Operations / DevOps Team (CCJ / Coffee Studios)
- Auftraggeber (VÖB Operations)
- Stakeholder und Führungskräfte

---

## Systemübersicht

### Architektur-Diagramm

```
┌───────────────────────────────────────────────────────────────────┐
│ Internet / Benutzer                                               │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ↓ HTTP (TLS geplant, aktuell noch nicht aktiv)

┌───────────────────────────────────────────────────────────────────┐
│ StackIT Cloud -- Region EU01 (Frankfurt)                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SKE Kubernetes Cluster "vob-chatbot"                        │ │
│  │ Node Pool "devtest": 2× g1a.8d (8 vCPU, 32 GB RAM)        │ │
│  │ Kubernetes 1.32, Flatcar OS                                 │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │ Namespace: onyx-dev (DEV)                             │  │ │
│  │  │ IngressClass: nginx                                   │  │ │
│  │  │ LoadBalancer IP: 188.34.74.187                        │  │ │
│  │  │                                                       │  │ │
│  │  │  Pods:                                                │  │ │
│  │  │  ├── onyx-dev-web-server       (Frontend, 1 Replica)  │  │ │
│  │  │  ├── onyx-dev-api-server       (Backend, 1 Replica)   │  │ │
│  │  │  ├── onyx-dev-celery-beat      (Scheduler, 1 Replica) │  │ │
│  │  │  ├── onyx-dev-celery-worker-primary (Worker, 1 Rep.)  │  │ │
│  │  │  ├── onyx-dev-celery-worker-light    (Worker, 1 Rep.)  │  │ │
│  │  │  ├── onyx-dev-celery-worker-heavy    (Worker, 1 Rep.)  │  │ │
│  │  │  ├── onyx-dev-celery-worker-docfetching  (Worker, 1 Rep.) │  │ │
│  │  │  ├── onyx-dev-celery-worker-docprocessing (Worker, 1 Rep.)│  │ │
│  │  │  ├── onyx-dev-celery-worker-monitoring   (Worker, 1 Rep.) │  │ │
│  │  │  ├── onyx-dev-celery-worker-user-file    (Worker, 1 Rep.) │  │ │
│  │  │  ├── onyx-dev-inference-model  (Model Server, 1 Rep.) │  │ │
│  │  │  ├── onyx-dev-indexing-model   (Model Server, 1 Rep.) │  │ │
│  │  │  ├── vespa                     (Vector Store, 1 Rep.) │  │ │
│  │  │  └── redis                     (Cache, 1 Replica)     │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │ Namespace: onyx-test (TEST)                           │  │ │
│  │  │ IngressClass: nginx-test                              │  │ │
│  │  │ LoadBalancer IP: 188.34.118.201                       │  │ │
│  │  │                                                       │  │ │
│  │  │  (Identische Pod-Struktur wie DEV, 15 Pods)                    │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│              ↓ Internal Networking                                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Managed PostgreSQL Flex (StackIT)                           │ │
│  │                                                             │ │
│  │  DEV: vob-dev (Flex 2.4 Single, 2 CPU, 4 GB, 20 GB SSD)  │ │
│  │  TEST: vob-test (Flex 2.4 Single, 2 CPU, 4 GB, 20 GB SSD)│ │
│  │  PostgreSQL Version: 16                                     │ │
│  │  Backup: DEV täglich 02:00 UTC, TEST täglich 03:00 UTC (managed) │ │
│  │  ACL: Cluster-Egress-IP 188.34.93.194/32 + Admin           │ │
│  │  Users: onyx_app (RW), db_readonly_user (RO)               │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ StackIT Object Storage (S3-kompatibel)                     │ │
│  │                                                             │ │
│  │  Buckets:                                                   │ │
│  │  - vob-dev (DEV File Store)                                │ │
│  │  - vob-test (TEST File Store)                              │ │
│  │  Endpoint: object.storage.eu01.onstackit.cloud             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ StackIT AI Model Serving (LLM)                             │ │
│  │                                                             │ │
│  │  DEV: GPT-OSS 120B + Qwen3-VL 235B (konfiguriert)         │ │
│  │  TEST: GPT-OSS 120B + Qwen3-VL 235B (konfiguriert seit 2026-03-03) │ │
│  │  Embedding: nomic-embed-text-v1 (self-hosted, aktiv).         │ │
│  │    Ziel: Qwen3-VL-Embedding 8B (Blocker aufgehoben, Upstream PR #9005)│ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ StackIT Container Registry                                 │ │
│  │                                                             │ │
│  │  Projekt: voeb-chatbot                                     │ │
│  │  Images: onyx-backend, onyx-web-server                     │ │
│  │  Registry: registry.onstackit.cloud                        │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Komponenten-Übersicht

| Komponente | Technologie | Zweck | Replicas (DEV/TEST) |
|-----------|------------|-------|---------------------|
| Frontend (Web Server) | Next.js 16, React 19, TypeScript | Web UI | 1 |
| Backend (API Server) | Python 3.11, FastAPI 0.133.1, SQLAlchemy 2.0, Pydantic 2.11 | REST API | 1 |
| Background Worker | Celery 5.5 (Standard Mode, 8 separate Worker) | Async Tasks, Indexing | 7 Worker + 1 Beat |
| Model Server | Onyx Model Server v2.9.8 (Docker Hub Upstream) | Embedding, Inference | 2 (Index + Inference) |
| Vespa | Vespa 8.609.39 (In-Cluster) | RAG + Vector Store | 1 |
| Redis | Redis 7.0.15 (In-Cluster, OT Operator) | Cache, Celery Broker | 1 |
| PostgreSQL | StackIT Managed Flex 2.4 (Extern) | Relationale Daten | Managed (Single) |
| Object Storage | StackIT S3-kompatibel (Extern) | File Store | Managed |
| LLM | StackIT AI Model Serving | Chat, RAG | Managed |
| Ingress | NGINX Ingress Controller | Load Balancing, Routing | 1 pro Namespace |

### Umgebungen

| Umgebung | Namespace | IP | IngressClass | Status |
|----------|-----------|-----|-------------|--------|
| DEV | `onyx-dev` | `188.34.74.187` | `nginx` | LIVE seit 2026-02-27 |
| TEST | `onyx-test` | `188.34.118.201` | `nginx-test` | LIVE seit 2026-03-03 |
| PROD | `onyx-prod` (geplant) | -- | -- | Geplant (eigener Cluster) |

**Hinweis**: DEV und TEST teilen sich denselben SKE-Cluster mit einem Node Pool (`devtest`, 2 Nodes). PROD wird laut ADR-004 auf einem separaten Cluster betrieben.

---

## Tech-Stack

### Backend
- **Sprache**: Python 3.11
- **Framework**: FastAPI 0.133.1
- **ORM**: SQLAlchemy 2.0.15
- **Migrations**: Alembic 1.10.4
- **Validation**: Pydantic 2.11
- **Task Queue**: Celery 5.5.1
- **LLM Integration**: LiteLLM 1.81.6
- **Dependency Management**: uv (Requirements exportiert nach `backend/requirements/`)

### Frontend
- **Framework**: Next.js 16.1.6
- **UI Library**: React 19.2.4
- **Sprache**: TypeScript 5.9
- **Styling**: Tailwind CSS 3.4
- **State Management**: Zustand 5.0, SWR 2.1
- **Testing**: Jest 29, Playwright

### Infrastructure as Code
- **Terraform**: StackIT Provider ~> 0.80
- **Helm**: v3.16.0 (Onyx Chart READ-ONLY + Value-Overlays)
- **CI/CD**: GitHub Actions

---

## Deployment-Prozess

### CI/CD Pipeline

Die Pipeline ist in `.github/workflows/stackit-deploy.yml` definiert und seit Run #5 produktionsreif verifiziert.

```
Git Push auf "main"
  ↓
GitHub Actions Workflow (automatisch)
  ├── Prepare: Image Tag bestimmen (Git SHA)
  ├── Build Backend (parallel, je ~7 Min mit Cache)
  │   └── Push: registry.onstackit.cloud/voeb-chatbot/onyx-backend:<sha>
  ├── Build Frontend (parallel, je ~7 Min mit Cache)
  │   └── Push: registry.onstackit.cloud/voeb-chatbot/onyx-web-server:<sha>
  └── Deploy DEV
      ├── helm dependency build
      ├── helm upgrade --install onyx-dev
      │   -f values-common.yaml -f values-dev.yaml
      │   --set Secrets (PG, Redis, S3, DB_READONLY)
      ├── kubectl patch: Recreate-Strategie (Single-Node)
      ├── kubectl rollout status (alle 12 Deployments)
      └── Smoke Test: curl ${WEB_DOMAIN}/api/health

Manuell (workflow_dispatch):
  ├── Environment wählbar: dev / test / prod
  ├── TEST: --atomic (automatischer Rollback bei Fehler)
  └── PROD: Required Reviewers in GitHub Environment
```

**Wichtige Details**:
- Model Server wird NICHT gebaut -- Upstream-Image `onyxdotapp/onyx-model-server:v2.9.8` von Docker Hub
- Secrets werden per `--set` aus GitHub Environment Secrets injiziert (nie in Git)
- Concurrency: Nur ein Deploy pro Environment gleichzeitig, laufende Builds werden bei neuem Push abgebrochen
- DEV-Deploy patcht Deployments auf Recreate-Strategie (beibehalten zur Vermeidung von Port-Konflikten, g1a.8d haette genug CPU fuer RollingUpdate)
- Alle GitHub Actions sind SHA-gepinnt (Supply-Chain-Sicherheit)

### CI/CD-Details

#### Trigger und paths-ignore

Der Workflow wird **nicht** ausgelöst bei Änderungen an:
- `docs/**` -- reine Dokumentationsänderungen
- `*.md` -- Markdown-Dateien im Root
- `.claude/**` -- AI-Instruktionsdateien

Dadurch erzeugen Docs-only Commits kein unnötiges Build+Deploy. Code-Änderungen an `main` triggern immer einen DEV-Deploy.

#### Concurrency-Verhalten

```yaml
concurrency:
  group: deploy-${{ github.event.inputs.environment || 'dev' }}
  cancel-in-progress: true
```

- Pro Environment (dev/test/prod) läuft maximal **ein** Deploy gleichzeitig
- Ein neuer Push auf `main` bricht einen laufenden DEV-Deploy ab und startet den neueren
- TEST- und PROD-Deploys (manuell) haben eigene Concurrency-Gruppen und beeinflussen DEV nicht

#### Supply-Chain-Sicherheit (SHA-Pinning)

Alle GitHub Actions sind auf **Commit-SHA fixiert** statt auf Major-Version-Tags (z.B. `v4`). Dies verhindert Supply-Chain-Angriffe, bei denen ein kompromittiertes Action-Repository ein Tag auf einen schadhaften Commit umbiegt.

```
actions/checkout@34e114876b...            # v4
docker/login-action@c94ce9fb46...         # v3
docker/setup-buildx-action@8d2750c6...    # v3
docker/build-push-action@10e90e36...      # v6
azure/setup-helm@bf6a7d304b...            # v4
azure/setup-kubectl@c0c8b32d33...         # v4
```

Die Pipeline hat `permissions: contents: read` -- minimales Privilege, nur Lesezugriff auf das Repository.

#### Smoke Test pro Environment

Nach jedem Deploy wird ein Health Check gegen `/api/health` ausgeführt:

| Environment | Versuche | Interval | Timeout | Gesamt |
|-------------|----------|----------|---------|--------|
| DEV | 12 | 10s | 5s pro Request | ~2 Min |
| TEST | 12 | 10s | 5s pro Request | ~2 Min |
| PROD | 18 | 10s | 5s pro Request | ~3 Min |

PROD hat mehr Versuche, da HA-Deployments (mehrere Replicas) länger zum Starten brauchen können. Die Domain wird dynamisch aus der Kubernetes ConfigMap `env-configmap` gelesen.

#### Model Server Pinning

Der Model Server (`onyxdotapp/onyx-model-server`) wird **nicht** von uns gebaut. Er ist identisch mit dem Upstream Onyx Image und wird direkt von Docker Hub gepullt.

- Gepinnt auf Version `v2.9.8` (kein `:latest`)
- Definiert als Environment-Variable im Workflow (zentral änderbar)
- Für PROD: Evaluierung ob das Image in die StackIT Registry gespiegelt wird (Datensouveränität)

#### Secret-Injection

Secrets werden **nie** in Git gespeichert. Der Injektionspfad:

```
GitHub Environment Secrets (verschlüsselt, pro Environment getrennt)
  ↓ CI/CD Pipeline liest Secrets zur Laufzeit
    ↓ helm upgrade --set "auth.postgresql.values.password=${{ secrets.POSTGRES_PASSWORD }}"
      ↓ Helm erstellt Kubernetes Secrets (Base64-encoded)
        ↓ Pods mounten Secrets als Environment-Variablen
```

**Verwaltete Secrets pro Environment**:

| Secret | Verwendung |
|--------|-----------|
| `POSTGRES_PASSWORD` | PostgreSQL App-User Passwort |
| `REDIS_PASSWORD` | Redis Standalone Passwort |
| `S3_ACCESS_KEY_ID` | StackIT Object Storage Access Key |
| `S3_SECRET_ACCESS_KEY` | StackIT Object Storage Secret Key |
| `DB_READONLY_PASSWORD` | PostgreSQL Readonly-User (Knowledge Graph) |

**Globale Secrets** (Repository-weit, nicht Environment-spezifisch):

| Secret | Verwendung |
|--------|-----------|
| `STACKIT_REGISTRY_USER` | Container Registry Robot Account |
| `STACKIT_REGISTRY_PASSWORD` | Container Registry Token |
| `STACKIT_KUBECONFIG` | Base64-encoded Kubeconfig (Ablauf: 2026-05-28) |

### Helm-basiertes Deployment

```
deployment/helm/
├── charts/onyx/                   ← Onyx Helm Chart (READ-ONLY, nicht verändern!)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
└── values/
    ├── values-common.yaml         ← Gemeinsam: PG aus, MinIO aus, Vespa+Redis an
    ├── values-dev.yaml            ← DEV: 1 Replica, 8 Celery-Worker (Standard Mode), eigene PG+S3
    └── values-test.yaml           ← TEST: Analog DEV, eigene PG+S3+IngressClass
```

**Deployment-Kommandos** (manuell, falls nötig):

```bash
# DEV
helm upgrade --install onyx-dev deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml

# TEST
helm upgrade --install onyx-test deployment/helm/charts/onyx \
  --namespace onyx-test \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-test.yaml
```

**Hinweis**: Vor jedem manuellen Helm-Deploy muss `helm dependency build deployment/helm/charts/onyx` ausgeführt werden. Die Subchart-`.tgz`-Dateien sind gitignored.

### Rollback-Strategie

**Szenarien**:

1. **Fehlerhaftes Deployment (TEST/PROD)**
   - TEST-Deploys nutzen `--atomic`: Helm rollt bei Fehler automatisch zurück
   - PROD-Deploys nutzen ebenfalls `--atomic` + Required Reviewers
   - Manueller Rollback: `helm rollback onyx-{env} -n onyx-{env}`

2. **Fehlerhaftes Deployment (DEV)**
   - DEV nutzt kein `--atomic` (bewusste Entscheidung für Debug-Möglichkeit)
   - Manueller Rollback: `helm rollback onyx-dev -n onyx-dev`
   - Helm History: Maximal 5 Revisionen (`--history-max 5`)

3. **Datenbankmigrationen**
   - Alembic-Migrationen werden vom API-Server beim Start ausgeführt
   - Vor kritischen Migrationen: PG-Backup verifizieren (managed, DEV 02:00 UTC, TEST 03:00 UTC)
   - Reverse-Migration: `alembic downgrade -1`

---

## Change Management

### Branching-Strategie

Das Projekt nutzt **Simplified GitLab Flow** -- ein einziger langlebiger Branch (`main`) mit Feature- und Release-Branches.

```
feature/*  →  PR  →  main  →  auto-deploy DEV
                       │
                       └→  release/X.Y  →  workflow_dispatch  →  TEST
                                │
                                └→  tag vX.Y.Z  →  workflow_dispatch  →  PROD
                                │
                                └→  merge back  →  main
```

**Branch-Typen**:

| Branch | Zweck | Lebensdauer |
|--------|-------|-------------|
| `main` | Integrationsbranch, auto-deploy DEV, Upstream-Merges | Permanent |
| `feature/*` | Feature-Entwicklung, Bugfixes, Doku | Temporär (bis PR gemergt) |
| `release/*` | Release-Stabilisierung für TEST/PROD | Temporär (bis zurück in main gemergt) |
| `hotfix/*` | Dringende Fixes auf Release-Branch | Temporär (Stunden bis Tage) |

### Promotion-Pfad

Jede Änderung durchläuft folgende Stufen:

```
Entwicklung (Feature-Branch)
  → Pull Request (Code Review, CI muss grün sein)
    → Merge auf main
      → Automatischer Deploy auf DEV
        → Manueller Deploy auf TEST (workflow_dispatch)
          → Manueller Deploy auf PROD (workflow_dispatch + Approval)
```

### Änderungskategorien

| Kategorie | Beschreibung | Beispiele | Prozess |
|-----------|-------------|-----------|---------|
| **Standard Change** | Geplante Feature-Entwicklung | Neues Modul, UI-Änderung, Doku | Feature-Branch → PR → main → DEV → TEST → PROD |
| **Emergency Change** | Dringender Fix für Produktionsproblem | Security Patch, Crash Fix | Hotfix-Branch → PR → Release-Branch + main |
| **Upstream-Merge** | Update von Onyx FOSS | Quarterly oder bei Security Updates | Feature-Branch → Test-Merge → PR → main |
| **Infrastruktur-Change** | Terraform, Helm Values, CI/CD | Node-Skalierung, neue Secrets | Feature-Branch → PR → main → Deploy |

### Freigabestufen pro Environment

| Environment | Trigger | Freigabe | Rollback | Helm Timeout |
|-------------|---------|----------|----------|-------------|
| **DEV** | Automatisch bei Push auf `main` | Keine manuelle Freigabe nötig | `helm rollback` (manuell) | 10 Min |
| **TEST** | Manuell (`workflow_dispatch`) | Tech Lead triggert Deploy | `--atomic` (automatisch bei Fehler) | 10 Min |
| **PROD** | Manuell (`workflow_dispatch`) | Tech Lead + Required Reviewer (GitHub Environment Protection) | `--atomic` (automatisch bei Fehler) | 15 Min |

### Dokumentation von Änderungen

Jede Änderung wird an folgenden Stellen dokumentiert:

1. **Git Commit**: Konventionelles Format `<type>(<scope>): <Beschreibung>` mit Bullet-Liste im Body
2. **Pull Request**: Titel + Beschreibung der Änderung, verlinkte Issues
3. **CHANGELOG.md**: Eintrag unter `[Unreleased]` mit Kategorie (Added, Changed, Fixed, Security)
4. **Modulspezifikation**: Bei Abweichung von der Spezifikation wird diese aktualisiert

### 4-Augen-Prinzip (BAIT Kap. 8.6)

**BAIT-Anforderung**: Keine Änderung an der Produktionsumgebung ohne dokumentierte zweite Freigabe.

**Aktueller Stand** (1-Person-Entwicklungsteam):

| Maßnahme | Status | Details |
|----------|--------|---------|
| Pull Request Pflicht | IMPLEMENTIERT | Jede Änderung läuft über Feature-Branch + PR |
| Self-Review + PR-Checkliste | IMPLEMENTIERT | Checkliste vor jedem Commit (Tests, Lint, Types, Docs) |
| Branch Protection (`main`) | IMPLEMENTIERT (2026-03-06) | PR required, 1 Review, 3 Required Status Checks (helm-validate, build-backend, build-frontend) |
| Environment Protection (`prod`) | GEPLANT | Required Reviewers in GitHub Environment Settings |

**Interims-Lösung** (bis zweiter Reviewer verfügbar):
- Tech Lead führt dokumentiertes Self-Review durch (PR-Beschreibung + Checkliste)
- Commit-Freigabe erfolgt explizit durch Tech Lead nach lokaler Prüfung
- Kein Self-Merge auf `main` ohne vorherige Checkliste

**Langfristig**: VÖB-Stakeholder oder zweiter CCJ-Mitarbeiter als Required Reviewer für das GitHub Environment `prod`.

---

## Release Management

### Release-Planung

Releases sind an Projektmeilensteine (M1-M6) gebunden. Jeder Meilenstein erzeugt einen Release-Branch, der durch TEST und PROD promoviert wird.

### Versionierung

**Semantic Versioning** (SemVer): `Major.Minor.Patch`

| Segment | Wann inkrementieren | Beispiel |
|---------|---------------------|---------|
| **Major** | Breaking Changes, große Architekturänderungen | `2.0.0` |
| **Minor** | Neues Feature, neuer Meilenstein | `1.1.0` |
| **Patch** | Bugfix, Security Patch | `1.0.1` |

**Nomenklatur**:
- Release-Branch: `release/X.Y` (z.B. `release/1.0`)
- Git Tag: `vX.Y.Z` (z.B. `v1.0.0`)
- Erster Release (M1 Infrastruktur): `v1.0.0`

### Release-Checkliste

Vor jedem Release-Deploy auf TEST/PROD:

| # | Schritt | Verantwortlich | Prüfung |
|---|---------|---------------|---------|
| 1 | DEV stabil: Smoke Tests grün, keine offenen P0/P1 Bugs | Tech Lead | CI/CD Pipeline grün |
| 2 | Release-Branch von `main` schneiden | Tech Lead | `git checkout -b release/X.Y` |
| 3 | TEST-Deploy + Validierung | Tech Lead | `gh workflow run stackit-deploy.yml -f environment=test --ref release/X.Y` |
| 4 | UAT (User Acceptance Testing) durch VÖB | VÖB | Falls für Meilenstein erforderlich |
| 5 | Bugfixes auf Release-Branch, Cherry-Pick zurück nach `main` | Tech Lead | `git cherry-pick <fix-commit>` auf `main` |
| 6 | Git Tag setzen | Tech Lead | `git tag -a vX.Y.Z -m "Release vX.Y.Z — Meilenstein"` |
| 7 | PROD-Deploy | Tech Lead + Reviewer | `gh workflow run stackit-deploy.yml -f environment=prod --ref release/X.Y` |
| 8 | Release-Branch zurück nach `main` mergen | Tech Lead | `git checkout main && git merge release/X.Y` |
| 9 | CHANGELOG.md aktualisieren | Tech Lead | `[Unreleased]` → `[vX.Y.Z]` |
| 10 | Abnahmeprotokoll ausfüllen | Tech Lead + VÖB | `docs/abnahme/` |

### Hotfix-Prozess

Für dringende Fixes auf einer bereits released Version:

```
1. Hotfix-Branch von release/* erstellen
   git checkout release/X.Y
   git checkout -b hotfix/beschreibung

2. Fix implementieren + testen

3. PR gegen release/* Branch
   gh pr create --base release/X.Y

4. Nach Merge: Neuen Patch-Tag setzen (Z inkrementieren)
   git tag -a vX.Y.(Z+1) -m "Hotfix: Beschreibung"
   # Beispiel: v1.0.0 → v1.0.1

5. PROD-Deploy (workflow_dispatch)

6. Cherry-Pick nach main
   git checkout main
   git cherry-pick <fix-commit>
```

### Release-Historie

| Version | Meilenstein | Datum | Inhalt |
|---------|-------------|-------|--------|
| v1.0.0 | M1 Infrastruktur | Geplant | DEV+TEST live, CI/CD, Security Baseline |

---

## Monitoring und Alerting

### Aktueller Stand

**Aktuell ist kein dediziertes Monitoring-Stack (Prometheus/Grafana/AlertManager) im Einsatz.** Die Überwachung erfolgt über:

1. **CI/CD Smoke Tests**: Jeder Deploy prüft `/api/health` (DEV/TEST: 12 Versuche à 10s = 120s, PROD: 18 Versuche à 10s = 180s)
2. **Kubernetes-native Prüfungen**: `kubectl get pods`, `kubectl describe`, `kubectl logs`
3. **Helm Status**: `helm status onyx-{env} -n onyx-{env}`
4. **StackIT Console**: Managed-Service-Metriken für PostgreSQL und Object Storage

### Health Checks (Kubernetes)

Die Health Checks sind im Onyx Helm Chart definiert. Der API-Server exponiert:

- **Health Endpoint**: `GET /api/health` -- geprüft durch CI/CD Smoke Test nach jedem Deploy
- **Liveness/Readiness Probes**: Konfiguriert im Helm Chart (Templates, READ-ONLY)

### Geplanter Monitoring-Ausbau

[AUSSTEHEND -- Vor PROD-Go-Live zu implementieren]

Der Monitoring-Ausbau ist für die PROD-Vorbereitung geplant und umfasst:

| Thema | Geplante Lösung | Priorität |
|-------|----------------|-----------|
| Metriken | Prometheus + Grafana | Vor PROD |
| Alerting | AlertManager oder StackIT-native Lösung | Vor PROD |
| Log-Aggregation | Zu evaluieren (ELK, Loki, StackIT-nativ) | Vor PROD |
| Uptime-Monitoring | Zu evaluieren | Vor PROD |

**Empfohlene Metriken für PROD** (noch nicht implementiert):

| Metrik | Schwellwert | Aktion |
|--------|------------|--------|
| Pod Restart Count | > 0 in 5 Min | Alert |
| Memory/CPU Usage | > 80% | Investigate |
| API Error Rate | > 1% | Alert |
| Database Connections | Pool-Limit nahend | Alert |
| Disk Usage | > 85% | Alert |

---

## Backup und Recovery

### Backup-Strategie

#### PostgreSQL (Managed)
- **Anbieter**: StackIT Managed PostgreSQL Flex
- **Automatische Backups**:
  - DEV: Täglich um 02:00 UTC (konfiguriert per Terraform: `pg_backup_schedule = "0 2 * * *"`)
  - TEST: Täglich um 03:00 UTC (1h nach DEV, kein Overlap: `pg_backup_schedule = "0 3 * * *"`)
- **Retention**: Managed durch StackIT (Details in StackIT-Dokumentation)
- **PITR (Point-in-Time Recovery)**: Abhängig vom StackIT Flex Tier
- **Lifecycle Protection**: `prevent_destroy = true` in Terraform

#### Object Storage
- **Anbieter**: StackIT Object Storage (S3-kompatibel)
- **Replikation**: Managed durch StackIT
- **Buckets**: `vob-dev`, `vob-test` (jeweils für File Store)

#### Applikation
- **Code**: Git Repository (GitHub)
- **Konfiguration**: Helm Values in Git, Secrets in GitHub Environments
- **Infrastruktur**: Terraform State (lokal, Remote-Backend vorbereitet)
- **Vespa-Daten**: Persistent Volumes (20 GB pro Umgebung), kein separates Backup

#### Redis
- **Kein Backup**: Redis dient als Cache und Celery Broker. Datenverlust hat keine Auswirkung auf persistente Daten.

### RTO/RPO Targets

[AUSSTEHEND -- Klärung mit VÖB für PROD-SLAs]

| Szenario | RTO (Recovery Time) | RPO (Data Loss) | Anmerkung |
|----------|---------------------|------------------|-----------|
| Einzelner Pod Fehler | 1-2 Min | 0 (stateless) | Kubernetes Restart |
| Helm Rollback | ~5 Min | 0 | `helm rollback` |
| PostgreSQL Restore | Abhängig von StackIT | Bis letztes Backup | Managed Service |
| Cluster-Neuaufbau | Stunden | Bis letztes PG-Backup | Terraform + Helm |

### Disaster Recovery Prozess

1. **Detection**: CI/CD Smoke Test schlägt fehl / manuelle Meldung
2. **Assessment**: `kubectl get pods`, `helm status`, StackIT Console prüfen
3. **Recovery**:
   - Pod-Fehler: Kubernetes-Restart oder `kubectl delete pod`
   - Deployment-Fehler: `helm rollback`
   - Datenbank-Fehler: StackIT Support kontaktieren (Managed Restore)
   - Cluster-Fehler: Terraform + Helm Re-Deploy (Runbooks folgen)
4. **Validation**: Health Check, funktionale Prüfung
5. **Notification**: VÖB informieren
6. **Post-Incident**: Root Cause Analysis dokumentieren

---

## Update-Prozess

### Upstream Merges (Onyx Updates)

**Frequenz**: Jeden Quarter oder bei kritischen Security Updates

**Prozess**:

```
1. Fetch Upstream
   git fetch upstream main

2. Create Branch
   git checkout -b feature/upstream-merge-vX.Y.Z

3. Merge
   git merge upstream/main

4. Resolve Conflicts
   - Konflikte NUR in 7 Core-Dateien erwartet
   - Upstream übernehmen, dann Patches aus _core_originals/ neu anwenden
   - Andere Konflikte = Fork-Regeln wurden verletzt

5. Test
   - Full Test Suite lokal
   - Deploy auf TEST
   - Funktionale Prüfung

6. Deploy to Production
   - workflow_dispatch mit environment=prod
   - Required Reviewers Approval
```

**Warum "Extend, don't modify" funktioniert**: Max. 7 vorhersagbare Merge-Konflikte. Der `ext/`-Code existiert nicht in Upstream und erzeugt keine Konflikte.

### Extension Updates

**Prozess**: Standard Git Workflow
1. Feature Branch (`feature/{modulname}`)
2. Implementierung in `backend/ext/` und/oder `web/src/ext/`
3. Tests + Code Review
4. Merge auf `main`
5. Automatischer Deploy auf DEV (Push-Trigger)
6. Manueller Deploy auf TEST (workflow_dispatch)
7. Manueller Deploy auf PROD (workflow_dispatch + Approval)

### Database Migrations

**Strategie**: Alembic-Migrationen werden beim API-Server-Start automatisch ausgeführt.

- **Onyx-Migrationen**: `backend/alembic/` (READ-ONLY, kommen mit Upstream-Merges)
- **Extension-Migrationen**: `backend/ext/migrations/` (eigener Alembic-Branch)
- **Managed-PG-Einschränkung**: StackIT Flex erlaubt kein `CREATEROLE` -- spezielle User (z.B. `db_readonly_user`) werden per Terraform angelegt

---

## Skalierung

### Aktuelle Konfiguration (DEV/TEST)

| Komponente | Requests | Limits |
|-----------|----------|--------|
| API Server | 250m CPU, 512Mi RAM | 500m CPU, 1Gi RAM |
| Web Server | 100m CPU, 256Mi RAM | 250m CPU, 512Mi RAM |
| Celery Primary | 250m CPU, 512Mi RAM | 500m CPU, 1Gi RAM |
| Celery Beat | 100m CPU, 256Mi RAM | 250m CPU, 512Mi RAM |
| Model Server (je) | 250m CPU, 768Mi RAM | 1000m CPU, 2Gi RAM |
| Vespa | 500m CPU, 2Gi RAM | 1500m CPU, 4Gi RAM |
| Redis | 100m CPU, 128Mi RAM | 250m CPU, 256Mi RAM |

### Skalierungsstrategie

**DEV/TEST**: Keine Autoskalierung. 1 Replica pro Service. Standard Celery Mode (8 separate Worker).

**PROD (geplant)**:

[AUSSTEHEND -- PROD-Sizing nach Lastprofil]

- Eigener SKE-Cluster (ADR-004)
- Mehrere Replicas für API Server und Web Server
- Separate Celery Worker (kein Lightweight Mode) — **Erledigt (2026-03-06):** Standard Mode (Lightweight durch Upstream PR #9014 entfernt).
- Größere Node Types oder mehr Nodes
- HPA (HorizontalPodAutoscaler) nach Bedarf

### Vertikale Skalierung

- **Kubernetes Nodes**: g1a.8d (8 vCPU, 32 GB) ist aktuelle Konfiguration (seit 2026-03-06, ADR-005).
- **PostgreSQL**: Flex 2.4 (2 CPU, 4 GB). Upgrade auf größeres Flavor oder HA (3 Replicas) per Terraform.

---

## Wartungsfenster

### Kubernetes Cluster Maintenance (Managed)

Das SKE-Cluster hat ein automatisches Wartungsfenster (konfiguriert per Terraform):

```
Zeitfenster: 02:00-04:00 UTC (täglich, managed durch StackIT)
Inhalt: Kubernetes-Version-Updates, Machine-Image-Updates
```

### Geplante Wartungen

[AUSSTEHEND -- Klärung mit VÖB]

| Zeitfenster | Frequenz | Aktivitäten |
|---|---|---|
| [Zu vereinbaren] | Wöchentlich | Patch Management, Security Updates |
| [Zu vereinbaren] | Monatlich | Major Updates, Upstream Merges |

**Benachrichtigungsprozess**: [AUSSTEHEND -- Klärung mit VÖB]

---

## Incident Management

### Severity Levels

| Level | Auswirkung | Response Time | Resolution Target |
|-------|-----------|---|---|
| P1 (Critical) | Produktionssystem down | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] |
| P2 (High) | Funktionalität beeinträchtigt | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] |
| P3 (Medium) | Geringer Impact, Workaround existiert | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] |
| P4 (Low) | Kosmetisches Problem, kein Impact | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] |

### Eskalationspfade

[AUSSTEHEND -- Klärung mit VÖB]

```
Incident Detection (Smoke Test fehlgeschlagen / manuelle Meldung)
  ↓
Tech Lead (CCJ) informiert
  ↓
Assessment + Fix
  ↓
Bei P1/P2: VÖB Operations informieren
  ↓
Post-Incident: Root Cause Analysis
```

### Incident Log Template

```markdown
# Incident: [Titel]

## Timeline
- **YYYY-MM-DD HH:MM UTC**: Incident erkannt
- **YYYY-MM-DD HH:MM UTC**: Assessment begonnen
- **YYYY-MM-DD HH:MM UTC**: Root Cause identifiziert
- **YYYY-MM-DD HH:MM UTC**: Fix deployt
- **YYYY-MM-DD HH:MM UTC**: Service wiederhergestellt

## Root Cause
[Analyse]

## Mitigation
[Was wurde getan]

## Prevention
[Was verhindert Wiederholung]
```

---

## SLA-Definitionen

[AUSSTEHEND -- Abhängig von Vereinbarung mit VÖB]

SLAs, Verfügbarkeitsziele und Reaktionszeiten müssen mit VÖB abgestimmt werden. Folgende Punkte sind zu klären:

- Verfügbarkeitsziel (z.B. 99.5%, 99.9%)
- Response Times pro Severity Level
- Geplante vs. ungeplante Downtime
- Ausnahmen (Wartungsfenster, externe Abhängigkeiten)
- Berichtspflichten

### Externe Abhängigkeiten (nicht unter unserer Kontrolle)

| Abhängigkeit | Anbieter | Auswirkung bei Ausfall |
|-------------|----------|----------------------|
| PostgreSQL Flex | StackIT Managed | Kein DB-Zugriff |
| Object Storage | StackIT Managed | Kein File-Upload/-Download |
| SKE Cluster | StackIT Managed | Kein Betrieb |
| AI Model Serving | StackIT Managed | Keine LLM-Antworten |
| Container Registry | StackIT | Kein Image Pull (laufende Pods nicht betroffen) |
| Microsoft Entra ID | Microsoft (geplant, Phase 3) | Kein Login |

---

## Kontaktliste

[AUSSTEHEND -- Klärung mit VÖB]

| Rolle | Name | Kontakt | Notizen |
|-------|------|---------|---------|
| **Tech Lead (CCJ)** | Nikolaj Ivanov | [AUSSTEHEND -- Klärung mit VÖB] | Geschäftszeiten |
| **StackIT Support** | -- | [AUSSTEHEND -- Klärung mit VÖB] | Managed Services |
| **VÖB Operations Lead** | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] | |
| **VÖB CISO** | [AUSSTEHEND -- Klärung mit VÖB] | [AUSSTEHEND -- Klärung mit VÖB] | Security Incidents |

---

## Sicherheitsrelevante Betriebsaspekte

### Netzwerk-ACLs

| Ressource | ACL | Status |
|-----------|-----|--------|
| PostgreSQL Flex (DEV + TEST) | Cluster-Egress-IP `188.34.93.194/32` + Admin | SEC-01 umgesetzt |
| SKE Cluster API | Offen (`0.0.0.0/0`) | OPS-01 geplant (vor PROD) |

### Secrets Management

- **GitHub Environments**: `dev` und `test` mit je 5 Secrets (POSTGRES_PASSWORD, REDIS_PASSWORD, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, DB_READONLY_PASSWORD)
- **Globale Secrets**: STACKIT_REGISTRY_USER, STACKIT_REGISTRY_PASSWORD, STACKIT_KUBECONFIG
- **Kubeconfig-Ablauf**: 2026-05-28 -- Erneuerung einplanen
- **Kubernetes Secrets**: `onyx-postgresql`, `onyx-redis`, `onyx-dbreadonly`, `onyx-objectstorage`, `stackit-registry` (pro Namespace)

### Security-Audit Findings (SEC-01 bis SEC-07)

> Autoritative Quelle: `docs/sicherheitskonzept.md`. Priorisierung: P0 = vor TEST, P1 = vor PROD, P2 = vor VÖB-Abnahme.

| ID | Finding | Priorität | Status |
|----|---------|-----------|--------|
| SEC-01 | PostgreSQL ACL auf Cluster-Egress-IP einschränken | P0 | Umgesetzt |
| SEC-02 | Node Affinity erzwingen (DEV/TEST auf eigenen Nodes) | P1 | Vor PROD |
| SEC-03 | Kubernetes NetworkPolicies (Namespace-Isolation) | P1 | **Umgesetzt** (2026-03-05) |
| SEC-04 | Terraform Remote State (Secrets im Klartext lokal) | P1 | Vor PROD |
| SEC-05 | Separate Kubeconfigs pro Environment (RBAC) | P1 | Vor PROD |
| SEC-06 | Container SecurityContext (runAsNonRoot etc.) | P2 | Vor Abnahme |
| SEC-07 | Encryption-at-Rest verifizieren (PG, S3, Volumes) | P2 | Vor Abnahme |

### Betriebsmaßnahmen (OPS)

> Eigenständige Betriebsmaßnahmen, die nicht als SEC-Finding klassifiziert sind.

| ID | Maßnahme | Priorität | Status |
|----|----------|-----------|--------|
| OPS-01 | Cluster API ACL einschränken | P1 | Vor PROD |
| OPS-02 | TLS/HTTPS aktivieren | P1 | Nach DNS-Setup |
| OPS-03 | Image Scanning (Trivy/Snyk in CI/CD) | P2 | Vor Abnahme |
| OPS-04 | Audit Logging (zentralisiert) | P2 | Vor Abnahme |

---

## Dokumentation und Runbooks

Runbooks werden in `docs/runbooks/` gepflegt. Jedes Runbook ist ein eigenständiges, verifiziertes Step-by-Step-Dokument.

**Siehe [Runbook-Index](./runbooks/README.md) für die vollständige Übersicht.**

### Vorhandene Runbooks

| # | Runbook | Status | Beschreibung |
|---|---------|--------|--------------|
| 1 | [StackIT Projekt-Setup](./runbooks/stackit-projekt-setup.md) | Verifiziert | StackIT CLI, Service Account, Container Registry |
| 2 | [StackIT PostgreSQL](./runbooks/stackit-postgresql.md) | Verifiziert | DB anlegen, Readonly-User, Managed PG Einschränkungen |
| 3 | [Helm Deploy](./runbooks/helm-deploy.md) | Verifiziert | Helm Install/Upgrade, Secrets, Redis, Troubleshooting |
| 4 | [CI/CD Pipeline](./runbooks/ci-cd-pipeline.md) | Verifiziert | Deploy, Rollback, Secrets, Troubleshooting |
| 5 | [DNS/TLS Setup](./runbooks/dns-tls-setup.md) | Bereit zur Umsetzung | cert-manager, Let's Encrypt, Cloudflare DNS-01, BSI-konform |
| 6 | [LLM-Konfiguration](./runbooks/llm-konfiguration.md) | Verifiziert | StackIT AI Model Serving, Embedding, Admin UI Setup |
| 7 | [Rollback-Verfahren](./runbooks/rollback-verfahren.md) | Verifiziert | Entscheidungsbaum, Helm/DB-Rollback, Kommunikation, Post-Mortem |

### Geplante Runbooks (vor PROD)

1. **Incident Response** -- P1/P2 Prozeduren
2. **Monitoring Setup** -- Prometheus/Grafana Installation
3. **PROD Provisioning** -- Terraform + Helm für Produktionsumgebung
4. **Upstream Merge** -- Schritt-für-Schritt Onyx-Update-Prozess

### Weitere Referenzdokumentation

| Dokument | Pfad | Inhalt |
|----------|------|--------|
| Implementierungsplan | `docs/referenz/stackit-implementierungsplan.md` | Schritt-für-Schritt DEV+TEST Setup |
| Infrastruktur-Referenz | `docs/referenz/stackit-infrastruktur.md` | Architekturentscheidungen, Specs |
| ADR-004 | `docs/adr/adr-004-umgebungstrennung-dev-test-prod.md` | Umgebungstrennung |
| Sicherheitskonzept | `docs/sicherheitskonzept.md` | DSGVO, BAIT, BSI-Grundschutz |
| Testkonzept | `docs/testkonzept.md` | Teststrategie, Abnahmekriterien |
| Changelog | `docs/CHANGELOG.md` | Versionshistorie |

---

**Dokumentstatus**: Entwurf (teilweise verifiziert)
**Letzte Aktualisierung**: 2026-03-07
**Version**: 0.5
