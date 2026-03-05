# Runbook: Helm Deploy — Betriebswissen

**Zuletzt verifiziert:** 2026-02-27
**Ausgeführt von:** Nikolaj Ivanov

---

## Voraussetzungen

- SKE Cluster läuft (`kubectl get nodes` → Ready)
- Namespace `onyx-dev` existiert mit Image Pull Secret
- PostgreSQL Flex: Datenbank `onyx` existiert (siehe [PostgreSQL Runbook](./stackit-postgresql.md))
- Object Storage: Credentials erstellt (siehe unten)
- Redis Operator installiert (im `default` Namespace, verwaltet Redis-Pods in allen Namespaces):
  ```bash
  helm install redis ot-helm/redis-operator --namespace default
  ```

---

## Deploy-Befehl

```bash
helm upgrade --install onyx-dev \
  deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  -f deployment/helm/values/values-dev-secrets.yaml
```

Die Datei `values-dev-secrets.yaml` ist gitignored und enthält:
- PostgreSQL Passwort
- Object Storage Credentials (S3 Access Key / Secret Key)
- DB Readonly Password

---

## Object Storage Credentials anlegen

Credentials werden über die StackIT CLI erstellt (nicht über Terraform):

```bash
# Credentials-Gruppe anzeigen
stackit object-storage credentials-group list --project-id <PROJECT_ID>

# Credentials erstellen (Bestätigung mit "y")
echo "y" | stackit object-storage credentials create \
  --project-id <PROJECT_ID> \
  --credentials-group-id <GROUP_ID>
```

Ausgabe enthält `Access Key ID` und `Secret Access Key`. Diese in `values-dev-secrets.yaml` eintragen:

```yaml
auth:
  objectstorage:
    values:
      s3_aws_access_key_id: "<ACCESS_KEY>"
      s3_aws_secret_access_key: "<SECRET_KEY>"
```

---

## Redis: Service-Name Mismatch

Der Onyx Helm Chart generiert `REDIS_HOST: <release>-master` (Bitnami-Konvention). Der OT Container Kit Redis Operator erstellt den Service aber als `<release>` (ohne `-master`).

**Lösung:** `REDIS_HOST` explizit in `values-dev.yaml` überschreiben:

```yaml
configMap:
  REDIS_HOST: "onyx-dev"
```

**Validierung:**
```bash
# DNS prüfen (muss auflösen)
kubectl run dns-test --rm -it --restart=Never --namespace onyx-dev \
  --image=busybox -- nslookup onyx-dev.onyx-dev.svc.cluster.local

# Darf NICHT auflösen (das ist der falsche Name)
kubectl run dns-test2 --rm -it --restart=Never --namespace onyx-dev \
  --image=busybox -- nslookup onyx-dev-master.onyx-dev.svc.cluster.local
```

---

## Rolling Update Deadlock (1-Node Cluster)

### Problem

Bei `helm upgrade` erstellt Kubernetes neue ReplicaSets (Rolling Update). Auf einem 1-Node Cluster mit knappem CPU-Budget können die neuen Pods nicht schedulen, weil die alten noch laufen. Ergebnis: Deadlock — alte Pods warten auf neue, neue können nicht starten.

### Erkennung

```bash
kubectl get pods -n onyx-dev
# Symptom: Neue Pods "Pending", alte Pods "Running"
# kubectl describe pod <pending-pod> → "Insufficient cpu"
```

### Sofort-Lösung

Alte ReplicaSets manuell auf 0 skalieren:

```bash
# Alte RS identifizieren (READY > 0, aber nicht die neueste)
kubectl get rs -n onyx-dev

# Beispiel: Alte RS runterskalieren
kubectl scale rs <old-rs-name> --replicas=0 -n onyx-dev
```

### Langfristige Lösung (DEV)

Deployment-Strategie auf `Recreate` setzen (akzeptabel für DEV, kein Zero-Downtime nötig). Das muss im Helm Chart oder per Post-Renderer gemacht werden.

---

## AUTH_TYPE Deprecation

`AUTH_TYPE=disabled` wird ab dieser Chart-Version nicht mehr unterstützt. Onyx fällt automatisch auf `basic` zurück (Email/Passwort-Login).

**Empfehlung:** In `values-dev.yaml` explizit setzen:
```yaml
configMap:
  AUTH_TYPE: "basic"
```

Für Phase 3 (Entra ID): `AUTH_TYPE: "oidc"`.

---

## Startup-Reihenfolge

Onyx-Pods haben interne Readiness-Probes die auf andere Services warten:

1. **PostgreSQL** (extern) — muss erreichbar sein
2. **Redis** — celery-beat und celery-worker warten darauf
3. **Vespa** — celery-worker wartet auf Port 8081 (Vespa braucht ~2-3 Min zum Starten)
4. **api-server** — führt `alembic upgrade head` aus, dann startet Uvicorn. Deployed das Vespa Application Package.

Bei erstmaligem Deploy dauert der api-server-Start länger (viele Alembic-Migrationen). Kann 1-2 Restarts verursachen wenn die Startup-Probe zu kurz ist.

---

## Validierung nach Deploy

```bash
# Alle Pods 1/1 Running
kubectl get pods -n onyx-dev

# API Health
curl -s http://<EXTERNAL_IP>/api/health
# Erwartete Ausgabe: {"success":true,"message":"ok","data":null}

# Login-Seite
curl -s -o /dev/null -w "%{http_code}" http://<EXTERNAL_IP>/auth/login
# Erwartete Ausgabe: 200 (oder 307 redirect zu login)
```

---

## Domain / Cookie-Konfiguration

Onyx setzt `cookie_secure` basierend auf `WEB_DOMAIN`:

```python
# backend/onyx/auth/users.py:991
cookie_secure=WEB_DOMAIN.startswith("https")
```

**Solange kein DNS/TLS konfiguriert ist**, muss die Domain auf die IP mit HTTP zeigen:

```yaml
DOMAIN: "188.34.74.187"
WEB_DOMAIN: "http://188.34.74.187"
```

Bei `WEB_DOMAIN: "https://..."` wird ein `Secure`-Cookie gesetzt, das der Browser bei HTTP-Verbindungen **nicht sendet** → Login-Loop (403 auf `/me`).

**Nach DNS/TLS-Setup** auf FQDN + HTTPS umstellen:

```yaml
DOMAIN: "dev.chatbot.voeb-service.de"
WEB_DOMAIN: "https://dev.chatbot.voeb-service.de"
```

---

## Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Pods Pending: "Insufficient cpu" | Rolling Update Deadlock | Alte RS auf 0 skalieren |
| api-server CrashLoop: `database "onyx" does not exist` | DB nicht angelegt | [PostgreSQL Runbook](./stackit-postgresql.md) |
| api-server CrashLoop: `permission denied to create role` | Managed PG kein CREATEROLE | `db_readonly_user` per Terraform |
| api-server CrashLoop: `NoCredentialsError` | S3 Credentials fehlen | Object Storage Credentials anlegen |
| celery-beat: Redis probe timeout | REDIS_HOST falsch | `REDIS_HOST: "onyx-dev"` setzen |
| celery-worker: Vespa probe failed | Vespa startet langsam | 2-3 Min warten, Vespa-Logs prüfen |
| 502 Bad Gateway | api-server noch nicht bereit | Warten bis Alembic + Uvicorn gestartet |
| Login-Loop: 403 auf `/me` | `WEB_DOMAIN` ist HTTPS, Zugriff per HTTP | `WEB_DOMAIN: "http://<IP>"` setzen |
| Login klappt, Verifizierung hängt | `REQUIRE_EMAIL_VERIFICATION` ohne SMTP | `REQUIRE_EMAIL_VERIFICATION: "false"` |
