# StackIT Container Registry — Konzepte & Authentifizierung

**Stand**: Februar 2026
**Bezug**: [Implementierungsplan](stackit-implementierungsplan.md) | [CI/CD Workflow](../../.github/workflows/stackit-deploy.yml)

---

## Begriffe im Vergleich

| Begriff | Was ist das? | Wo zu finden? | Beispielwert |
|---------|-------------|---------------|--------------|
| **StackIT Project ID** | UUID des StackIT-Cloud-Projekts. Identifiziert alle Ressourcen (SKE, PG Flex, Object Storage, AI Model Serving) | StackIT Portal → Dashboard → URL | `b3d2a04e-46de-48bc-abc6-c4dfab38c2cd` |
| **Container Registry Projekt** | Eigenes Projekt innerhalb der Registry. Hat eigene Repositories, User, Robot Accounts. **Nicht identisch mit der Project ID.** | Container Registry UI → Projekte | `voeb-chatbot` |
| **Repository** | Ein Image-Name innerhalb eines Registry-Projekts | Container Registry UI → Projekt → Repositories | `voeb-chatbot/onyx-backend` |
| **Robot Account** | Technischer User für CI/CD mit eigenem Token. Nicht an eine Person gebunden. | Container Registry UI → Projekt → Robot Accounts | `robot$voeb-chatbot+github-ci` |

### Beziehung zwischen den Konzepten

```
StackIT Cloud
├── Project (b3d2a04e-...)
│   ├── SKE Cluster (vob-chatbot)
│   ├── PostgreSQL Flex (vob-dev)
│   ├── Object Storage (vob-dev)
│   └── AI Model Serving (GPT-OSS, Qwen3-VL, ...)
│
└── Container Registry (registry.onstackit.cloud)
    └── Projekt: voeb-chatbot          ← EIGENES Projektsystem
        ├── Repository: onyx-backend
        ├── Repository: onyx-web-server
        ├── Repository: onyx-model-server
        └── Robot Account: github-ci
```

> **Wichtig:** Die Container Registry hat ein **eigenes Projektsystem**, unabhängig von der StackIT Project ID.
> Die Project ID (UUID) wird in der Registry-URL **nicht** verwendet.
> Stattdessen wird der **Projektname** in der Registry genutzt.

---

## Image-URL-Struktur

```
registry.onstackit.cloud / voeb-chatbot / onyx-backend : abc1234
│                          │               │               │
Registry-Host              Projekt-Name    Image-Name      Tag (Git SHA)
```

Unsere 3 Images:

| Image | Dockerfile | Beschreibung |
|-------|-----------|--------------|
| `voeb-chatbot/onyx-backend` | `backend/Dockerfile` | API Server + Celery Worker |
| `voeb-chatbot/onyx-web-server` | `web/Dockerfile` | Next.js Frontend |
| `voeb-chatbot/onyx-model-server` | `backend/Dockerfile.model_server` | Embedding/Inference Model Server |

---

## Authentifizierung

### Methode 1: Persönlicher Login (Entwicklung)

Für lokales `docker push/pull`:

```bash
docker login registry.onstackit.cloud
# Username: StackIT-Email (z.B. n.ivanov@coffeestudios.de)
# Password: CLI Secret (Portal → User Profile → CLA Secret)
```

**Nicht** für CI/CD geeignet — an Person gebunden, Passwort kann rotieren.

### Methode 2: Robot Account (CI/CD)

Für automatisierte Pipelines:

```bash
docker login registry.onstackit.cloud \
  -u 'robot$voeb-chatbot+github-ci' \
  -p '<ROBOT_TOKEN>'
```

> **Achtung:** Username enthält `$`-Zeichen — in Bash mit einfachen Anführungszeichen oder `\$` escapen.

#### Robot Account erstellen

1. Container Registry UI → Projekt `voeb-chatbot` → Tab **Robot Accounts**
2. **New Robot Account** klicken
3. Name: `github-ci`, Ablauf: z.B. 365 Tage
4. Berechtigungen: `repository:push` + `repository:pull`
5. **Token sofort kopieren** — wird nur einmal angezeigt!

#### Ergebnis

| Feld | Wert | GitHub Secret |
|------|------|---------------|
| Robot Account Name | `robot$voeb-chatbot+github-ci` | `STACKIT_REGISTRY_USER` |
| Robot Account Token | (einmalig angezeigt) | `STACKIT_REGISTRY_PASSWORD` |

---

## Mapping: Was → Welches Secret?

### Übersicht aller Credentials

| Credential | Quelle | Verwendung | GitHub Secret |
|-----------|--------|-----------|---------------|
| Registry Robot Username | Container Registry UI | Docker Login in CI | `STACKIT_REGISTRY_USER` |
| Registry Robot Token | Container Registry UI | Docker Login in CI | `STACKIT_REGISTRY_PASSWORD` |
| Kubeconfig (base64) | `stackit ske kubeconfig create` | kubectl/helm in CI | `STACKIT_KUBECONFIG` |
| PG App-User Passwort | `terraform output -raw pg_password` | Helm Values | `POSTGRES_PASSWORD` (env: dev) |
| S3 Access Key ID | `stackit object-storage credentials` | Helm Values | `S3_ACCESS_KEY_ID` (env: dev) |
| S3 Secret Access Key | `stackit object-storage credentials` | Helm Values | `S3_SECRET_ACCESS_KEY` (env: dev) |
| PG Readonly Passwort | `terraform output` (readonly user) | Helm Values | `DB_READONLY_PASSWORD` (env: dev) |

### Was ist NICHT als Secret nötig?

| Wert | Grund |
|------|-------|
| StackIT Project ID (`b3d2a04e-...`) | Wird im Workflow nicht referenziert. Registry nutzt Projektnamen. |
| SA Credentials (`voeb-terraform`) | Nur für Terraform/CLI, nicht für CI/CD Pipeline. |
| StackIT AI Model Serving Token | Wird über Onyx Admin UI konfiguriert, nicht über CI/CD. |

---

## Kubeconfig-Ablauf

Die Kubeconfig für SKE wird mit begrenzter Gültigkeit erstellt:

```bash
stackit auth activate-service-account \
  --service-account-key-path ~/.stackit/voeb-terraform-credentials.json

echo "y" | stackit ske kubeconfig create vob-chatbot \
  --project-id b3d2a04e-46de-48bc-abc6-c4dfab38c2cd \
  --expiration 90d

# Base64-encoden und als GitHub Secret setzen:
base64 -i ~/.kube/config | gh secret set STACKIT_KUBECONFIG
```

> **Erinnerung:** Kubeconfig muss vor Ablauf erneuert werden (alle 90 Tage).
> Langfristige Verbesserung: StackIT CLI im CI-Workflow installieren und Kubeconfig dynamisch erzeugen.

---

## Zusammenhang mit Helm Deploy

Die CI/CD Pipeline (`stackit-deploy.yml`) nutzt die Registry wie folgt:

```
Build-Job:
  docker push registry.onstackit.cloud/voeb-chatbot/onyx-backend:<git-sha>

Deploy-Job:
  helm upgrade --install onyx-dev ... \
    --set "api.image.repository=registry.onstackit.cloud/voeb-chatbot/onyx-backend"
```

Der Helm Chart zieht dann die Images aus der Registry. Dafür muss im K8s Namespace ein **Image Pull Secret** existieren:

```bash
kubectl create secret docker-registry stackit-registry \
  --namespace=onyx-dev \
  --docker-server=registry.onstackit.cloud \
  --docker-username='robot$voeb-chatbot+github-ci' \
  --docker-password='<ROBOT_TOKEN>'
```

> **Hinweis:** Das Image Pull Secret auf dem Cluster muss die **gleichen** Registry-Credentials nutzen
> wie die CI/CD Pipeline. Wenn ein Robot Account erstellt wird, muss das Secret auf dem Cluster
> aktualisiert werden (sofern es zuvor andere Credentials verwendet hat).
