# StackIT Implementierungsplan — VÖB Service Chatbot

**Stand**: Februar 2026
**Erstellt von**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Bezug**: [Technische Referenz](stackit-infrastruktur.md) | [Meilensteinplan](../abnahme/meilensteinplan.md)

> **Scope dieses Plans: DEV Environment.**
> TEST und PROD werden erst aufgesetzt, wenn DEV stabil läuft.
> PROD-Spezifikationen sind in der [Technischen Referenz](stackit-infrastruktur.md) dokumentiert.

---

## Was wird provisioniert?

| Ressource | Spec | Geschätzte Kosten |
|-----------|------|-------------------|
| 1× SKE Cluster | 1 Node Pool (`devtest`) | ~72 EUR/Monat |
| 1× Worker Node | g1a.4d (4 vCPU, 16 GB RAM) | ~142 EUR/Monat |
| 1× PostgreSQL Flex 2.4 | Single (2 CPU, 4 GB, 20 GB SSD) | ~30 EUR/Monat |
| 1× Object Storage Bucket | `vob-dev` | ~5 EUR/Monat |
| **TOTAL DEV** | | **~250 EUR/Monat** |

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
      dev/                            ← NEU
        main.tf                       ← Ruft Modul mit DEV-Werten auf
        backend.tf                    ← Local State (Remote vorbereitet)
        terraform.tfvars              ← Leer (project_id per CLI)
  helm/
    charts/onyx/                      ← BESTEHEND — READ-ONLY, nicht anfassen
    values/                           ← NEU
      values-common.yaml              ← PG aus, MinIO aus, Vespa+Redis an
      values-dev.yaml                 ← 1 Replica pro Service, Lightweight

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
- 1 Node Pool `devtest` mit 1× g1a.4d
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

> **Status**: ✅ **Abgeschlossen** (2026-02-27). Alle 10 Pods Running, API Health OK, UI erreichbar unter `http://188.34.74.187`.

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
| Redis Operator | 500m | — | 1 |
| **TOTAL DEV (onyx-dev)** | **~2.1 CPU** | **~4.7 Gi** | |
| kube-system (Calico, DNS, VPN, Metrics) | ~1.4 CPU | ~2 Gi | — |
| **TOTAL Node** | **~3.5 CPU** | **~6.7 Gi** | |

**Verfügbar (1× g1a.4d)**: 4 CPU / 16 GB RAM. ~1.4 CPU werden von kube-system (Calico, CoreDNS, VPN, Metrics) beansprucht.

---

## Phase 5: CI/CD Pipeline

> **Status**: ✅ GitHub Secrets gesetzt, Robot Account erstellt (2026-03-02). Drei Test-Runs durchgeführt:
> - Run #1: Build OK, Deploy fehlgeschlagen (fehlender `helm dependency build`-Step) → Fix: `f3a22017f`
> - Run #2: Build OK, Deploy fehlgeschlagen (Helm Repos nicht registriert) → Fix: `64c9c7aca`
> - Run #3: Läuft (2026-03-02) — beide Fixes angewendet
> - Upstream-Workflows: 21 Onyx-Workflows deaktiviert, nur StackIT Deploy + Upstream Check aktiv

Die Pipeline `.github/workflows/stackit-deploy.yml` ist bereits erstellt.

**Ablauf**:
1. Push auf `develop` → Build-Job baut 3 Docker Images
2. Images werden in StackIT Container Registry gepusht
3. Helm Deploy in `onyx-dev` Namespace

**Voraussetzung**: GitHub Secrets aus Phase 1.4 müssen gesetzt sein.

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

> ⏳ Noch nicht konfiguriert.

Gleicher Provider, gleiche API Base, gleicher Auth Token. Separater Provider-Eintrag in der Admin UI.

| Feld | Wert |
|------|------|
| Display Name | `StackIT Embedding - Dev` |
| Provider Name | `openai` |
| API Key | Gleicher Auth Token |
| API Base | `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1` |
| Model Name | `intfloat/e5-mistral-7b-instruct` |
| Default Model | `intfloat/e5-mistral-7b-instruct` |

**Modell-Details E5 Mistral 7B:** 4096 Dimensionen, max 4096 Tokens, 0,02 EUR / 1M Tokens.

### 6.4 Weitere verfügbare Modelle (Fallback / Alternativen)

| Modell | StackIT Model ID | Kontext | Status |
|--------|------------------|---------|--------|
| **GPT-OSS 120B** | `openai/gpt-oss-120b` | 131K | ✅ Verifiziert |
| **Qwen3-VL 235B** | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` | 218K | ✅ Verifiziert |
| Llama 3.3 70B | `cortecs/Llama-3.3-70B-Instruct-FP8-Dynamic` | 128K | Verfügbar |
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

## Validierung (DEV)

| Kriterium | Test | Status |
|-----------|------|--------|
| K8s Cluster läuft | `kubectl get nodes` → Ready, g1a.4d | [x] ✅ (2026-02-27) |
| PostgreSQL erreichbar | DB `onyx` existiert, Alembic-Migrationen laufen | [x] ✅ (2026-02-27) |
| Vespa deployed | Pod Running, Application Package deployed | [x] ✅ (2026-02-27) |
| Redis deployed | Pod Running, Celery Beat/Worker verbunden | [x] ✅ (2026-02-27) |
| Object Storage | Credentials aktiv, api-server startet ohne Fehler | [x] ✅ (2026-02-27) |
| API Health | `curl http://188.34.74.187/api/health` → `{"success":true}` | [x] ✅ (2026-02-27) |
| Onyx UI erreichbar | `http://188.34.74.187/auth/login` → Login-Seite | [x] ✅ (2026-02-27) |
| LLM Chat-Modell (GPT-OSS) | GPT-OSS 120B antwortet über Onyx Chat | [x] ✅ (2026-02-27) |
| LLM Chat-Modell (Qwen3-VL) | Qwen3-VL 235B antwortet über Onyx Chat | [x] ✅ (2026-02-27) |
| LLM Embedding-Modell | E5 Mistral 7B für Dokumenten-Suche | [ ] ⏳ |
| CI/CD funktioniert | Push auf develop → Pods updated | [ ] ⏳ (Run #3 läuft, Helm-Fixes angewendet) |

---

## Nächste Schritte (nach stabilem DEV)

| Schritt | Wann | Was |
|---------|------|-----|
| TEST Environment | Nach DEV-Validierung | Eigener PG Flex 2.4 + Bucket `vob-test` + Namespace `onyx-test` |
| Entra ID (Auth) | Sobald Credentials von VÖB | `AUTH_TYPE: oidc` in Helm Values |
| PROD Node Pool | Vor Go-Live | 2× g1a.4d Nodes + PG Flex 4.8 HA + Namespace `onyx-prod` |
| TLS/HTTPS | Nach DNS-Setup | Let's Encrypt oder StackIT-CA |
| Monitoring | Phase M5 | Prometheus/Grafana Stack |

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
| 10 | DNS-Zone (`dev.chatbot.voeb.example.com` → `188.34.74.187`) | VÖB IT | Offen |
| 11 | Entra ID Credentials | VÖB IT | Blockiert |
| 12 | Storage Class Name prüfen | Bei `terraform plan` sichtbar | ✅ `premium-perf2-stackit` (bestätigt) |
| 13 | CI/CD Pipeline Helm-Fixes | Niko | ✅ Erledigt (2026-03-02) — `f3a22017f` + `64c9c7aca` |
| 14 | Upstream-Workflows deaktivieren | Niko | ✅ Erledigt (2026-03-02) — 21 Workflows disabled via API |

---

## Quellen

- [StackIT Terraform Provider](https://registry.terraform.io/providers/stackitcloud/stackit/latest/docs)
- [StackIT CLI](https://github.com/stackitcloud/stackit-cli)
- [StackIT AI Model Serving](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/)
- Onyx Helm Chart: `deployment/helm/charts/onyx/values.yaml`
- [Technische Referenz](stackit-infrastruktur.md)
