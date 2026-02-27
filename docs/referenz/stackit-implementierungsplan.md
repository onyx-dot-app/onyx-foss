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
| 1× Worker Node | g1a.2d (2 vCPU, 8 GB RAM) | ~70 EUR/Monat |
| 1× PostgreSQL Flex 2.4 | Single (2 CPU, 4 GB, 20 GB SSD) | ~30 EUR/Monat |
| 1× Object Storage Bucket | `vob-dev` | ~5 EUR/Monat |
| **TOTAL DEV** | | **~180 EUR/Monat** |

---

## Architekturentscheidungen

| Helm Default | StackIT-Entscheidung | Grund |
|-------------|---------------------|-------|
| CloudNativePG (in-cluster) | **StackIT Managed PostgreSQL Flex** (extern) | Backups, PITR managed |
| MinIO (in-cluster) | **StackIT Object Storage** (extern) | S3-kompatibel, kein Overhead |
| Docker Hub Images | **StackIT Container Registry** | Datensouveränität |
| OpenAI / LiteLLM | **StackIT AI Model Serving** | Daten bleiben in DE |
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
        versions.tf                   ← Provider stackitcloud/stackit ~> 0.56
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
# Docker Login
docker login registry.onstackit.cloud
# Username: StackIT-Email
# Password: CLI Secret (Portal → User Profile)

# Image-Naming:
# registry.onstackit.cloud/<PROJECT_ID>/onyx-backend:<tag>
# registry.onstackit.cloud/<PROJECT_ID>/onyx-web-server:<tag>
# registry.onstackit.cloud/<PROJECT_ID>/onyx-model-server:<tag>
```

### 1.4 GitHub Secrets anlegen

| Secret | Wert |
|--------|------|
| `STACKIT_PROJECT_ID` | Project UUID aus Portal |
| `STACKIT_SERVICE_ACCOUNT_KEY` | Inhalt von credentials.json |
| `STACKIT_REGISTRY_USER` | Registry Username |
| `STACKIT_REGISTRY_PASSWORD` | Registry Password |
| `STACKIT_KUBECONFIG` | Base64-encoded Kubeconfig (nach Phase 2) |

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
- 1 Node Pool `devtest` mit 1× g1a.2d
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

> **Status**: ⏭️ **Nächster Schritt**

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

---

## Phase 4: Helm Deploy (DEV)

> **Status**: ⏳ Wartet auf Phase 3

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
  --set "global.version=latest" \
  --wait --timeout 10m

# Verifizieren
kubectl get pods -n onyx-dev
kubectl get svc -n onyx-dev
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
| **TOTAL DEV** | **~1.5 CPU** | **~4.4 Gi** | |

**Verfügbar (1× g1a.2d)**: 2 CPU / 8 GB RAM → ausreichend für DEV. Bei Bedarf auf g1a.4d skalierbar.

---

## Phase 5: CI/CD Pipeline

> **Status**: ⏳ Pipeline erstellt, GitHub Secrets noch nicht gesetzt

Die Pipeline `.github/workflows/stackit-deploy.yml` ist bereits erstellt.

**Ablauf**:
1. Push auf `develop` → Build-Job baut 3 Docker Images
2. Images werden in StackIT Container Registry gepusht
3. Helm Deploy in `onyx-dev` Namespace

**Voraussetzung**: GitHub Secrets aus Phase 1.3 müssen gesetzt sein.

---

## Phase 6: LLM-Integration (nach funktionierendem Deploy)

> **Status**: 🔒 Blockiert — StackIT AI Model Serving API Keys ausstehend

StackIT AI Model Serving bietet eine OpenAI-kompatible API.
Onyx unterstützt das nativ über LiteLLM.

**Konfiguration über Onyx Admin UI** (nach Deploy):

| Feld | Wert |
|------|------|
| API Endpoint | `https://ai-model-serving.eu01.onstackit.cloud/v1` |
| API Key | StackIT Service Account Token |
| Model | `mistral-large-latest` |
| Embedding Model | StackIT Embedding Plus |

**Token-Kalkulation DEV** (5 User, ~550 Queries/Monat): ~2 EUR/Monat LLM-Kosten.

---

## Validierung (DEV)

| Kriterium | Test | Status |
|-----------|------|--------|
| K8s Cluster läuft | `kubectl get nodes` → Ready | [x] ✅ (2026-02-27 verifiziert) |
| PostgreSQL erreichbar | `psql -h <PG_HOST> -U onyx_app -c "SELECT 1"` | [ ] |
| Vespa deployed | `kubectl get pods -n onyx-dev -l app=vespa` | [ ] |
| Object Storage | `aws s3 ls s3://vob-dev/ --endpoint-url https://...` | [ ] |
| Onyx UI erreichbar | Browser → LoadBalancer IP | [ ] |
| CI/CD funktioniert | Push auf develop → Pods updated | [ ] |

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
| 6 | StackIT AI Model Serving API Keys | StackIT | Blockiert |
| 7 | DNS-Zone | VÖB IT | Offen |
| 8 | Entra ID Credentials | VÖB IT | Blockiert |
| 9 | Storage Class Name prüfen | Bei `terraform plan` sichtbar | ✅ `premium-perf2-stackit` (bestätigt) |

---

## Quellen

- [StackIT Terraform Provider](https://registry.terraform.io/providers/stackitcloud/stackit/latest/docs)
- [StackIT CLI](https://github.com/stackitcloud/stackit-cli)
- [StackIT AI Model Serving](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/)
- Onyx Helm Chart: `deployment/helm/charts/onyx/values.yaml`
- [Technische Referenz](stackit-infrastruktur.md)
