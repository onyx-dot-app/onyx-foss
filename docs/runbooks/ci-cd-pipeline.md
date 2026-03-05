# CI/CD Pipeline — Runbook

> **Workflow**: `.github/workflows/stackit-deploy.yml`
> **Verifiziert**: 2026-03-02 (Run #5, Commit `ea70a11`)
> **Letzte Änderung**: 2026-03-02

---

## Voraussetzungen

- Zugriff auf GitHub-Repo `CCJ-Development/voeb-chatbot`
- `gh` CLI authentifiziert (oder GitHub UI)
- Für Cluster-Zugriff: `kubectl` mit gültiger Kubeconfig (Ablauf: **2026-05-28**)

---

## 1. Pipeline-Architektur

### Übersicht

```
Push auf main / workflow_dispatch
        │
    ┌───▼───┐
    │prepare│  (6s) Image Tag bestimmen (Git SHA oder manuell)
    └───┬───┘
        │
   ┌────┴────┐
   ▼         ▼
┌──────┐  ┌──────┐
│build-│  │build-│  (~7 Min, parallel)
│back- │  │front-│
│end   │  │end   │
└──┬───┘  └──┬───┘
   │         │
   └────┬────┘
        │
   ┌────▼────┐
   │deploy-  │  (~2 Min) Helm upgrade + Smoke Test
   │{env}    │
   └─────────┘
```

### Was wird gebaut

| Image | Quelle | Registry | Warum |
|-------|--------|----------|-------|
| `onyx-backend` | `./backend` Dockerfile | StackIT Registry | Unser Fork-Code (Extensions, Config) |
| `onyx-web-server` | `./web` Dockerfile | StackIT Registry | Unser Fork-Code (Frontend) |
| `onyx-model-server` | Docker Hub Upstream | `docker.io/onyxdotapp` | Identisch mit Upstream — kein eigener Build nötig |

### Was wird NICHT gebaut

Der **Model Server** wird nicht gebaut. Er nutzt das offizielle Onyx-Image von Docker Hub, gepinnt auf Version `v2.9.8`. Begründung:

1. Wir ändern nichts am Embedding/Reranking-Code
2. Spart ~12 Min Build-Zeit
3. Eliminiert ImagePullBackOff-Probleme mit der StackIT Registry

> **Bei Upstream-Update**: Tag in `MODEL_SERVER_TAG` im Workflow aktualisieren. Vorher prüfen ob das neue Image kompatibel ist.

---

## 2. Deploy auslösen

### Automatisch (DEV)

Push auf `main` löst automatisch DEV-Deploy aus:
```bash
git push origin main
```

Ausnahme: Änderungen nur an `docs/**`, `*.md`, `.claude/**` lösen keinen Build aus.

### Manuell (DEV/TEST/PROD)

```bash
# DEV
gh workflow run "StackIT Build & Deploy" \
  --repo CCJ-Development/voeb-chatbot \
  --ref main \
  -f environment=dev

# TEST
gh workflow run "StackIT Build & Deploy" \
  --repo CCJ-Development/voeb-chatbot \
  --ref main \
  -f environment=test

# PROD (benötigt Required Reviewers in GitHub Settings)
gh workflow run "StackIT Build & Deploy" \
  --repo CCJ-Development/voeb-chatbot \
  --ref main \
  -f environment=prod
```

### Mit spezifischem Image-Tag

```bash
gh workflow run "StackIT Build & Deploy" \
  --repo CCJ-Development/voeb-chatbot \
  --ref main \
  -f environment=dev \
  -f image_tag=ea70a11
```

---

## 3. Deploy-Status prüfen

```bash
# Letzten Run anzeigen
gh run list --workflow="StackIT Build & Deploy" \
  --repo CCJ-Development/voeb-chatbot --limit 3

# Details eines Runs
gh run view <RUN_ID> --repo CCJ-Development/voeb-chatbot

# Logs eines Jobs
gh run view --job=<JOB_ID> --repo CCJ-Development/voeb-chatbot --log
```

### Auf dem Cluster

```bash
# Pod-Status
kubectl get pods -n onyx-dev

# Welche Images laufen
kubectl get pods -n onyx-dev \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# API Health Check
curl http://188.34.74.187/api/health
```

---

## 4. Rollback

### Automatisch (TEST/PROD)

TEST und PROD verwenden `--atomic`. Bei Fehler rollt Helm automatisch auf den vorherigen Release zurück.

### Manuell (DEV)

DEV verwendet kein `--atomic` (wegen des kubectl-Patches). Manueller Rollback:

```bash
# Letzte Helm Releases anzeigen
helm history onyx-dev -n onyx-dev

# Auf vorherige Revision zurückrollen
helm rollback onyx-dev <REVISION> -n onyx-dev

# Oder: Auf einen bestimmten Image-Tag deployen
gh workflow run "StackIT Build & Deploy" \
  --repo CCJ-Development/voeb-chatbot \
  --ref main \
  -f environment=dev \
  -f image_tag=<FUNKTIONIERENDER_TAG>
```

### Notfall: Direkter Image-Wechsel

Ohne Pipeline, direkt auf dem Cluster:

```bash
kubectl set image deployment/onyx-dev-api-server \
  api-server=registry.onstackit.cloud/voeb-chatbot/onyx-backend:<TAG> \
  -n onyx-dev
```

---

## 5. Secrets verwalten

### Übersicht

| Secret | Scope | Beschreibung |
|--------|-------|-------------|
| `STACKIT_REGISTRY_USER` | Global | Robot Account Name |
| `STACKIT_REGISTRY_PASSWORD` | Global | Robot Account Token |
| `STACKIT_KUBECONFIG` | Global | Base64-encoded, **Ablauf: 2026-05-28** |
| `POSTGRES_PASSWORD` | Per Environment | PG Flex App-User Passwort |
| `S3_ACCESS_KEY_ID` | Per Environment | StackIT Object Storage |
| `S3_SECRET_ACCESS_KEY` | Per Environment | StackIT Object Storage |
| `DB_READONLY_PASSWORD` | Per Environment | PG Readonly User |
| `REDIS_PASSWORD` | Per Environment | Redis Standalone |

### Secret aktualisieren

```bash
# Global
gh secret set STACKIT_KUBECONFIG \
  --repo CCJ-Development/voeb-chatbot \
  --body "$(base64 < ~/.kube/config)"

# Per Environment
gh secret set POSTGRES_PASSWORD \
  --repo CCJ-Development/voeb-chatbot \
  --env dev \
  --body "neues-passwort"
```

### Kubeconfig erneuern

Die Kubeconfig läuft am **2026-05-28** ab. Vorher erneuern:

```bash
# Neue Kubeconfig von StackIT holen
stackit ske kubeconfig create voeb-chatbot-devtest \
  --project-id b3d2a04e-46de-48bc-abc6-c4dfab38c2cd \
  --login --expiration 90d

# Als GitHub Secret setzen
gh secret set STACKIT_KUBECONFIG \
  --repo CCJ-Development/voeb-chatbot \
  --body "$(base64 < ~/.kube/config)"

# Neues Ablaufdatum in Workflow-Header und MEMORY.md dokumentieren
```

---

## 6. Troubleshooting

### Pipeline schlägt fehl: Build

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| `unauthorized` bei Registry Login | Robot Account Token abgelaufen | Neues Token in StackIT Portal erstellen, `STACKIT_REGISTRY_PASSWORD` aktualisieren |
| Build Timeout | GHA-Cache ungültig nach großer Änderung | Manuell Cache löschen: GitHub UI → Actions → Caches |
| `COPY failed: file not found` | Dockerfile-Kontext falsch | `context:` im Workflow prüfen (`./backend` bzw. `./web`) |

### Pipeline schlägt fehl: Deploy

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| `helm dependency build` Fehler | Helm Repo nicht erreichbar | Prüfen ob Repo-URLs noch aktuell sind (Chart-Dependencies ändern sich upstream) |
| `Insufficient CPU` | Alte + neue Pods gleichzeitig auf Single Node | Recreate-Strategie-Patch prüfen. Ist nur für DEV relevant |
| `UPGRADE FAILED: timed out` | Pods kommen nicht hoch | Logs prüfen: `kubectl logs deployment/<name> -n onyx-dev` |

### Pods starten nicht

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| `CrashLoopBackOff` API-Server | `LICENSE_ENFORCEMENT_ENABLED` nicht auf `"false"` | `kubectl get configmap env-configmap -n onyx-dev -o yaml \| grep LICENSE` |
| `ImagePullBackOff` | Registry-Credentials ungültig oder Image-Tag falsch | Image Pull Secret prüfen: `kubectl get secret stackit-registry -n onyx-dev -o yaml` |
| `Pending` | Nicht genug Ressourcen auf Node | `kubectl describe pod <name> -n onyx-dev` → Events prüfen |
| `OOMKilled` | Memory Limit zu niedrig | Resource Limits in `values-dev.yaml` erhöhen |

### Smoke Test schlägt fehl

Der Smoke Test prüft `/api/health` mit 12 Versuchen (alle 10s = 2 Min Timeout).

```bash
# Manuell prüfen
curl -v http://188.34.74.187/api/health

# Pod-Logs ansehen
kubectl logs deployment/onyx-dev-api-server -n onyx-dev --tail=50

# Wenn Ingress-Problem: Nginx-Logs prüfen
kubectl logs deployment/onyx-dev-nginx-controller -n onyx-dev --tail=50
```

---

## 7. Entscheidungslog

Dokumentation der "Warum"-Fragen für Audits und Nachvollziehbarkeit.

### Warum SHA-gepinnte Actions?

GitHub Actions mit Major-Version-Tags (`@v4`) können jederzeit vom Maintainer geändert werden. Ein kompromittiertes Action-Repository könnte Code injizieren, der Secrets exfiltriert. SHA-Pinning fixiert den exakten Stand und erfordert bewusste Updates. Relevant für: BAIT App. 4.3.2 (Nachvollziehbarkeit), BSI-Grundschutz APP.6.

### Warum kein eigener Model Server Build?

Der Onyx Model Server (Embedding + Reranking) ist reiner Upstream-Code. Wir ändern nichts daran. Ein eigener Build:
- Dauert ~12 Minuten
- Erzeugt ein identisches Image
- Verursachte ImagePullBackOff (StackIT Registry Latenz)

Docker Hub Image ist öffentlich, schnell, und mit `v2.9.8` gepinnt.

### Warum Recreate statt RollingUpdate (DEV)?

Der DEV-Cluster hat 1 Node (g1a.4d, 4 vCPU). RollingUpdate startet neue Pods neben den alten — dafür reicht die CPU nicht. Recreate stoppt zuerst die alten, dann starten die neuen. Downtime ist für DEV akzeptabel.

### Warum `LICENSE_ENFORCEMENT_ENABLED: "false"`?

Onyx FOSS hat seit einer neueren Version den Default `"true"` für diese Variable. Das aktiviert Enterprise-Edition-Code-Pfade, die das Modul `onyx.server.tenants` importieren. Dieses Modul existiert nur im proprietären EE-Repository. Ohne die explizite Deaktivierung crasht der API-Server mit `ModuleNotFoundError`.

### Warum kein `--atomic` für DEV?

DEV verwendet einen kubectl-Patch nach dem Helm Deploy (Recreate-Strategie). `--atomic` würde bei Timeout zurückrollen, bevor der Patch angewendet wird. Stattdessen: manuelles Rollout-Monitoring mit echtem Error-Reporting.

### Warum Redis-Passwort als GitHub Secret?

War vorher hardcoded in `values-dev.yaml` — steht im Git-Repository. Credentials gehören nicht in Git, auch nicht für DEV. Alle anderen Credentials (PG, S3) waren bereits als Secrets konfiguriert.

---

## 8. Wartung

### Regelmäßig prüfen

| Was | Wann | Wie |
|-----|------|-----|
| Kubeconfig-Ablauf | Monatlich | Datum im Workflow-Header prüfen (aktuell: 2026-05-28) |
| GitHub Actions Updates | Bei Dependabot-Alert oder monatlich | SHA im Workflow gegen neuestes Release-Tag prüfen |
| Model Server Version | Bei Onyx-Release | Docker Hub Tags prüfen, `MODEL_SERVER_TAG` aktualisieren |
| Robot Account Token | Bei Ablauf | StackIT Portal → Container Registry → Robot Account |
| Helm Chart Updates | Bei Upstream-Merge | `helm dependency build` nach Merge testen |

### GitHub Actions SHA aktualisieren

```bash
# Aktuellen SHA für ein Action-Tag ermitteln
gh api repos/actions/checkout/git/ref/tags/v4 --jq '.object.sha'

# Im Workflow ersetzen:
# ALT: uses: actions/checkout@<alter-sha> # v4
# NEU: uses: actions/checkout@<neuer-sha> # v4
```
