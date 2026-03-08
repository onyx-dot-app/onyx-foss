# StackIT Implementierungsplan — VÖB Service Chatbot

**Stand**: März 2026
**Erstellt von**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Bezug**: [Technische Referenz](stackit-infrastruktur.md) | [Meilensteinplan](../abnahme/meilensteinplan.md)

> **Scope dieses Plans: DEV + TEST Environments.**
> Phase 1–6: DEV (abgeschlossen). Phase 7: TEST (abgeschlossen, LIVE seit 2026-03-03).
> PROD-Spezifikationen sind in der [Technischen Referenz](stackit-infrastruktur.md) dokumentiert.
> Architekturentscheidung zur Umgebungstrennung: [ADR-004](../adr/adr-004-umgebungstrennung-dev-test-prod.md)

---

## Was wird provisioniert?

| Ressource | Spec | Geschätzte Kosten |
|-----------|------|-------------------|
| 1× SKE Cluster | 1 Node Pool (`devtest`) | ~72 EUR/Monat |
| 2× Worker Nodes | g1a.8d (8 vCPU, 32 GB RAM) je | ~566 EUR/Monat |
| 2× PostgreSQL Flex 2.4 | Single (2 CPU, 4 GB, 20 GB SSD) je | ~60 EUR/Monat |
| 2× Object Storage Bucket | `vob-dev`, `vob-test` | ~10 EUR/Monat |
| **TOTAL DEV + TEST** | | **~868 EUR/Monat** |

---

## Architekturentscheidungen

| Helm Default | StackIT-Entscheidung | Grund |
|-------------|---------------------|-------|
| CloudNativePG (in-cluster) | **StackIT Managed PostgreSQL Flex** (extern) | Backups, PITR managed |
| MinIO (in-cluster) | **StackIT Object Storage** (extern) | S3-kompatibel, kein Overhead |
| Docker Hub Images | **StackIT Container Registry** | Datensouveränität |
| OpenAI / LiteLLM | **StackIT AI Model Serving** (`openai/gpt-oss-120b`) | Daten bleiben in DE, OpenAI-kompatible API |
| Vespa (in-cluster) | **Vespa (in-cluster)** — bleibt | Kein managed Vespa verfügbar |
| Redis (in-cluster) | **Redis (in-cluster)** — bleibt | Lightweight genug |

---

## Erstellte Dateien (alle NEU, kein Onyx-Code verändert)

```
deployment/
  terraform/
    modules/
      stackit/                        ← NEU (neben bestehendem aws/)
        main.tf                       ← SKE + PostgreSQL + ObjectStorage
        variables.tf                  ← Alle Variablen mit Defaults
        outputs.tf                    ← Kubeconfig, PG-Credentials, Bucket
        versions.tf                   ← Provider stackitcloud/stackit ~> 0.80
    environments/
      dev/                            ← DEV-Umgebung
        main.tf                       ← Ruft Modul mit DEV-Werten auf
        backend.tf                    ← Local State (Remote vorbereitet)
        terraform.tfvars              ← Leer (project_id per CLI)
      test/                           ← NEU — TEST-Umgebung
        main.tf                       ← Eigene PG Flex + Bucket
        backend.tf                    ← Local State
        terraform.tfvars              ← Leer (project_id per CLI)
  helm/
    charts/onyx/                      ← BESTEHEND — READ-ONLY, nicht anfassen
    values/                           ← NEU
      values-common.yaml              ← PG aus, MinIO aus, Vespa+Redis an
      values-dev.yaml                 ← 1 Replica pro Service, 8 Celery-Worker (Standard Mode)
      values-test.yaml                ← NEU — TEST analog DEV, eigene Credentials
      values-prod.yaml              ← PROD: Platzhalter (noch nicht deployed)

.github/workflows/
  stackit-deploy.yml                  ← NEU (neben bestehenden Workflows)
```

---

## Phase 1: StackIT Projekt einrichten

> **Status**: ✅ Abgeschlossen (2026-02-12). Siehe [Runbook](../runbooks/stackit-projekt-setup.md) für verifizierte Schritte.

### 1.1 CLI + Service Account erstellen

```bash
# CLI installieren (Cask, nicht Formula)
brew tap stackitcloud/tap
brew install --cask stackit

# Login
stackit auth login

# Service Account für Terraform (Name max. 20 Zeichen)
stackit service-account create \
  --name "voeb-terraform" \
  --project-id <PROJECT_ID>

# Key generieren (Email in Anführungszeichen wegen @-Zeichen)
stackit service-account key create \
  --email "<SA_EMAIL>" \
  --project-id <PROJECT_ID>

# Credentials sicher ablegen (NICHT in Git!)
mkdir -p ~/.stackit
# JSON in ~/.stackit/voeb-terraform-credentials.json speichern
export STACKIT_SERVICE_ACCOUNT_KEY_PATH=~/.stackit/voeb-terraform-credentials.json
```

### 1.2 Service Account Berechtigungen

Service Account braucht `project.admin`-Rolle. Erfordert einen User mit `project.owner`:

```bash
stackit project member add <SA_EMAIL> \
  --project-id <PROJECT_ID> \
  --role project.admin
```

### 1.3 Container Registry aktivieren

Aktivierung über das [StackIT Portal](https://portal.stackit.cloud/) → Sidebar → Container Registry.

```bash
# Docker Login (persönlich, für Entwicklung)
docker login registry.onstackit.cloud
# Username: StackIT-Email
# Password: CLI Secret (Portal → User Profile)

# Docker Login (Robot Account, für CI/CD)
docker login registry.onstackit.cloud \
  -u 'robot$voeb-chatbot+github-ci' \
  -p '<ROBOT_TOKEN>'

# Image-Naming (Registry-Projektname, NICHT Project UUID):
# registry.onstackit.cloud/voeb-chatbot/onyx-backend:<tag>
# registry.onstackit.cloud/voeb-chatbot/onyx-web-server:<tag>
# registry.onstackit.cloud/voeb-chatbot/onyx-model-server:<tag>
```

> **Hinweis:** Die Container Registry nutzt einen eigenen Projektnamen (`voeb-chatbot`),
> nicht die StackIT Project UUID. Siehe [Container Registry Doku](stackit-container-registry.md).

### 1.4 GitHub Secrets anlegen

**Global (Repository-weit):**

| Secret | Wert | Quelle |
|--------|------|--------|
| `STACKIT_REGISTRY_USER` | Robot Account Name (z.B. `robot$voeb-chatbot+github-ci`) | Container Registry UI → Robot Accounts |
| `STACKIT_REGISTRY_PASSWORD` | Robot Account Token | Container Registry UI (einmalig bei Erstellung) |
| `STACKIT_KUBECONFIG` | Base64-encoded Kubeconfig | `stackit ske kubeconfig create` → `base64` |

**Per GitHub Environment (dev/test/prod):**

| Secret | Wert | Quelle |
|--------|------|--------|
| `POSTGRES_PASSWORD` | PG Flex App-User Passwort | `terraform output -raw pg_password` |
| `S3_ACCESS_KEY_ID` | Object Storage Access Key | `stackit object-storage credentials` |
| `S3_SECRET_ACCESS_KEY` | Object Storage Secret Key | `stackit object-storage credentials` |
| `DB_READONLY_PASSWORD` | PG Readonly User Passwort | `terraform output` (readonly user) |

> **Hinweis:** `STACKIT_PROJECT_ID` wird NICHT als Secret benötigt.
> Die Container Registry nutzt einen eigenen Projektnamen (`voeb-chatbot`), nicht die Project UUID.
> Siehe [Container Registry Doku](stackit-container-registry.md) für Details.

---

## Phase 2: DEV-Infrastruktur provisionieren

> **Status**: ✅ Abgeschlossen (2026-02-22). SKE Cluster, PostgreSQL Flex und Object Storage laufen.

### 2.1 Terraform initialisieren

> **Voraussetzung:** `STACKIT_SERVICE_ACCOUNT_KEY_PATH` muss gesetzt sein (siehe Phase 1.1).

```bash
cd deployment/terraform/environments/dev

# Provider herunterladen (installiert stackitcloud/stackit Provider)
terraform init

# Plan erstellen (Project ID übergeben)
terraform plan -var="project_id=<DEINE-PROJECT-ID>" -out=tfplan

# Plan prüfen, dann ausführen
terraform apply tfplan
```

> **Hinweis:** Provider ab v0.80 erfordert `default_region` statt `region` in der Provider-Konfiguration. Ist in `modules/stackit/main.tf` bereits korrigiert.

### 2.2 Was Terraform erstellt

Das Modul in `deployment/terraform/modules/stackit/main.tf` provisioniert:

**SKE Cluster** (`vob-chatbot`):
- 1 Node Pool `devtest` mit 2× g1a.8d (min=2, max=2)
- Kubernetes v1.32.12 (SKE weist nächst-verfügbare Version zu)
- Flatcar OS
- Maintenance-Window: 02:00–04:00 UTC
- ACL: offen (wird später eingeschränkt)

**PostgreSQL Flex** (`vob-dev`):
- Version 16
- 2 CPU, 4 GB RAM (Flex 2.4)
- 1 Replica (Single, kein HA)
- 20 GB SSD Storage
- Tägliches Backup um 02:00 UTC
- Automatisch generierter App-User `onyx_app`

**Object Storage**:
- Bucket `vob-dev`

### 2.3 Outputs sichern

```bash
# Kubeconfig über StackIT CLI holen (NICHT terraform output — Token läuft nach ~1h ab)
stackit ske kubeconfig create vob-chatbot \
  --project-id <PROJECT_ID> \
  --expiration 12h
# Speichert automatisch in ~/.kube/config bzw. --filepath angeben

export KUBECONFIG=~/.kube/voeb-chatbot.yaml

# PostgreSQL-Zugangsdaten
terraform output pg_host       # → Host für Helm Values
terraform output pg_port       # → Port
terraform output -raw pg_password  # → Passwort für K8s Secret

# Cluster verifizieren
kubectl get nodes
kubectl cluster-info
```

> **Hinweis:** `terraform output -raw kubeconfig` generiert ein Client-Zertifikat mit ~1h Gültigkeit. Für den täglichen Zugriff immer `stackit ske kubeconfig create` mit `--expiration` verwenden.

---

## Phase 3: Kubernetes-Namespace einrichten

> **Status**: ✅ Abgeschlossen (2026-02-27). Namespace, Image Pull Secret erstellt. Resource Quota entfernt (blockiert Pods ohne explizite Limits).

### 3.1 DEV Namespace

```bash
kubectl create namespace onyx-dev
kubectl label namespace onyx-dev environment=dev project=voeb-chatbot
```

### 3.2 Image Pull Secret

```bash
kubectl create secret docker-registry stackit-registry \
  --namespace=onyx-dev \
  --docker-server=registry.onstackit.cloud \
  --docker-username=<REGISTRY_USER> \
  --docker-password=<REGISTRY_PASSWORD>
```

### 3.3 Resource Quota (DEV)

> **ENTFERNT:** Resource Quota blockiert Pods ohne explizite Resource Limits (z.B. NGINX Admission Webhook Job aus dem Onyx Chart). Für DEV wird keine Quota gesetzt. Für PROD wird eine angepasste Quota mit höheren Limits definiert.

<!--
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: resource-quota
  namespace: onyx-dev
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 12Gi
    limits.cpu: "8"
    limits.memory: 16Gi
```
-->

---

## Phase 4: Helm Deploy (DEV)

> **Status**: ✅ **Abgeschlossen** (2026-02-27). Alle 16 Pods Running, API Health OK, UI erreichbar unter `http://188.34.74.187`.

### 4.1 Helm Values anpassen

Nach `terraform apply` die tatsächlichen Werte in `deployment/helm/values/values-dev.yaml` eintragen:

```yaml
configMap:
  POSTGRES_HOST: "<output von terraform output pg_host>"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "onyx"
```

### 4.2 Deploy ausführen

```bash
helm upgrade --install onyx-dev \
  deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  -f deployment/helm/values/values-dev-secrets.yaml

# Verifizieren
kubectl get pods -n onyx-dev
curl -s http://<EXTERNAL_IP>/api/health
```

### 4.3 Ressourcen auf DEV-Node

| Komponente | CPU Request | RAM Request | Replicas |
|-----------|------------|-------------|----------|
| Backend API | 250m | 512Mi | 1 |
| Frontend | 100m | 256Mi | 1 |
| Vespa | 500m | 2Gi | 1 |
| Redis | 100m | 128Mi | 1 |
| Model Server (Inference) | 250m | 768Mi | 1 |
| Model Server (Indexing) | 250m | 768Mi | 1 |
| Celery Beat | 100m | 256Mi | 1 |
| Celery Worker Primary | 250m | 512Mi | 1 |
| Celery Worker Light | 250m | 512 Mi | 1 |
| Celery Worker Heavy | 250m | 512 Mi | 1 |
| Celery Worker DocFetching | 250m | 512 Mi | 1 |
| Celery Worker DocProcessing | 250m | 512 Mi | 1 |
| Celery Worker Monitoring | 100m | 256 Mi | 1 |
| Celery Worker User File | 250m | 512 Mi | 1 |
| Redis Operator | 500m | — | 1 |
| NGINX Ingress Controller | 100m | 128Mi | 1 |
| **TOTAL DEV (onyx-dev)** | **~3.5 CPU** | **~7 Gi** | |
| kube-system (Calico, DNS, VPN, Metrics) | ~1.4 CPU | ~2 Gi | — |
| **TOTAL Node** | **~4.9 CPU** | **~9 Gi** | |

**Verfuegbar (1x g1a.8d)**: ~7.9 CPU / ~28.3 Gi RAM. ~1.4 CPU werden von kube-system (Calico, CoreDNS, VPN, Metrics) beansprucht.

---

## Phase 5: CI/CD Pipeline

> **Status**: ✅ Produktionsreif (2026-03-02). Pipeline getestet über 5 Runs, alle Probleme gelöst.
> - Run #1: Deploy fehlgeschlagen — fehlender `helm dependency build`-Step → Fix: `f3a22017f`
> - Run #2: Deploy fehlgeschlagen — Helm Repos nicht registriert → Fix: `64c9c7aca`
> - Run #3: Deploy fehlgeschlagen — `Insufficient CPU` bei RollingUpdate auf Single-Node → Fix: Recreate-Strategie
> - Run #4: Deploy OK (Pipeline grün), aber API-Server CrashLoop (`LICENSE_ENFORCEMENT_ENABLED` Default `true` aktiviert EE-Code) + Model Server ImagePullBackOff → Rollback
> - **Run #5: Komplett grün** (ea70a11, ~10 Min). Alle 10 Pods Running, Health Check OK.
> - 21 Onyx-Upstream-Workflows deaktiviert, nur StackIT Deploy + Upstream Check aktiv

### Pipeline-Architektur

```
prepare (6s)          → Git SHA als Image Tag bestimmen
  ├── build-backend   → ~6 Min (parallel)  → StackIT Registry
  └── build-frontend  → ~8 Min (parallel)  → StackIT Registry
deploy-{env}          → ~2 Min (Helm upgrade + Smoke Test)
```

**Gesamtdauer: ~10 Minuten** (Build parallel + Deploy).

### Sicherheitsmaßnahmen (Enterprise)

- **SHA-gepinnte GitHub Actions** — alle 6 Actions auf Commit-Hash fixiert (Supply-Chain-Schutz)
- **Least-Privilege Permissions** — `permissions: contents: read`
- **Concurrency Control** — max 1 Deploy pro Environment, cancel-in-progress
- **Secrets ausschließlich über GitHub Secrets** — keine Credentials in Git (auch Redis)
- **Model Server gepinnt** — `v2.9.8` statt `:latest` (Reproduzierbarkeit)

### Deploy-Verhalten pro Environment

| Feature | DEV | TEST | PROD |
|---------|-----|------|------|
| Trigger | `main`-Push oder manuell | Nur manuell | Nur manuell |
| Helm Rollback | Manuell | `--atomic` (automatisch) | `--atomic` (automatisch) |
| Recreate-Patch | Ja (Single-Node) | Nein | Nein |
| Smoke Test | `/api/health` (120s Timeout) | `/api/health` (120s Timeout) | `/api/health` (180s Timeout, 18 Attempts) |
| Required Reviewers | Nein | Nein | Ja (GitHub Settings) |

### Image-Strategie

| Dienst | Image-Quelle | Tag |
|--------|-------------|-----|
| Backend (API + Celery) | StackIT Registry | Git SHA (`ea70a11`) |
| Frontend (Web) | StackIT Registry | Git SHA |
| Model Server | Docker Hub Upstream | `v2.9.8` (gepinnt) |

Der Model Server wird **nicht** von uns gebaut — er ist identisch mit Upstream Onyx und wird direkt von Docker Hub gepullt. Das spart ~12 Min Build-Zeit und eliminiert das ImagePullBackOff-Problem (StackIT Registry → Docker Hub).

### Kritische Konfiguration

- `LICENSE_ENFORCEMENT_ENABLED: "false"` in `values-common.yaml` — **PFLICHT**. Onyx FOSS hat Default `true`, was EE-Code-Pfade aktiviert und zum Crash führt (`onyx.server.tenants` existiert nicht im FOSS-Fork).
- Kubeconfig-Ablauf: **2026-05-28** — muss vorher erneuert werden.

### Voraussetzung

GitHub Secrets aus Phase 1.4 müssen gesetzt sein + `REDIS_PASSWORD` pro Environment.

### Runbook

Detaillierte Anleitung: [`docs/runbooks/ci-cd-pipeline.md`](../runbooks/ci-cd-pipeline.md)

---

## Phase 6: LLM-Integration (nach funktionierendem Deploy)

> **Status**: ✅ Chat-Modell konfiguriert (2026-02-27). Embedding-Modell ausstehend.

StackIT AI Model Serving bietet eine **OpenAI-kompatible API** (vLLM-Backend).
Onyx unterstützt das nativ über LiteLLM — keine Code-Änderung nötig, reine Admin-UI-Konfiguration.

### 6.1 Voraussetzung: Auth Token erstellen

Im StackIT Portal → AI Model Serving → Token erstellen (Name + Laufzeit, z.B. `onyx-dev` / 90d).
Ein Token gilt für **alle Modelle** (Chat + Embedding) im Projekt.

> ⚠️ Token wird nur einmalig bei Erstellung angezeigt — sofort sicher speichern!

### 6.2 Chat-Modell konfigurieren (Onyx Admin UI)

> ✅ **Verifiziert am 2026-02-27** — GPT-OSS 120B antwortet korrekt.

Pfad: Admin UI → `http://<HOST>/admin/configuration/llm` → **Setup Custom LLM**

| Feld | Wert |
|------|------|
| Display Name | `StackIT - Demo Dev` |
| Provider Name | `openai` |
| API Key | StackIT AI Model Serving Auth Token |
| API Base | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1` |
| Model Name | `openai/gpt-oss-120b` |
| Max Input Tokens | `130048` |
| Default Model | `openai/gpt-oss-120b` |

> **LiteLLM-Besonderheit:** StackIT-Modell-IDs enthalten einen Prefix (z.B. `openai/gpt-oss-120b`).
> In der Onyx Admin UI muss der **volle StackIT-Modellname** als Model Name eingetragen werden.
> Onyx baut intern `{provider}/{model}` → `openai/openai/gpt-oss-120b`.
> LiteLLM splittet beim ersten `/`, erkennt Provider=`openai`, und schickt `openai/gpt-oss-120b` korrekt an die API.
>
> **NICHT** den "OpenAI"-Provider aus der Standardliste verwenden — dessen Formular validiert auf `sk-`-Key-Format.
> Stattdessen immer **"Setup Custom LLM"** nutzen.
>
> **Provider Name ist IMMER `openai`** — unabhängig vom Modell (GPT-OSS, Qwen, Llama, Gemma, ...).
> Der Provider Name bestimmt das API-Protokoll (OpenAI-kompatibel), nicht das Modell.
> Den Modellhersteller (z.B. `qwen`, `google`) **NICHT** als Provider Name eintragen.

**Modell-Details GPT-OSS 120B:**
- 131K Token Kontext, 4-bit Quantisierung
- Tool Calling, Reasoning, Structured Output
- 0,45 EUR / 1M Input-Tokens, 0,65 EUR / 1M Output-Tokens

#### Qwen3-VL 235B (zweites Chat-Modell)

> ✅ **Verifiziert am 2026-02-27** — Qwen3-VL antwortet korrekt.

Separater Custom LLM Provider in der Admin UI:

| Feld | Wert |
|------|------|
| Display Name | `StackIT - Demo - Qwen3` |
| Provider Name | `openai` |
| API Key | Gleicher StackIT Auth Token |
| API Base | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1` |
| Model Name | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` |
| Default Model | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` |

**Modell-Details Qwen3-VL 235B:**
- 218K Token Kontext, 8-bit Quantisierung
- Vision, OCR (32 Sprachen), Tool Calling
- 0,45 EUR / 1M Input-Tokens, 0,65 EUR / 1M Output-Tokens

### 6.3 Embedding-Modell konfigurieren

> ⚠️ Blocker aufgehoben (Upstream PR #9005). Fallback: nomic-embed-text-v1 aktiv.

Gleicher Provider, gleiche API Base, gleicher Auth Token. Separater Provider-Eintrag in der Admin UI.

| Feld | Wert |
|------|------|
| Display Name | `StackIT Embedding - Dev` |
| Provider Name | `openai` |
| API Key | Gleicher Auth Token |
| API Base | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1` |
| Model Name | `Qwen/Qwen3-VL-Embedding-8B` |
| Default Model | `Qwen/Qwen3-VL-Embedding-8B` |

**Modell-Details Qwen3-VL-Embedding 8B:** 4096 Dimensionen (flexibel 64–4096), max 32.768 Tokens, 30+ Sprachen inkl. Deutsch, multimodal (Text + Bilder). MTEB Multilingual #1 (Score 70.58). Ersetzt E5 Mistral 7B (nur Englisch empfohlen).

### 6.4 Weitere verfügbare Modelle (Fallback / Alternativen)

| Modell | StackIT Model ID | Kontext | Status |
|--------|------------------|---------|--------|
| **GPT-OSS 120B** | `openai/gpt-oss-120b` | 131K | ✅ Verifiziert |
| **Qwen3-VL 235B** | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` | 218K | ✅ Verifiziert |
| Llama 3.3 70B | `cortecs/Llama-3.3-70B-Instruct-FP8-Dynamic` | 128K | Verfügbar |

> **TODO (H3):** Llama 3.3 Model-ID ist inkonsistent: hier `cortecs/Llama-3.3-70B-Instruct-FP8-Dynamic` (FP8-Quantisierung), im [LLM-Runbook](../runbooks/llm-konfiguration.md) `meta-llama/Llama-3.3-70B-Instruct` (Standard). Korrekte StackIT Model-ID verifizieren und vereinheitlichen.
| Gemma 3 27B | `google/gemma-3-27b-it` | 37K | Verfügbar |
| Mistral-Nemo 12B | `neuralmagic/Mistral-Nemo-Instruct-2407-FP8` | 128K | Verfügbar |
| Llama 3.1 8B | `neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8` | 128K | Verfügbar |

> Bei Modellwechsel: Die **volle StackIT Model ID** als Model Name eintragen (s. Abschnitt 6.2).

### 6.5 Rate Limits

- **TPM:** 200.000 Tokens/Minute (Output-Tokens 5× gewichtet)
- **RPM:** 30–600 Requests/Minute (modellabhängig)

### 6.6 Token-Kalkulation DEV

5 User, ~550 Queries/Monat → ~2–3 EUR/Monat LLM-Kosten (Chat + Embedding).

---

## Phase 7: TEST-Umgebung aufsetzen

> **Status**: ✅ TEST LIVE (2026-03-03). ADR-004 akzeptiert. 15 Pods Running, Health Check OK, UI unter `http://188.34.118.201`.
> **Bezug**: [ADR-004: Umgebungstrennung](../adr/adr-004-umgebungstrennung-dev-test-prod.md)

### 7.1 Node Pool skalieren (1 → 2 Nodes)

Der bestehende Node Pool `devtest` wird auf 2 Nodes erweitert, damit DEV und TEST jeweils eigene Hardware haben.

```bash
cd deployment/terraform/environments/dev

# Änderung in main.tf:
# node_pool.minimum = 2
# node_pool.maximum = 2

terraform plan -var="project_id=<PROJECT_ID>" -out=tfplan
terraform apply tfplan

# Verifizieren
kubectl get nodes  # → 2 Nodes "Ready"
```

> **Hinweis:** Node Pool Label `environment` bleibt `dev` (nicht `devtest`), da der Wert den PG-Instanznamen bestimmt (`vob-{environment}`). Für SEC-02 (Node Affinity) müssen die Nodes manuell per `kubectl label` separate Labels erhalten.

### 7.2 TEST PostgreSQL Flex + Object Storage

Eigene Terraform-Konfiguration in `deployment/terraform/environments/test/main.tf`:

```bash
cd deployment/terraform/environments/test

terraform init
terraform plan -var="project_id=<PROJECT_ID>" -out=tfplan
terraform apply tfplan
```

**Was Terraform erstellt:**

| Ressource | Name | Spec |
|-----------|------|------|
| PostgreSQL Flex | `vob-test` | 2.4 Single (2 CPU, 4 GB), 20 GB SSD |
| PG Users | `onyx_app` + `db_readonly_user` | Analog DEV |
| Object Storage | `vob-test` | S3-kompatibel |

> **Kein eigener Cluster!** TEST nutzt den gleichen SKE-Cluster wie DEV (ADR-004).
> Das Terraform-Modul für TEST erstellt nur PG + Bucket, keinen neuen Cluster.

### 7.3 Kubernetes-Namespace einrichten

```bash
kubectl create namespace onyx-test
kubectl label namespace onyx-test environment=test project=voeb-chatbot

# Image Pull Secret (gleiche Registry wie DEV)
kubectl create secret docker-registry stackit-registry \
  --namespace=onyx-test \
  --docker-server=registry.onstackit.cloud \
  --docker-username=<REGISTRY_USER> \
  --docker-password=<REGISTRY_PASSWORD>
```

### 7.4 Helm Values (values-test.yaml)

Neues File `deployment/helm/values/values-test.yaml`, analog zu `values-dev.yaml`:

| Unterschied zu DEV | TEST-Wert |
|---------------------|-----------|
| `POSTGRES_HOST` | Aus `terraform output pg_host` (TEST-Instanz) |
| `S3_FILE_STORE_BUCKET_NAME` | `vob-test` |
| `WEB_DOMAIN` | `http://<TEST-LoadBalancer-IP>` (bis DNS verfügbar) |
| `REDIS_HOST` | `onyx-test` (Release-Name = Redis-Service-Name) |
| Alle Replicas | 1 (wie DEV) |
| `AUTH_TYPE` | `basic` (bis Entra ID verfügbar) |

### 7.5 GitHub Secrets für Environment `test`

In GitHub → Repository Settings → Environments → `test`:

| Secret | Quelle |
|--------|--------|
| `POSTGRES_PASSWORD` | `terraform output -raw pg_password` (TEST) |
| `S3_ACCESS_KEY_ID` | `stackit object-storage credentials` (TEST-Bucket) |
| `S3_SECRET_ACCESS_KEY` | `stackit object-storage credentials` (TEST-Bucket) |
| `DB_READONLY_PASSWORD` | `terraform output -raw pg_readonly_password` (TEST) |
| `REDIS_PASSWORD` | Neues Passwort generieren |

### 7.6 DB `onyx` anlegen auf TEST-Instanz

Analog zu DEV — die PG Flex Instanz erstellt nur die Instanz, nicht die Datenbank:

```bash
# PG Host + Port aus Terraform Output
psql "postgresql://onyx_app:<PASSWORD>@<TEST_PG_HOST>:<PORT>/postgres" \
  -c "CREATE DATABASE onyx;"
```

> Alternativ: Beim ersten Helm Deploy erstellt Onyx die DB via Alembic-Migration automatisch,
> sofern `onyx_app` die Rolle `createdb` hat (per Terraform gesetzt).

### 7.7 Deploy + Validierung

```bash
# Option A: Manuell per workflow_dispatch (GitHub UI)
# Branch: main → Environment: test

# Option B: Manuell per CLI
helm upgrade --install onyx-test \
  deployment/helm/charts/onyx \
  --namespace onyx-test \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-test.yaml \
  --atomic --timeout 10m

# Verifizieren
kubectl get pods -n onyx-test          # → 15 Pods Running (+ redis-operator im default NS)
curl -s http://<TEST-IP>/api/health    # → {"success":true}
```

### 7.8 Smoke Test für deploy-test Job

✅ Smoke Test wurde im CI/CD-Workflow ergänzt (analog zu `deploy-dev`: `/api/health`, 12 Versuche, 120s Timeout).

### 7.9 LLM-Konfiguration

Nach erfolgreichem Deploy: Gleiche LLM-Provider in der TEST Admin UI konfigurieren (siehe Phase 6). Gleicher StackIT AI Model Serving Token, gleiche Modelle.

---

## Validierung (DEV)

| Kriterium | Test | Status |
|-----------|------|--------|
| K8s Cluster läuft | `kubectl get nodes` → Ready, g1a.8d | [x] ✅ (2026-02-27) |
| PostgreSQL erreichbar | DB `onyx` existiert, Alembic-Migrationen laufen | [x] ✅ (2026-02-27) |
| Vespa deployed | Pod Running, Application Package deployed | [x] ✅ (2026-02-27) |
| Redis deployed | Pod Running, Celery Beat/Worker verbunden | [x] ✅ (2026-02-27) |
| Object Storage | Credentials aktiv, api-server startet ohne Fehler | [x] ✅ (2026-02-27) |
| API Health | `curl http://188.34.74.187/api/health` → `{"success":true}` | [x] ✅ (2026-02-27) |
| Onyx UI erreichbar | `http://188.34.74.187/auth/login` → Login-Seite | [x] ✅ (2026-02-27) |
| LLM Chat-Modell (GPT-OSS) | GPT-OSS 120B antwortet über Onyx Chat | [x] ✅ (2026-02-27) |
| LLM Chat-Modell (Qwen3-VL) | Qwen3-VL 235B antwortet über Onyx Chat | [x] ✅ (2026-02-27) |
| LLM Embedding-Modell | Qwen3-VL-Embedding 8B fuer Dokumenten-Suche | [ ] ⚠️ Blocker aufgehoben (Upstream PR #9005). Fallback: nomic-embed-text-v1 aktiv. |
| CI/CD funktioniert | Push auf main → Pods updated | [x] ✅ Run #5 (2026-03-02): 10 Min, 10/10 Pods, Health OK |

---

## Validierung (TEST)

| Kriterium | Test | Status |
|-----------|------|--------|
| 2 Nodes im Cluster | `kubectl get nodes` → 2× Ready, g1a.8d | [x] ✅ (2026-03-03) |
| TEST PostgreSQL erreichbar | DB `onyx` existiert auf TEST-Instanz | [x] ✅ (2026-03-03) |
| Object Storage (vob-test) | Credentials aktiv, Bucket erreichbar | [x] ✅ (2026-03-03) |
| Namespace onyx-test | `kubectl get ns onyx-test` → Active | [x] ✅ (2026-03-03) |
| 15 Pods Running (+ redis-operator im default NS) | `kubectl get pods -n onyx-test` → 15/15 Running | [x] ✅ (2026-03-03) |
| API Health | `curl http://188.34.118.201/api/health` → `{"success":true}` | [x] ✅ (2026-03-03) |
| Onyx UI erreichbar | `http://188.34.118.201/auth/login` → Login-Seite | [x] ✅ (2026-03-03) |
| LLM Chat-Modell | GPT-OSS 120B antwortet über TEST Chat | [x] ✅ (2026-03-03) |
| CI/CD deploy-test | `workflow_dispatch` → Pods updated | [x] ✅ (2026-03-03) |
| DEV unabhängig | DEV-Pods weiterhin Running nach TEST-Deploy | [x] ✅ (2026-03-03) |

---

## Nächste Schritte

| Schritt | Wann | Was | Status |
|---------|------|-----|--------|
| TEST Environment | Nach DEV-Validierung | Phase 7: Node Pool skalieren, PG + Bucket + Namespace + Helm | ✅ LIVE (2026-03-03) |
| Embedding-Modell | Parallel zu TEST | Qwen3-VL-Embedding 8B in Admin UI konfigurieren | ⚠️ Blocker aufgehoben (Upstream PR #9005). nomic-embed-text-v1 als Fallback aktiv. |
| Branding | Nach TEST-Setup | Logo-Dateien ersetzen, ext/-Komponenten | ⏳ Offen |
| Entra ID (Auth) | Sobald Credentials von VÖB | `AUTH_TYPE: oidc` in Helm Values | Blockiert |
| DNS + TLS | Nach DNS-Setup | Let's Encrypt oder StackIT-CA | Blockiert (VÖB IT) |
| Security-Härtung P0 | Vor TEST-Deploy | SEC-01: PG ACL einschränken (30 Min) | ✅ Erledigt (2026-03-03) |
| Security-Härtung P1 | Nach TEST, vor PROD | SEC-06 Phase 1 ✅ (`privileged: false` deployed). Phase 2: `runAsNonRoot` (4-6h) + M7: Cluster-ACL. SEC-02/04/05 zurückgestellt. | ⏳ Teilweise |
| PROD Cluster | Vor Go-Live | Eigener SKE-Cluster + 2× g1a.8d + PG 4.8 HA (ADR-004) | Geplant |
| Monitoring | Phase M5 | Prometheus/Grafana Stack | Geplant |

---

## Offene Punkte

| Nr. | Thema | Wer | Status |
|-----|-------|-----|--------|
| 1 | StackIT Project ID für Terraform | Niko | ✅ Erledigt (2026-02-12) |
| 2 | Service Account erstellen | Niko | ✅ Erledigt (2026-02-12) |
| 3 | Container Registry aktivieren | Niko | ✅ Erledigt (2026-02-12) |
| 4 | SA `project.admin`-Rolle zuweisen | Org-Admin | ✅ Erledigt (2026-02-22) |
| 5 | Terraform apply (DEV) | Niko | ✅ Erledigt (2026-02-22) |
| 6 | Helm Deploy (DEV) | Niko | ✅ Erledigt (2026-02-27) |
| 7 | DB `onyx` + `db_readonly_user` anlegen | Niko | ✅ Erledigt (2026-02-27) |
| 8 | Object Storage Credentials | Niko | ✅ Erledigt (2026-02-27) |
| 9 | StackIT AI Model Serving (Chat-Modell konfiguriert) | Niko | ✅ Erledigt (2026-02-27) |
| 10 | DNS-Zone (`dev.chatbot.voeb-service.de` → `188.34.74.187`) | VÖB IT | ✅ Erledigt (2026-03-05) |
| 11 | Entra ID Credentials | VÖB IT | Blockiert |
| 12 | Storage Class Name prüfen | Bei `terraform plan` sichtbar | ✅ `premium-perf2-stackit` (bestätigt) |
| 13 | CI/CD Pipeline Helm-Fixes | Niko | ✅ Erledigt (2026-03-02) — `f3a22017f` + `64c9c7aca` |
| 14 | Upstream-Workflows deaktivieren | Niko | ✅ Erledigt (2026-03-02) — 21 Workflows disabled via API |
| 15 | TEST: Node Pool 1→2 Nodes skalieren | Niko | ✅ Erledigt (2026-03-03) |
| 16 | TEST: PG Flex + Object Storage provisionieren | Niko | ✅ Erledigt (2026-03-03) |
| 17 | TEST: Namespace + Image Pull Secret | Niko | ✅ Erledigt (2026-03-03) |
| 18 | TEST: values-test.yaml + GitHub Secrets | Niko | ✅ Erledigt (2026-03-03) |
| 19 | TEST: Helm Deploy + Validierung | Niko | ✅ Erledigt (2026-03-03) |
| 20 | TEST: LLM-Konfiguration in Admin UI | Niko | ✅ Erledigt (2026-03-03) |
| 21 | **SEC-01**: PostgreSQL ACL einschränken | Niko | ✅ Erledigt (2026-03-03) |
| 22 | **SEC-02**: Node Affinity erzwingen | Niko | **Zurückgestellt** (2026-03-08) — bestehende Isolation ausreichend |
| 23 | **SEC-03**: Kubernetes NetworkPolicies | Niko | ✅ Erledigt (2026-03-05) |
| 24 | **SEC-04**: Terraform Remote State | Niko | **Zurückgestellt** (2026-03-08) → P3 (Nice-to-have) |
| 25 | **SEC-05**: Separate Kubeconfigs | Niko | **Zurückgestellt** (2026-03-08) → P3 (opportunistisch bei Kubeconfig-Renewal) |
| 26 | **SEC-06**: Container SecurityContext (`privileged: true` entfernen) | Niko | **Phase 1 ✅** (2026-03-08) — `privileged: false` deployed. Phase 2 (runAsNonRoot) vor PROD |
| 27 | **SEC-07**: Encryption-at-Rest verifizieren | Niko | ✅ Erledigt (2026-03-08) — StackIT Default |
| 28 | **H3**: Llama 3.3 Model-ID vereinheitlichen (FP8 vs Standard) | Niko | ⏳ Klärung mit StackIT |
| 29 | **M3**: IP-Ownership in ADR-001 klären ("CCJ oder VÖB" → eindeutig) | Niko | ⏳ Klärung mit VÖB |
| 30 | **C5**: DSGVO-Dokumente erstellen (DSFA, Löschkonzept, AVV) | Niko | ⏳ P2 (vor Abnahme) |
| 31 | **M5**: PROD OIDC-Secrets in GitHub Environment `prod` vorbereiten | Niko | ⏳ Nach Entra ID |
| 32 | **M6**: PROD Node-Sizing entscheiden (2 vs 3 Nodes) | Niko | ⏳ Vor PROD |
| 33 | **M7**: Cluster-API-ACL Default `0.0.0.0/0` entfernen (`modules/stackit/variables.tf`) | Niko | ⏳ P1 (vor PROD) |
| 34 | **M9**: ✅ Erledigt — Standard Mode (8 separate Worker), Lightweight Mode durch Upstream PR #9014 entfernt | Niko | ✅ Erledigt (2026-03-06) |

---

## Security-Härtung (Audit-Findings, 2026-03-02)

> **Quelle**: Enterprise-Audit der TEST-Infrastruktur vor erstem Deploy.
> Diese Items stammen aus einer systematischen Überprüfung gegen BAIT/BSI-Grundschutz.
> Priorisierung: P0 = vor TEST-Deploy, P1 = vor PROD, P2 = vor VÖB-Abnahme.

### SEC-01: PostgreSQL ACL einschränken (P0 — vor TEST-Deploy)

**Problem**: `pg_acl = ["0.0.0.0/0"]` in allen Environments — PostgreSQL ist für das gesamte Internet erreichbar. Für eine Banking-Anwendung unter BAIT ist das ein Showstopper.

**Betrifft**:
- `deployment/terraform/modules/stackit/main.tf` (DEV-Modul, Zeile 75)
- `deployment/terraform/modules/stackit-data/main.tf` (TEST-Modul)
- `deployment/terraform/environments/dev/main.tf` (hardcoded `pg_acl`)
- `deployment/terraform/environments/test/main.tf` (hardcoded `pg_acl`)

**Lösung**:
1. **Cluster-Egress-CIDR ermitteln:**
   ```bash
   # SKE-Cluster NAT Gateway IP herausfinden:
   # Option A: StackIT Portal → SKE → Cluster → Network Details
   # Option B: Aus einem Pod heraus prüfen:
   kubectl run curl-test --image=curlimages/curl --rm -it -- curl ifconfig.me
   # → gibt die externe IP zurück, die der Cluster für Egress nutzt
   ```
2. **`pg_acl` in beiden Environments einschränken:**
   ```hcl
   # environments/dev/main.tf + environments/test/main.tf
   pg_acl = ["<CLUSTER_EGRESS_CIDR>/32"]
   ```
3. **Default in `variables.tf` beider Module von `["0.0.0.0/0"]` auf `[]` ändern** — erzwingt explizite Angabe pro Environment.
4. **Verifizieren:** `psql` aus einem Pod heraus → Verbindung OK. `psql` von extern → Verbindung abgelehnt.

**Aufwand**: 30 Minuten (+ CIDR-Ermittlung)
**Risiko bei Nicht-Umsetzung**: Audit-Failure, potentieller Datenzugriff durch Dritte.

**Umsetzung (2026-03-03)**:
- Cluster-Egress-IP ermittelt: `188.34.93.194` (NAT Gateway, fest für Cluster-Lifecycle, bestätigt via StackIT Docs)
- Admin-IP: `109.41.112.160` (Nikolaj Ivanov, für direkten DB-Zugriff bei Debugging)
- `pg_acl` Default in beiden Modulen (`stackit`, `stackit-data`) von `["0.0.0.0/0"]` auf **kein Default** geändert → erzwingt explizite Angabe pro Environment
- DEV + TEST: `pg_acl = ["188.34.93.194/32", "109.41.112.160/32"]`
- Credentials-Handling: `~/.stackit/credentials.json` (Wrapper → SA Key), `chmod 600`, `.envrc` in `.gitignore`

### SEC-02: Node Affinity — ZURÜCKGESTELLT (2026-03-08)

**Ursprüngliches Finding**: `nodeSelector` in Helm Values erzwingen, damit DEV- und TEST-Pods jeweils auf eigenen Nodes laufen.

**Entscheidung: Zurückgestellt — kein akuter Handlungsbedarf.**

Begründung (Details im Sicherheitskonzept):
- ADR-004 sagt explizit: "Kein Dedicated-Node-Affinity nötig" (Zeile 61)
- Bestehende Isolation ausreichend: Namespace-Isolation + NetworkPolicies (SEC-03) + separate PG/S3/Secrets/LoadBalancer
- BAIT/BSI-Grundschutz fordern keine Node-Level-Isolation für DEV/TEST
- DEV/TEST enthalten keine Produktionsdaten
- PROD wird eigener Cluster (ADR-004) — dort irrelevant
- Technische Einschränkung: 1 Node Pool = Labels nur uniform per Terraform; persistente Per-Node-Labels erfordern separate Node Pools (Kostenimpact)

**Wiederaufnahme**: Nur bei expliziter Forderung im VÖB-Audit oder bei drittem Tenant auf demselben Cluster.

**Risiko bei Nicht-Umsetzung**: Gering. Scheduler verteilt natürlich (Bin-Packing), NetworkPolicies verhindern Cross-NS-Zugriff.

### SEC-03: Kubernetes NetworkPolicies (P1 — vor PROD)

**Problem**: `stackit-infrastruktur.md` verspricht "Namespace-isoliert", aber es existieren keine NetworkPolicy-Manifeste. Kubernetes isoliert Namespaces NICHT auf Netzwerkebene — Pods in `onyx-dev` können Pods in `onyx-test` direkt erreichen.

**Betrifft**: Gesamter Cluster, alle Namespaces.

**Lösung**:
1. **Default-Deny Policy pro Namespace** erstellen:
   ```yaml
   # k8s/network-policies/default-deny.yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: default-deny-all
     namespace: onyx-dev  # + onyx-test
   spec:
     podSelector: {}
     policyTypes:
       - Ingress
       - Egress
   ```
2. **Allow-Rules pro Namespace** (Ingress innerhalb Namespace + Egress zu PG, S3, LLM):
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-intra-namespace
     namespace: onyx-dev
   spec:
     podSelector: {}
     ingress:
       - from:
           - podSelector: {}  # Alle Pods im gleichen Namespace
     egress:
       - to:
           - podSelector: {}  # Intra-Namespace
       - to:
           - ipBlock:
               cidr: 0.0.0.0/0  # Externe Services (PG, S3, LLM)
         ports:
           - port: 5432      # PostgreSQL
           - port: 443       # S3, LLM API
   ```
3. **Prüfen** ob StackIT SKE einen NetworkPolicy-Controller (Calico, Cilium) vorinstalliert hat — ohne Controller werden Policies ignoriert.
4. **Testen**: `kubectl exec` in einem DEV-Pod → `curl onyx-test-api:80` → sollte nach Policy abgelehnt werden.

**Status**: ✅ ERLEDIGT (2026-03-05). 5 Policies auf DEV + TEST applied, Cross-NS-Isolation verifiziert. Details: `docs/audit/networkpolicy-analyse.md`

### SEC-04: Terraform Remote State — ZURÜCKGESTELLT (2026-03-08)

**Ursprüngliches Finding**: Terraform State liegt lokal mit Klartext-Passwörtern (PG-Credentials, Kubeconfig). Kein Backup, kein Audit-Trail.

**Entscheidung: Herabgestuft von P1 auf P3 (Nice-to-have).** Begründung:
- Solo-Entwickler — kein State-Locking nötig (StackIT S3 bietet ohnehin kein DynamoDB-Äquivalent)
- FileVault aktiv (Full-Disk-Encryption), State gitignored, CI/CD nutzt kein Terraform
- PG ACL als Defense-in-Depth (Passwort allein reicht nicht für DB-Zugang)
- Remote State tauscht ein lokales Secret gegen ein anderes (S3-Credentials müssten lokal liegen)
- Kein BAIT/BSI-Requirement für Remote IaC State
- Kosten bei Umsetzung: 0,03 EUR/Monat (reine GB-Abrechnung, kein Bucket-Grundpreis)

**Quick Win umgesetzt**: `chmod 600` auf alle State-Dateien (war `644`).

**Wiederaufnahme**: Bei Teamvergrößerung oder expliziter Audit-Anforderung. `backend.tf` ist bereits vorbereitet (auskommentierter S3-Block).

**Aufwand bei Umsetzung**: 2 Stunden (Bucket + Migration + Verifizierung)
**Risiko bei Nicht-Umsetzung**: Gering. Bei Laptop-Verlust müssten ~6 Terraform-Ressourcen manuell re-importiert werden (~1-2h).

### SEC-05: Separate Kubeconfigs — ZURÜCKGESTELLT (2026-03-08)

**Ursprüngliches Finding**: Ein globaler `STACKIT_KUBECONFIG` GitHub Secret für alle Environments. Kompromittierter DEV-Workflow kann TEST/PROD manipulieren.

**Entscheidung: Herabgestuft von P1 auf P3 (Nice-to-have).** Begründung:
- PROD wird eigener Cluster (ADR-004) — separates Kubeconfig ergibt sich automatisch. Blast-Radius-Reduktion ist architektonisch gelöst.
- Solo-Entwickler — Namespace-scoped RBAC isoliert den einzigen Operator vor sich selbst (kein praktischer Nutzen)
- CI/CD bereits gehärtet: SHA-gepinnte Actions, `permissions: contents: read`, Environment-gated Deploys
- Kein BAIT/BSI-Requirement für Pre-Production bei Solo-Dev (BAIT Kap. 8.6 gilt für Produktionsumgebung)
- DEV/TEST enthalten keine Kundendaten

**Opportunistische Umsetzung**: Beim Kubeconfig-Renewal (Ablauf 2026-05-28) kostenneutral mitnehmbar — neue ServiceAccounts + namespace-scoped RoleBindings statt erneuter Cluster-Admin-Kubeconfig.

**Aufwand bei Umsetzung**: 3 Stunden
**Risiko bei Nicht-Umsetzung**: Gering für DEV/TEST. Für PROD durch ADR-004 (eigener Cluster) abgedeckt.

### SEC-06: Container SecurityContext — Phase 1 ERLEDIGT (2026-03-08)

**Kritisches Finding**: Analyse der Onyx Helm Chart Templates (2026-03-08) ergab, dass mehrere Komponenten mit `privileged: true` + `runAsUser: 0` laufen. Ein privilegierter Container hat vollen Host-Kernel-Zugriff — faktisch keine Container-Isolation.

**Betrifft**: `deployment/helm/values/values-common.yaml` (alle Environments).

**Betroffene Komponenten:**

| Komponente | Aktueller Zustand | Risiko |
|------------|-------------------|--------|
| Celery (alle 8 Worker) | `privileged: true`, `runAsUser: 0` | HOCH |
| Model Server (inference + index) | `privileged: true`, `runAsUser: 0` | HOCH |
| Vespa | `privileged: true`, `runAsUser: 0` | HOCH |
| API Server | `runAsUser: 0` (nicht privileged) | Mittel |
| Web Server (Next.js) | UID 1001 (non-root) | OK |
| NGINX Ingress | `runAsNonRoot`, UID 101 | OK |

**BSI-Relevanz**: SYS.1.6.A10: "Privileged Mode SOLLTE NICHT verwendet werden." In einem Banking-Kontext wird dies in jedem Audit als Finding markiert.

**Technischer Hinweis**: Alle Chart-Templates unterstützen `securityContext`-Overrides via Values (`{{- toYaml .Values.<component>.securityContext | nindent 12 }}`). Kein Chart-Umbau nötig.

**Stufenplan:**
1. **Phase 1 (Quick Win, 1-2h):** `privileged: false` für Celery, Model Server, Vespa via `values-common.yaml`. `runAsUser: 0` beibehalten. Eliminiert das schlimmste Finding — `privileged` wird fast nie tatsächlich benötigt (Onyx setzt es als lazy Default).
   ```yaml
   # values-common.yaml — für jede betroffene Komponente:
   celery_shared:
     securityContext:
       privileged: false
   inferenceCapability:
     securityContext:
       privileged: false
   indexCapability:
     securityContext:
       privileged: false
   vespa:
     securityContext:
       privileged: false
   ```
2. **Phase 2 (vor PROD, 4-6h):** `runAsUser: 1001` + `runAsNonRoot: true` für API, Celery, Model Server. Dockerfiles definieren User `onyx` (UID 1001), nutzen ihn aber nie via `USER` Directive. `emptyDir` für `/tmp` (Celery Readiness/Liveness Probes schreiben nach `/tmp/onyx_k8s_*`). Vespa als dokumentierte Ausnahme (Upstream-Limitation: benötigt ggf. Root für `vm.max_map_count`).
3. **Phase 3 (P2, optional):** `readOnlyRootFilesystem: true` mit vollständigem emptyDir-Mapping. Diminishing Returns.

**Aufwand**: Phase 1: 1-2h | Phase 2: 4-6h | Phase 3: 3-4h
**Risiko bei Nicht-Umsetzung**: `privileged: true` ist inakzeptabel in einem Banking-Kontext. Selbst bei geringer Angriffswahrscheinlichkeit (internes System) ist es ein Audit-Blocker.

### SEC-07: Encryption-at-Rest — ERLEDIGT (2026-03-08)

**Verifiziert**: StackIT Managed Services bieten Encryption-at-Rest standardmäßig — nicht deaktivierbar.

- **PostgreSQL Flex**: Verschlüsselte SSD-Volumes (AES-256)
- **Object Storage**: Server-Side Encryption (SSE) als Default
- **Nachweis**: Dokumentiert in `docs/sicherheitskonzept.md`, Abschnitt SEC-07

**Kein Handlungsbedarf.** Verschlüsselung ist plattformseitig garantiert.

---

## Quellen

- [StackIT Terraform Provider](https://registry.terraform.io/providers/stackitcloud/stackit/latest/docs)
- [StackIT CLI](https://github.com/stackitcloud/stackit-cli)
- [StackIT AI Model Serving](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/)
- Onyx Helm Chart: `deployment/helm/charts/onyx/values.yaml`
- [Technische Referenz](stackit-infrastruktur.md)
