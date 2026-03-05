# Cloud-Infrastruktur Audit — Ergebnisse & Massnahmenplan

**Datum:** 2026-03-04
**Durchgefuehrt von:** 5 parallele Opus-4.6-Agenten (Terraform/IaC, K8s/Helm, CI/CD, Netzwerk/TLS/Auth, BSI/BAIT/DSGVO)
**Scope:** Gesamte StackIT-Infrastruktur (DEV + TEST), CI/CD, Helm, Terraform, Dokumentation
**Basis-Commit:** `703687754` (main)
**Tiefenpruefung:** 5 Findings verifiziert durch separate Opus-Agenten mit Code-Analyse (2026-03-04)

---

## Zusammenfassung

| Schweregrad | Anzahl | Verifiziert | Status |
|-------------|--------|-------------|--------|
| CRITICAL    | 10     | 5/10        | 1/10 erledigt |
| HIGH        | 18     | 5/18        | 2/18 erledigt |
| MEDIUM      | ~20    | —           | 0/~20 erledigt |
| LOW         | ~12    | —           | 0/~12 erledigt |

**Positiv-Befunde:** SHA-gepinnte Actions, PG ACL (SEC-01) korrekt, 100% Datensouveraenitaet (StackIT/DE), saubere Extension-Architektur, separate PG+Buckets pro Env, `prevent_destroy` auf PG, `web/Dockerfile` korrekt mit `USER nextjs`.

---

## Tier 1 — SOFORT (vor weiterer Entwicklung)

### C1: Kein TLS/HTTPS auf DEV + TEST
- **Risiko:** Credentials + Session-Cookies im Klartext ueber oeffentliches Internet
- **Dateien:** `deployment/helm/values/values-dev.yaml`, `values-test.yaml`
- **Massnahme:**
  - [ ] DNS-Eintraege bei Cloudflare anlegen (`dev.chatbot.voeb-service.de`, `test.chatbot.voeb-service.de`)
  - [ ] cert-manager + ClusterIssuer (Let's Encrypt, DNS-01 Challenge via Cloudflare)
  - [ ] Ingress-TLS konfigurieren (ECDSA P-384, BSI TR-02102-2)
  - [ ] `WEB_DOMAIN` auf `https://` umstellen
  - [ ] HTTP → HTTPS Redirect erzwingen
- **Runbook:** `docs/runbooks/dns-tls-setup.md` (bereit)
- **Blockiert durch:** Leif (Cloudflare DNS-Zugang + CF API Token)
- **Status:** [ ] Erledigt

---

### C2: K8s Cluster API ACL = `0.0.0.0/0`
- **Risiko:** Jeder im Internet kann K8s API ansprechen (nur Kubeconfig als Schutz)
- **Datei:** `deployment/terraform/modules/stackit/variables.tf:51-55`
- **Verifizierungsergebnis (2026-03-04):**
  ACL-Einschraenkung auf statische IPs ist fuer dieses Projekt **nicht praktikabel**:
  - Externer Dienstleister (Niko) arbeitet von wechselnden IPs (Laptop, Desktop, Handy)
  - VoB-IP-Ranges sind nicht bekannt
  - GitHub Actions hat dynamische IPs
  - **Kubeconfig mit Client-Zertifikat** ist der primaere Schutzmechanismus (funktioniert, laeuft 2026-05-28 ab)
- **Entscheidung:** Zurueckgestellt auf "Vor PROD". Fuer PROD: VPN oder StackIT-eigene Loesung evaluieren.
- **Status:** [ ] Zurueckgestellt (akzeptiertes Risiko fuer DEV/TEST)

---

### C3: Terraform State lokal mit Klartext-Credentials
- **Risiko:** PG-Passwoerter + RSA Private Key (Kubeconfig) im lokalen `terraform.tfstate`
- **Datei:** `deployment/terraform/environments/dev/backend.tf` (local backend)
- **Massnahme:**
  - [ ] **Kurzfristig:** `.tfstate` in `.gitignore` verifizieren (ist bereits drin)
  - [ ] **Kurzfristig:** Laptop-Festplattenverschluesselung (FileVault) verifizieren
  - [ ] **Mittelfristig (vor PROD):** Remote Backend aktivieren (StackIT Object Storage + State Locking)
    ```hcl
    backend "s3" {
      bucket   = "vob-terraform-state"
      key      = "dev/terraform.tfstate"
      endpoint = "https://object-storage.eu01.onstackit.cloud"
      encrypt  = true
    }
    ```
  - [ ] `sensitive = true` auf alle Credential-Outputs setzen
- **Status:** [ ] Erledigt

---

### C4: Container laufen als Root
- **Risiko:** Container-Escape → Root auf Node → Cluster-Kompromittierung
- **Dateien:**
  - `backend/Dockerfile` — erstellt User `onyx`, setzt aber nie `USER onyx`
  - `backend/Dockerfile.model_server` — gleich
  - `deployment/helm/charts/onyx/values.yaml` — Vespa/Celery: `privileged: true, runAsUser: 0`
- **Massnahme:**
  - [ ] `backend/Dockerfile`: `USER onyx` vor `CMD` einfuegen (**Achtung: Onyx-Upstream-Datei**)
  - [ ] `backend/Dockerfile.model_server`: Analog
  - [ ] Vespa `privileged: true` pruefen — benoetigt Vespa wirklich Root? (Upstream-Issue recherchieren)
  - [ ] Fuer eigene Workloads: `securityContext` in values-common.yaml:
    ```yaml
    securityContext:
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
    ```
  - [ ] Testen: Alle Pods starten und funktionieren nach Aenderung
- **Status:** [ ] Erledigt

---

### C5: Keine NetworkPolicies (DEV ↔ TEST nicht isoliert)
- **Risiko:** Kompromittierter Pod in DEV kann TEST-DB erreichen (shared Cluster)
- **Massnahme:**
  - [x] Default-Deny NetworkPolicy pro Namespace (01-default-deny-all.yaml)
  - [x] Whitelist-Policies fuer erlaubten Traffic (02-DNS, 03-Intra-NS, 04-Ingress-nginx, 05-Egress)
  - [x] Gleiches fuer `onyx-test`
  - [x] Testen: Cross-NS-Isolation verifiziert (DEV → TEST blockiert)
- **Loesung:** 5 NetworkPolicies in `deployment/k8s/network-policies/`, Analyse in `docs/audit/networkpolicy-analyse.md`
- **Status:** [x] Erledigt (2026-03-05)

---

### C6: DB_READONLY_PASSWORD in ConfigMap statt K8s Secret [VERIFIZIERT]

- **Risiko:** ConfigMaps sind unverschluesselt, fuer jeden mit Namespace-Zugriff per `kubectl get configmap -o yaml` lesbar. Das Passwort steht im Klartext.
- **Betroffene Dateien:**
  - `.github/workflows/stackit-deploy.yml` — Zeile 218 (DEV), 338 (TEST), 428 (PROD)
  - `deployment/helm/values/values-dev.yaml` — Zeile 48 (`DB_READONLY_USER` unter `configMap:`)
  - `deployment/helm/values/values-test.yaml` — analog
  - `deployment/helm/values/values-dev-secrets.yaml` — Zeile 20 (Klartext-Passwort)

#### Verifizierung (Opus-Agent, 2026-03-04)

Das Helm Chart hat einen **eingebauten Secret-Mechanismus** fuer `auth.dbreadonly` (`values.yaml:1143-1157`), der identisch zu `auth.postgresql`, `auth.redis` und `auth.objectstorage` funktioniert:

1. **`auth-secrets.yaml` Template** — Erstellt automatisch ein K8s Secret `onyx-dbreadonly` wenn `auth.dbreadonly.enabled: true`
2. **`_helpers.tpl:74-86` (`onyx.envSecrets` Helper)** — Iteriert ueber ALLE `auth.*`-Eintraege und injiziert sie als ENV-Variablen in 15 Pod-Templates (API, Web, alle 8 Celery Worker, Model Server, etc.)
3. **Key-Mapping:** `secretKeys.DB_READONLY_PASSWORD: db_readonly_password` → Helper macht automatisch uppercase → ENV `DB_READONLY_PASSWORD`

Der Mechanismus ist produktionsreif und wird bereits fuer 3 andere Secrets genutzt.

#### Exakte Aenderungen

**1) `values-dev.yaml` — `DB_READONLY_USER` aus configMap entfernen, `auth.dbreadonly` Block hinzufuegen:**

```yaml
# ENTFERNEN (Zeile 48):
#   DB_READONLY_USER: "db_readonly_user"

# HINZUFUEGEN unter auth: (nach objectstorage, ca. Zeile 35):
  dbreadonly:
    enabled: true
    secretName: "onyx-dbreadonly"
    values:
      db_readonly_user: "db_readonly_user"
      db_readonly_password: ""  # → GitHub Secret per --set im Workflow
```

**2) `values-test.yaml` — analog zu values-dev.yaml**

**3) `stackit-deploy.yml` — in allen 3 Deploy-Jobs:**

```yaml
# VORHER (Zeile 218 / 338 / 428):
--set "configMap.DB_READONLY_PASSWORD=${{ secrets.DB_READONLY_PASSWORD }}"

# NACHHER:
--set "auth.dbreadonly.values.db_readonly_password=${{ secrets.DB_READONLY_PASSWORD }}"
```

**4) `values-dev-secrets.yaml` — DB_READONLY_PASSWORD-Block entfernen (Zeile 17-20):**
Wird nicht mehr benoetigt, da Passwort ausschliesslich ueber GitHub Secrets → CI/CD → Helm `--set` injiziert wird.

#### Verifikation nach Deploy

```bash
# Darf KEIN Passwort mehr enthalten:
kubectl get configmap env-configmap -n onyx-dev -o yaml | grep -i password
# Erwartung: kein Treffer

# Secret muss existieren:
kubectl get secret onyx-dbreadonly -n onyx-dev
# Erwartung: Secret vorhanden

# Pods muessen die ENV-Variable haben:
kubectl exec deployment/onyx-dev-api-server -n onyx-dev -- env | grep DB_READONLY
# Erwartung: DB_READONLY_USER=db_readonly_user, DB_READONLY_PASSWORD=<wert>
```

#### Fallstricke

| Fallstrick | Absicherung |
|------------|-------------|
| `enabled` ist per Default `false` im Chart | Wird explizit auf `true` gesetzt in values-dev/test.yaml |
| YAML-Keys sind lowercase, ENV-Vars uppercase | Helper macht das automatisch (`$name \| upper`) |
| Alle 3 Deploy-Jobs muessen konsistent geaendert werden | DEV (Z.218), TEST (Z.338), PROD (Z.428) |
| `DB_READONLY_USER` muss auch ins Secret (nicht nur Passwort) | Steht in `values` Block als `db_readonly_user` |

- **Risiko der Aenderung:** Gering. Identischer Mechanismus wie die 3 funktionierenden Secrets.
- **Status:** [x] Erledigt (2026-03-04)

---

### C7: Klartext-Secrets in values-dev-secrets.yaml
- **Risiko:** PG-Passwort, S3-Keys im Klartext auf Laptop (auch wenn gitignored)
- **Datei:** `deployment/helm/values/values-dev-secrets.yaml`
- **Massnahme:**
  - [ ] Verifizieren: Datei ist in `.gitignore`
  - [ ] **Mittelfristig:** Sealed Secrets oder SOPS einfuehren
  - [ ] **Alternativ:** Alle Secrets ausschliesslich ueber GitHub Secrets → CI/CD injizieren (kein lokales File)
- **Status:** [ ] Erledigt

---

### C8: Keine DSFA (Datenschutzfolgenabschaetzung)
- **Risiko:** Art. 35 DSGVO — KI-System mit potenziell personenbezogenen Daten erfordert DSFA
- **Massnahme:**
  - [ ] DSFA erstellen (KI-Chatbot + Dokumentenverarbeitung + Bankdaten)
  - [ ] Risikobewertung: Verarbeitungszweck, Rechtsgrundlage, technische Massnahmen
- **Status:** [ ] Erledigt

---

### C9: Kein Loeschkonzept
- **Risiko:** Art. 17 DSGVO — Aufbewahrungsfristen undefiniert
- **Massnahme:**
  - [ ] Loeschkonzept erstellen: Welche Daten, wie lange, wie geloescht
  - [ ] Automatisierung fuer Loeschfristen (Cronjob oder Celery Task)
- **Status:** [ ] Erledigt

---

### C10: Kein IP-Allowlisting auf Ingress
- **Risiko:** DEV/TEST weltweit erreichbar (Login-Seite offen)
- **Verifizierungsergebnis (2026-03-04):**
  IP-basiertes Allowlisting ist **nicht praktikabel** (gleiche Gruende wie C2: wechselnde IPs, unbekannte Kunden-Ranges).
  **Alternativen:**
  - **Cloudflare Access (Zero Trust):** Email-basierte Auth vor der Seite, IP-unabhaengig, kostenlos bis 50 User
  - **Basic Auth auf nginx:** Einfaches Passwort als Uebergang
  - **Warten auf Entra ID (Phase 3, Termin 06.03):** Danach nur noch Microsoft-Login moeglich
- **Entscheidung:** Zurueckgestellt. Entra ID (1-2 Wochen) ist die eigentliche Loesung. Falls Entra ID sich verzoegert: Basic Auth oder Cloudflare Access als Uebergang.
- **Status:** [ ] Zurueckgestellt (akzeptiertes Risiko bis Entra ID)

---

## Tier 2 — VOR PROD (vor Production-Deployment)

### H1: PG-User hat `createdb`-Rolle [VERIFIZIERT]

- **Risiko:** Least Privilege verletzt — `onyx_app` kann neue Datenbanken erstellen (braucht er nicht)
- **Datei:** `deployment/terraform/modules/stackit/main.tf:100`
- **Geplante Aenderung:** `roles = ["login", "createdb"]` → `roles = ["login"]`

#### Verifizierung (Opus-Agent, 2026-03-04)

**WARNUNG: Diese Aenderung ist NICHT als Quick Win geeignet.**

Der Agent hat den Terraform State und das StackIT-Provider-Verhalten analysiert:

1. **StackIT PG Flex erlaubt kein Patching von User-Rollen.** Eine Aenderung der `roles` fuehrt zu **Destroy + Recreate** des Users.
2. **Bei Recreate wird ein NEUES Passwort auto-generiert** (aktuelles Passwort im State: `cP3JgN...`, 64 Zeichen).
3. **Das GitHub Secret `POSTGRES_PASSWORD` wird NICHT automatisch aktualisiert.**
4. **Konsequenz:** Alle 10 DEV-Pods + 9 TEST-Pods verlieren DB-Zugang → CrashLoop.

#### Ablauf bei Umsetzung (Wartungsfenster erforderlich)

```
1. Wartungsfenster planen (z.B. Freitag Abend)
2. terraform apply → User wird destroyed + recreated
3. Neues Passwort: terraform output -raw pg_password
4. GitHub Secret aktualisieren: gh secret set POSTGRES_PASSWORD --body="<neues_pw>"
5. Helm Re-Deploy: gh workflow run stackit-deploy.yml -f environment=dev
6. Repeat fuer TEST
7. Smoke Tests: /api/health auf beiden Environments
8. Geschaetzte Downtime: 15-20 Min pro Environment
```

#### Alternative: Direktes SQL (kein Passwort-Wechsel)

```sql
ALTER USER onyx_app NOCREATEDB;
```

**Vorteil:** Kein Passwort-Wechsel, keine Downtime
**Nachteil:** Terraform State und Realitaet laufen auseinander → naechstes `terraform apply` erzwingt Destroy+Recreate

#### Empfehlung

Auf Wartungsfenster verschieben. `createdb` ist ein Least-Privilege-Verstoss, aber kein akutes Sicherheitsrisiko:
- PG ACL beschraenkt Zugriff auf Egress-IP + Admin-IP
- User kann DBs erstellen, aber nicht aus dem Cluster ausbrechen
- Zusammen mit anderen Terraform-Aenderungen (Remote State Backend, PROD-Setup) buendeln

- **Status:** [ ] Wartungsfenster geplant

---

### H2: PostgreSQL kein HA (Single Instance)
- **Massnahme:**
  - [ ] Fuer PROD: PG Flex auf HA-Konfiguration (min. 2 Replicas, `pg_replicas = 3`)
  - [ ] Backup-Strategie dokumentieren (StackIT Flex: automatisch taeglich um 02:00, `pg_backup_schedule`)
- **Status:** [ ] Erledigt

---

### H3: Object Storage — keine Verschluesselung/Versionierung
- **Massnahme:**
  - [ ] Server-Side Encryption aktivieren (StackIT Object Storage Einstellung)
  - [ ] Versionierung aktivieren (Schutz gegen versehentliches Loeschen)
  - [ ] Lifecycle Policy fuer alte Versionen (z.B. 90 Tage)
- **Status:** [ ] Erledigt

---

### H4: Lock-File Inkonsistenz (package-lock.json)
- **Massnahme:**
  - [ ] `npm ci` statt `npm install` in CI/CD (bereits so? verifizieren)
  - [ ] Lock-File nach `npm install` committen wenn veraltet
- **Status:** [ ] Erledigt

---

### H5: API/Webserver ohne SecurityContext
- **Massnahme:**
  - [ ] `securityContext` fuer api-server und web-server Pods setzen (siehe C4)
  - [ ] `readOnlyRootFilesystem: true` + tmpfs Volumes fuer Schreibbedarf
- **Status:** [ ] Erledigt

---

### H6: Keine Health Probes (Liveness/Readiness)
- **Massnahme:**
  - [ ] Pruefen ob Helm Chart schon Probes definiert (wahrscheinlich ja)
  - [ ] Falls nicht: `/health` Endpoint als livenessProbe, `/api/health` als readinessProbe
  - [ ] `initialDelaySeconds`, `periodSeconds`, `failureThreshold` konfigurieren
- **Status:** [ ] Erledigt

---

### H7: Kein mTLS zwischen Services
- **Massnahme:**
  - [ ] **Mittelfristig:** Service Mesh evaluieren (Linkerd/Istio) — ggf. Overkill fuer aktuelle Groesse
  - [ ] **Alternativ:** NetworkPolicies (C5) als Mindestschutz
- **Status:** [ ] Erledigt

---

### H8: nginx — fehlende Security-Header [VERIFIZIERT]

- **Risiko:** Kein Schutz vor Clickjacking, MIME-Sniffing, ungewolltem Referrer-Leak
- **Datei:** `deployment/helm/values/values-common.yaml` (unsere Config, KEIN Upstream-Eingriff)

#### Verifizierung (Opus-Agent, 2026-03-04)

nginx wird als **Sub-Chart `ingress-nginx` v4.13.3** deployed. Die `http-snippet` in `values-common.yaml` wird in den `http {}`-Block der nginx.conf injiziert. `add_header`-Direktiven auf http-Ebene werden von allen `server {}`-Bloecken geerbt — die `server.conf` in `nginx-conf.yaml` hat keine eigenen `add_header`, also greift die Vererbung.

#### Exakte Aenderung

**`deployment/helm/values/values-common.yaml`** — bestehende `http-snippet` erweitern:

```yaml
# VORHER (im nginx.controller.config Block):
      http-snippet: |
        include /etc/nginx/custom-snippets/upstreams.conf;
        include /etc/nginx/custom-snippets/server.conf;

# NACHHER:
      http-snippet: |
        # Security Headers (BSI TR-02102 / VoB Enterprise)
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
        # Onyx custom config
        include /etc/nginx/custom-snippets/upstreams.conf;
        include /etc/nginx/custom-snippets/server.conf;
```

#### Was die Header tun

| Header | Schutz |
|--------|--------|
| `X-Content-Type-Options: nosniff` | Verhindert MIME-Sniffing (Browser interpretiert z.B. HTML nicht als JS) |
| `X-Frame-Options: DENY` | Verhindert Einbettung in iFrames (Clickjacking-Schutz) |
| `Referrer-Policy: strict-origin-when-cross-origin` | Limitiert Referrer-Informationen an Drittseiten |
| `Permissions-Policy` | Blockiert Kamera/Mikrofon/Geolocation API (braucht ein Chatbot nicht) |

#### Bewusst NICHT enthalten

| Header | Grund |
|--------|-------|
| `X-XSS-Protection` | Veraltet, wird von modernen Browsern ignoriert, kann in Edge-Cases schaden |
| `Strict-Transport-Security` (HSTS) | Erst NACH TLS-Aktivierung (C1), sonst sperrt man sich bei HTTP aus |
| Rate Limiting (`limit-rps`) | Benoetigt Ingress-Annotation, nicht ueber `http-snippet` moeglich. Separat evaluieren. |

#### Verifikation nach Deploy

```bash
# Header pruefen:
curl -sI http://188.34.74.187 | grep -E "X-Content-Type|X-Frame|Referrer-Policy|Permissions-Policy"
# Erwartung: Alle 4 Header in der Response
```

- **Risiko der Aenderung:** Sehr gering. `add_header` mit `always` ist Standard-Praxis. Falls ein Header Probleme macht, in 1 Zeile entfernbar.
- **Status:** [x] Erledigt (2026-03-04)

---

### H9: 5 GB Upload-Limit [VERIFIZIERT]

- **Risiko:** DoS-Vektor — ein einzelner 5-GB-POST kann Pod/Node ueberlasten
- **Datei:** `deployment/helm/charts/onyx/templates/nginx-conf.yaml:36` (Upstream, READ-ONLY)

#### Verifizierung (Opus-Agent, 2026-03-04)

`client_max_body_size 5G` ist **hardcoded** im Upstream-Template `nginx-conf.yaml:36`. Das Helm Chart bietet **keinen konfigurierbaren Value** dafuer. Da die Chart-Templates als READ-ONLY gelten, koennen wir den Wert nicht aendern.

Der `ingress-nginx` Sub-Chart hat zwar `proxy-body-size` in seiner ConfigMap, aber die custom `server.conf` ueberschreibt das mit ihrem expliziten `client_max_body_size 5G` — die Ingress-Controller-Einstellung greift nicht.

#### Optionen

| Option | Machbar? | Bewertung |
|--------|----------|-----------|
| **Akzeptiertes Risiko** fuer DEV/TEST | Ja | Mitigation: Auth (Entra ID), IP-Schutz |
| **Upstream PR** an Onyx: Wert konfigurierbar machen | Moeglich | Langfristig sauber, braucht Zeit |
| **Chart-Fork** mit eigener Template-Aenderung | Moeglich | Bricht READ-ONLY-Regel, Merge-Konflikte |

#### Entscheidung

**Akzeptiertes Risiko fuer DEV/TEST.** Mitigationen:
- Nur authentifizierte User koennen hochladen (nach Entra ID / Phase 3)
- Bankdokumente sind typischerweise <50 MB
- Fuer PROD: Upstream PR oder nginx `location`-Block mit eigenem Limit in ext/-Config

- **Status:** [ ] Akzeptiertes Risiko (mit Dokumentation)

---

### H10: Globale Kubeconfig (nicht Namespace-scoped)
- **Massnahme:**
  - [ ] Fuer CI/CD: Service Account pro Namespace mit RBAC (nur eigener Namespace)
  - [ ] Kubeconfig-Ablauf: 2026-05-28 — Erneuerungsprozess dokumentieren
- **Status:** [ ] Erledigt

---

### H11: `image_tag` Input-Injection in CI/CD [VERIFIZIERT]

- **Risiko:** Script Injection — `${{ inputs.image_tag }}` wird direkt in Shell interpoliert
- **Datei:** `.github/workflows/stackit-deploy.yml`

#### Verifizierung (Opus-Agent, 2026-03-04)

Der Agent hat die gesamte Pipeline analysiert und **3 Injection-Vektoren** identifiziert:

**Vektor 1 (KRITISCH) — Zeile 87-88:**
```yaml
if [ -n "${{ inputs.image_tag }}" ]; then
  echo "value=${{ inputs.image_tag }}" >> $GITHUB_OUTPUT
```
`${{ inputs.image_tag }}` wird direkt in die Shell interpoliert. Payload wie `"; rm -rf / #` wird ausgefuehrt. Ausnutzbar von jedem mit Write-Zugriff auf das Repo (workflow_dispatch).

**Vektor 2 (SEKUNDAER) — Zeilen 195, 315, 406:**
```yaml
IMAGE_TAG="${{ needs.prepare.outputs.image_tag }}"
```
Haengt von Vektor 1 ab — wenn der Output kompromittiert ist, ist auch hier Code-Execution moeglich.

**Vektor 3 (MODERAT) — Helm `--set`:**
Unkontrollierter Tag-Wert in `--set "global.version=${IMAGE_TAG}"` kann Helm-Template-Injection verursachen (z.B. `v1.0,foo=bar` setzt zusaetzliche Values).

**Alle anderen Stellen (Kubeconfig, Helm repos, Deployment-Namen) sind sicher** — hardcoded oder aus Secrets.

#### Exakte Aenderung

**`.github/workflows/stackit-deploy.yml` — Zeile 84-91:**

```yaml
# VORHER:
      - name: Determine image tag
        id: tag
        run: |
          if [ -n "${{ inputs.image_tag }}" ]; then
            echo "value=${{ inputs.image_tag }}" >> $GITHUB_OUTPUT
          else
            echo "value=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
          fi

# NACHHER:
      - name: Determine image tag
        id: tag
        env:
          INPUT_TAG: ${{ inputs.image_tag }}
        run: |
          set -euo pipefail
          if [ -n "${INPUT_TAG:-}" ]; then
            # Docker Tag Spec: Start mit [a-zA-Z0-9_], dann [a-zA-Z0-9._-], max 128 Zeichen
            if ! echo "$INPUT_TAG" | grep -qxE '[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}'; then
              echo "::error::Invalid image tag '${INPUT_TAG}'. Must match Docker tag spec: [a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}"
              exit 1
            fi
            echo "value=${INPUT_TAG}" >> $GITHUB_OUTPUT
          else
            echo "value=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
          fi
```

#### Zwei Schutzmechanismen

1. **`env:` statt `${{ }}`** — Wert wird als Environment-Variable uebergeben, nicht in die Shell interpoliert. Das ist der von GitHub Security Lab empfohlene Fix ([Quelle](https://securitylab.github.com/resources/github-actions-untrusted-input/)).
2. **Docker-Tag-Regex** — `[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}` — muss mit alphanumerisch/Unterstrich starten, max 128 Zeichen, nur erlaubte Sonderzeichen. Entspricht der Docker-Spec.

#### Warum Vektor 2 automatisch gefixt ist

Wenn Vektor 1 gefixt ist, kann `needs.prepare.outputs.image_tag` nur noch einen validierten Wert enthalten. Die Deploy-Jobs (Zeilen 195, 315, 406) sind damit implizit abgesichert — der Output ist entweder ein validierter Tag oder ein Git SHA.

#### Verifikation

```bash
# Workflow manuell triggern mit ungueltigem Tag:
gh workflow run stackit-deploy.yml -f environment=dev -f image_tag='"; echo PWNED #'
# Erwartung: Job schlaegt fehl mit "Invalid image tag" Error
```

- **Risiko der Aenderung:** Null. Alle validen Image-Tags (Git SHAs, Semantic Versions, etc.) passen durch die Regex.
- **Status:** [x] Erledigt (2026-03-04)

---

### H12: Kein Image-Signing / SBOM
- **Massnahme:**
  - [ ] **Vor PROD:** cosign fuer Image-Signierung einfuehren
  - [ ] SBOM generieren (syft/trivy) und als Build-Artefakt speichern
  - [ ] Optional: Admission Controller der nur signierte Images zulaesst
- **Status:** [ ] Erledigt

---

### H13: CORS Wildcard
- **Massnahme:**
  - [ ] CORS-Origin auf `https://dev.chatbot.voeb-service.de` einschraenken (nach TLS)
  - [ ] Kein `Access-Control-Allow-Origin: *` in Produktion
- **Status:** [ ] Erledigt

---

### H14: Cookie `Secure=false`
- **Massnahme:**
  - [ ] Wird automatisch gefixt wenn TLS aktiv ist (C1)
  - [ ] Verifizieren nach TLS-Aktivierung: `Set-Cookie: ... Secure; HttpOnly; SameSite=Lax`
- **Status:** [ ] Erledigt

---

### H15: DB-Credential-Verschluesselung fehlt (MIT Edition)
- **Datei:** `backend/onyx/utils/encryption.py` — `_encrypt_string` ist Identity-Funktion in MIT Edition
- **Massnahme:**
  - [ ] Akzeptables Risiko fuer DEV/TEST (MIT Edition)
  - [ ] Fuer PROD: EE-Lizenz oder eigene Verschluesselung in ext/ implementieren
- **Status:** [ ] Erledigt

---

### H16: Kein PROD-Environment vorbereitet
- **Massnahme:**
  - [ ] `values-prod.yaml` erstellen (HA, Ressource-Limits, TLS, Auth)
  - [ ] Terraform `environments/prod/` anlegen
  - [ ] GitHub Environment `prod` mit Required Reviewers
- **Status:** [ ] Erledigt

---

### H17: Fehlender AVV mit StackIT
- **Massnahme:**
  - [ ] Auftragsverarbeitungsvertrag (Art. 28 DSGVO) mit StackIT abschliessen
  - [ ] Niko: bei StackIT anfragen (Standard-AVV vorhanden?)
- **Status:** [ ] Erledigt

---

### H18: Kein DSB benannt
- **Massnahme:**
  - [ ] Datenschutzbeauftragten bei VoB und CCJ benennen (Art. 37 DSGVO)
  - [ ] In Sicherheitskonzept + Betriebskonzept dokumentieren
- **Status:** [ ] Erledigt

---

## Tier 3 — VOR ABNAHME (M1)

### M1: CSP-Header unvollstaendig
- **Datei:** `web/next.config.js`
- **Massnahme:**
  - [ ] `default-src 'self'`, `script-src`, `style-src`, `frame-ancestors 'none'` setzen
- **Status:** [ ] Erledigt

### M2: Keine Pod-Disruption-Budgets
- **Massnahme:**
  - [ ] PDBs fuer kritische Services (API, Web, Redis) — erst relevant bei >1 Replica
- **Status:** [ ] Erledigt

### M3: Keine Resource Limits/Requests
- **Massnahme:**
  - [ ] CPU/Memory Limits + Requests fuer alle Pods in values-common.yaml definieren
  - [ ] LimitRange pro Namespace als Fallback
- **Status:** [ ] Erledigt

### M4: Redis ohne Passwort
- **Massnahme:**
  - [ ] Redis-Passwort setzen (Helm Value `REDIS_PASSWORD`)
  - [ ] Oder: NetworkPolicy als Schutz (Redis nur von API-Pods erreichbar)
- **Status:** [ ] Erledigt

### M5: Kein Audit-Logging
- **Massnahme:**
  - [ ] K8s Audit Policy aktivieren (API-Server-Zugriffe loggen)
  - [ ] Anwendungs-Audit-Log fuer Login/Admin-Aktionen (ext/ Modul)
- **Status:** [ ] Erledigt

### M6: Kein Monitoring / Alerting
- **Massnahme:**
  - [ ] Prometheus + Grafana (oder StackIT Monitoring Service)
  - [ ] Alerts: Pod-Restarts, Disk >80%, Memory >80%, 5xx-Rate
- **Status:** [ ] Erledigt

### M7: Backup-Strategie nicht dokumentiert
- **Massnahme:**
  - [ ] PG Flex Backup-Einstellungen pruefen (automatisch bei StackIT, taeglich 02:00)
  - [ ] Object Storage Versionierung (H3)
  - [ ] Recovery-Test durchfuehren und dokumentieren
- **Status:** [ ] Erledigt

### M8: Helm Chart kein Pinning
- **Massnahme:**
  - [ ] Onyx Chart Version pinnen (nicht `latest`)
  - [ ] Sub-Chart-Versionen in `Chart.lock` verifizieren
- **Status:** [ ] Erledigt

---

## Tier 4 — NICE TO HAVE / LANGFRISTIG

### L1: Terraform Module nicht versioniert
- [ ] Module-Source auf Git-Tag pinnen

### L2: Kein Drift-Detection
- [ ] `terraform plan` in CI als Scheduled Job (woechentlich)

### L3: Pre-commit Hooks fuer Terraform
- [ ] `terraform fmt`, `terraform validate`, `tflint`, `tfsec` als pre-commit

### L4: SAST/DAST im CI
- [ ] Trivy/Grype fuer Container-Scanning
- [ ] Bandit fuer Python, ESLint Security fuer TypeScript

### L5: Penetrationstest
- [ ] Externer Pentest vor PROD-Go-Live (BAIT-Anforderung)

### L6: Notfallhandbuch
- [ ] Incident-Response-Plan erstellen
- [ ] Eskalationswege definieren (VoB, CCJ, StackIT)

### L7: Change-Management-Richtlinie
- [ ] Formaler Change-Prozess (BAIT ORP.4)

### L8: Secret-Rotationskonzept
- [ ] Rotationsintervalle definieren (PG-Passwoerter, API-Keys, Kubeconfig)
- [ ] Automatisierung wo moeglich

---

## Fehlende regulatorische Dokumente

| Dokument | DSGVO/BAIT Referenz | Prioritaet |
|----------|---------------------|------------|
| DSFA (Datenschutzfolgenabschaetzung) | Art. 35 DSGVO | CRITICAL — KI + personenbezogene Daten |
| Loeschkonzept | Art. 17 DSGVO | CRITICAL |
| AVV mit StackIT | Art. 28 DSGVO | HIGH |
| Datenschutzerklaerung | Art. 13/14 DSGVO | HIGH |
| Notfallhandbuch | BSI SYS.1.6, BAIT | MEDIUM |
| Change-Management-Richtlinie | BAIT ORP.4 | MEDIUM |
| Secret-Rotationskonzept | BSI OPS.1.1.3 | MEDIUM |
| Pentest-Bericht | BAIT | LOW (vor PROD) |

---

## Arbeitsreihenfolge (aktualisiert nach Verifizierung)

**Erledigt (3 Quick Wins, 2026-03-04):**
1. ~~**C6:** DB_READONLY_PASSWORD → Secret (CI/CD + Helm Values)~~ ✅
2. ~~**H8:** Security-Header auf nginx (values-common.yaml)~~ ✅
3. ~~**H11:** image_tag Injection fixen (CI/CD Workflow)~~ ✅

**Nach Leif (TLS-Blocker):**
4. **C1:** DNS + TLS aktivieren (Runbook bereit)
5. **H13:** CORS einschraenken (nach TLS)
6. **H14:** Cookie Secure verifizieren (nach TLS)

**Nach Entra ID (Phase 3, Termin 06.03):**
7. **C10:** Ingress-Schutz durch OIDC Auth (statt IP-Whitelist)

**Wartungsfenster (mit Terraform-Aenderungen buendeln):**
8. **H1:** PG createdb-Rolle entfernen (Destroy+Recreate, Passwort-Rotation)
9. **C3:** Remote Terraform Backend

**Container-Hardening (Woche 2-3):**
10. **C4:** Non-Root Container + SecurityContext
11. ~~**C5:** NetworkPolicies (DEV + TEST Isolation)~~ ✅ Erledigt (2026-03-05)
12. **M3:** Resource Limits/Requests
13. **M4:** Redis-Passwort

**Compliance-Dokumente (Woche 3-4):**
14. **C8:** DSFA erstellen
15. **C9:** Loeschkonzept erstellen
16. **H17:** AVV mit StackIT
17. **H18:** DSB benennen

**Vor PROD:**
18. **H2:** PG HA
19. **H16:** PROD-Environment vorbereiten
20. Alle verbleibenden HIGH + MEDIUM Findings

**Akzeptierte Risiken (mit Dokumentation):**
- **C2:** K8s API ACL 0.0.0.0/0 — Kubeconfig ist Schutz, VPN fuer PROD evaluieren
- **H9:** 5G Upload-Limit — Upstream hardcoded, Mitigation durch Auth
- **H15:** DB-Encryption MIT Edition — Akzeptabel fuer DEV/TEST

---

*Dieses Dokument wird fortlaufend aktualisiert. Erledigte Punkte mit [x] markieren und Datum eintragen.*
*Verifizierte Findings sind mit [VERIFIZIERT] markiert und enthalten exakte Aenderungsanweisungen.*
