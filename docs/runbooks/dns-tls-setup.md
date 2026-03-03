# Runbook: DNS und TLS Setup

**Status:** Entwurf (noch nicht durchgefuehrt)
**Erstellt:** 2026-03-03
**Erstellt von:** Nikolaj Ivanov

---

## Uebersicht

### Aktuelle Situation

Beide Environments laufen aktuell ueber unverschluesseltes HTTP auf nackten IPs:

| Environment | Zugriff | Status |
|-------------|---------|--------|
| DEV | `http://188.34.74.187` | HTTP-only, IP-basiert |
| TEST | `http://188.34.118.201` | HTTP-only, IP-basiert |
| PROD | Noch nicht provisioniert | -- |

### Ziel

HTTPS mit eigener Domain fuer alle Environments. Let's Encrypt Zertifikate via cert-manager.

### Abhaengigkeitskette

```
Domain-Entscheidung (VoeB)
  -> DNS A-Records (VoeB IT)
    -> cert-manager Installation (CCJ)
      -> Let's Encrypt Zertifikate (automatisch)
        -> HTTPS funktioniert
          -> OIDC Redirect URI (Entra ID, Phase 3)
```

**Wichtig:** Microsoft Entra ID erlaubt in Produktion keine `http://`-Redirect-URIs. Ohne HTTPS ist Phase 3 (Authentifizierung) blockiert. Quelle: `docs/entra-id-kundenfragen.md`, Abschnitt 7.

---

## Voraussetzungen

### Domain-Entscheidung (VoeB)

VoeB muss entscheiden, welche Domain verwendet wird. Vorschlaege:

| Variante | DEV | TEST | PROD |
|----------|-----|------|------|
| Subdomain von `voeb.de` | `dev.chatbot.voeb.de` | `test.chatbot.voeb.de` | `chatbot.voeb.de` |
| Eigene Domain | `dev.chatbot.<domain>` | `test.chatbot.<domain>` | `chatbot.<domain>` |

> **[AUSSTEHEND -- Klaerung mit VoeB]** Welche Domain wird verwendet? Liegt die DNS-Verwaltung bei VoeB IT?

### Verantwortlichkeiten

| Aufgabe | Wer |
|---------|-----|
| Domain-Entscheidung | VoeB |
| DNS A-Records anlegen | VoeB IT |
| cert-manager installieren | CCJ (Niko) |
| Helm Values anpassen | CCJ (Niko) |
| Let's Encrypt Zertifikate | Automatisch (cert-manager) |
| Verifikation | Gemeinsam |

---

## Schritt 1: DNS-Konfiguration (VoeB IT)

### A-Records anlegen

VoeB IT muss folgende DNS A-Records erstellen:

```
dev.chatbot.<domain>     A    188.34.74.187
test.chatbot.<domain>    A    188.34.118.201
chatbot.<domain>         A    [AUSSTEHEND -- PROD LoadBalancer IP]
```

**TTL-Empfehlung:** 300 Sekunden (5 Minuten). Niedriger TTL erlaubt schnelle Korrekturen bei Fehlkonfiguration. Nach Stabilisierung auf 3600 (1 Stunde) erhoehen.

> **Hinweis:** Die IPs `188.34.74.187` (DEV) und `188.34.118.201` (TEST) sind StackIT LoadBalancer IPs. Diese sind stabil, solange die Kubernetes Services vom Typ `LoadBalancer` existieren. Bei einem Cluster-Neubau aendern sich die IPs.

### DNS-Verifikation

Nach Anlage der A-Records (Propagation kann bis zu 48 Stunden dauern, typischerweise 5-30 Minuten):

```bash
# DEV pruefen
dig +short dev.chatbot.<domain>
# Erwartete Ausgabe: 188.34.74.187

nslookup dev.chatbot.<domain>
# Erwartete Ausgabe: Address: 188.34.74.187

# TEST pruefen
dig +short test.chatbot.<domain>
# Erwartete Ausgabe: 188.34.118.201

# HTTP-Zugriff testen (sollte vor TLS-Setup bereits funktionieren)
curl -s http://dev.chatbot.<domain>/api/health
# Erwartete Ausgabe: {"success":true,"message":"ok","data":null}

curl -s http://test.chatbot.<domain>/api/health
# Erwartete Ausgabe: {"success":true,"message":"ok","data":null}
```

> **Erst weitermachen wenn DNS aufloest.** cert-manager kann keine Zertifikate ausstellen, wenn die Domain nicht auf die richtige IP zeigt. Let's Encrypt prueft die Domain per HTTP-01 Challenge -- der Request muss beim richtigen Ingress Controller ankommen.

---

## Schritt 2: cert-manager installieren (CCJ)

### 2.1 cert-manager per Helm installieren

```bash
# Namespace erstellen
kubectl create namespace cert-manager

# Helm Repo hinzufuegen
helm repo add jetstack https://charts.jetstack.io
helm repo update

# cert-manager installieren (CRDs mitinstallieren)
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set crds.enabled=true \
  --set crds.keep=true \
  --version v1.17.1
```

> **Hinweis:** Die `--version` auf die zum Zeitpunkt der Ausfuehrung aktuelle stabile Version anpassen. CRDs (`crds.enabled=true`) muessen mitinstalliert werden, da der Onyx Helm Chart `ClusterIssuer` und `Certificate` CRDs nutzt.

### 2.2 Installation verifizieren

```bash
# Alle Pods muessen Running sein
kubectl get pods -n cert-manager
# Erwartete Ausgabe: 3 Pods (cert-manager, cert-manager-cainjector, cert-manager-webhook)

# CRDs pruefen
kubectl get crds | grep cert-manager
# Erwartete Ausgabe: clusterissuers.cert-manager.io, certificates.cert-manager.io, ...
```

### 2.3 Let's Encrypt Staging ClusterIssuer (optional, empfohlen)

Let's Encrypt hat strikte Rate Limits (50 Zertifikate/Domain/Woche). Fuer den ersten Test empfiehlt sich der Staging-Server:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: nikolaj.ivanov@coffee-studios.de
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

> **[AUSSTEHEND -- Klaerung mit VoeB]** Welche E-Mail-Adresse soll fuer die ACME-Registrierung verwendet werden? Let's Encrypt sendet Ablauf-Warnungen an diese Adresse. Empfehlung: Eine Team-Adresse, keine persoenliche.

---

## Schritt 3: Helm Values anpassen

### 3.1 Onyx Helm Chart: Eingebaute Let's Encrypt Unterstuetzung

Der Onyx Helm Chart bringt **bereits alles mit**:

- **`templates/lets-encrypt.yaml`**: Erstellt einen `ClusterIssuer` fuer Let's Encrypt Production, gesteuert durch `letsencrypt.enabled`.
- **`templates/ingress-api.yaml`** und **`templates/ingress-webserver.yaml`**: Haben `cert-manager.io/cluster-issuer` Annotation und TLS-Bloecke bereits fest eingebaut.
- **`templates/ingress-webserver.yaml`**: Hat zusaetzlich `kubernetes.io/tls-acme: "true"`.

Das Onyx Ingress wird **nur** deployed wenn `ingress.enabled: true` gesetzt ist. Aktuell nutzen DEV und TEST das Ingress **nicht** explizit -- der NGINX Ingress Controller aus dem Subchart routet direkt. Fuer TLS muss das Onyx Ingress aktiviert werden.

### 3.2 Bekanntes Problem: IngressClass im ClusterIssuer

Das Template `lets-encrypt.yaml` (Zeile 19) hat die Ingress-Klasse **hardcoded**:

```yaml
solvers:
  - http01:
      ingress:
        class: nginx
```

Fuer **DEV** (IngressClass `nginx`) funktioniert das. Fuer **TEST** (IngressClass `nginx-test`) funktioniert das **nicht**, weil die HTTP-01 Challenge an den falschen Ingress Controller geht.

**Loesung fuer TEST:** Eigenen ClusterIssuer per kubectl erstellen (nicht ueber den Chart):

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: onyx-test-letsencrypt
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: nikolaj.ivanov@coffee-studios.de
    privateKeySecretRef:
      name: onyx-test-letsencrypt
    solvers:
      - http01:
          ingress:
            class: nginx-test
EOF
```

Und in `values-test.yaml` den Chart-eigenen ClusterIssuer deaktiviert lassen (`letsencrypt.enabled: false`), aber die Ingress-Annotations manuell setzen. Alternativ: `letsencrypt.enabled: true` in TEST und den ClusterIssuer-Namen in den Ingress-Annotations per `--set` ueberschreiben.

> **Hinweis:** Dies ist eine Einschraenkung des Onyx Helm Charts (READ-ONLY, nicht veraenderbar). Falls der Chart in Zukunft die Ingress-Klasse im ClusterIssuer konfigurierbar macht, entfaellt dieser Workaround.

### 3.3 values-dev.yaml -- Aenderungen

**Vorher:**

```yaml
configMap:
  DOMAIN: "188.34.74.187"
  WEB_DOMAIN: "http://188.34.74.187"

letsencrypt:
  enabled: false
```

**Nachher:**

```yaml
configMap:
  DOMAIN: "dev.chatbot.<domain>"
  WEB_DOMAIN: "https://dev.chatbot.<domain>"

letsencrypt:
  enabled: true
  email: "nikolaj.ivanov@coffee-studios.de"

ingress:
  enabled: true
  className: "nginx"
  api:
    host: "dev.chatbot.<domain>"
  webserver:
    host: "dev.chatbot.<domain>"
```

> **WICHTIG:** `WEB_DOMAIN` muss mit `https://` beginnen. Onyx setzt `cookie_secure` basierend auf diesem Prefix (Quelle: `backend/onyx/auth/users.py:915`). Wenn `WEB_DOMAIN` auf `https://` steht aber kein TLS konfiguriert ist, entsteht ein Login-Loop (403 auf `/me`). Daher: **Erst TLS konfigurieren, dann `WEB_DOMAIN` umstellen.**

### 3.4 values-test.yaml -- Aenderungen

**Vorher:**

```yaml
configMap:
  DOMAIN: "188.34.118.201"
  WEB_DOMAIN: "http://188.34.118.201"

letsencrypt:
  enabled: false
```

**Nachher:**

```yaml
configMap:
  DOMAIN: "test.chatbot.<domain>"
  WEB_DOMAIN: "https://test.chatbot.<domain>"

letsencrypt:
  enabled: false  # TEST: Eigener ClusterIssuer (s. Schritt 3.2)

ingress:
  enabled: true
  className: "nginx-test"
  api:
    host: "test.chatbot.<domain>"
  webserver:
    host: "test.chatbot.<domain>"
```

Zusaetzlich muessen die Ingress-Templates den richtigen ClusterIssuer referenzieren. Da der Chart den ClusterIssuer-Namen aus dem Release-Namen generiert (`<release>-letsencrypt`), und wir den ClusterIssuer manuell als `onyx-test-letsencrypt` erstellt haben, passt das -- der Release-Name ist `onyx-test`, also wird `onyx-test-letsencrypt` referenziert.

### 3.5 CI/CD Workflow

Der CI/CD Workflow (`stackit-deploy.yml`) liest `WEB_DOMAIN` aus der ConfigMap fuer den Smoke Test:

```yaml
DOMAIN=$(kubectl get configmap env-configmap -n onyx-dev -o jsonpath='{.data.WEB_DOMAIN}')
curl --silent --fail --max-time 5 "${DOMAIN}/api/health"
```

Nach der Umstellung auf HTTPS muss der Smoke Test HTTPS unterstuetzen. `curl` folgt standardmaessig HTTPS. Falls das Zertifikat noch nicht bereit ist (cert-manager braucht 1-2 Minuten), koennte der Smoke Test initial fehlschlagen.

**Empfehlung:** Beim ersten Deploy nach TLS-Umstellung den Smoke Test manuell ausfuehren oder `--insecure` temporaer hinzufuegen.

---

## Schritt 4: Deploy ausfuehren

### 4.1 Reihenfolge (kritisch)

1. DNS A-Records muessen aufloesen (Schritt 1 verifiziert)
2. cert-manager muss installiert sein (Schritt 2 verifiziert)
3. Fuer TEST: Manueller ClusterIssuer muss existieren (Schritt 3.2)
4. Helm Values committen und deployen

### 4.2 DEV Deploy

```bash
# Option A: CI/CD (empfohlen)
# values-dev.yaml committen + pushen auf develop
# Pipeline deployt automatisch

# Option B: Manuell
helm upgrade --install onyx-dev \
  deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  -f deployment/helm/values/values-dev-secrets.yaml
```

### 4.3 TEST Deploy

```bash
# Option A: CI/CD (workflow_dispatch, Environment: test)

# Option B: Manuell
helm upgrade --install onyx-test \
  deployment/helm/charts/onyx \
  --namespace onyx-test \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-test.yaml \
  --set "auth.postgresql.values.password=<PG_PASSWORD>" \
  --set "auth.redis.values.redis_password=<REDIS_PASSWORD>" \
  --set "auth.objectstorage.values.s3_aws_access_key_id=<S3_KEY>" \
  --set "auth.objectstorage.values.s3_aws_secret_access_key=<S3_SECRET>" \
  --set "configMap.DB_READONLY_PASSWORD=<READONLY_PW>" \
  --atomic --timeout 10m
```

---

## Schritt 5: Verifikation

### 5.1 cert-manager Status pruefen

```bash
# ClusterIssuer-Status (DEV)
kubectl get clusterissuer
# Erwartete Ausgabe: onyx-dev-letsencrypt   True   ...

# Zertifikat-Status (DEV)
kubectl get certificate -n onyx-dev
# Erwartete Ausgabe: onyx-dev-ingress-api-tls       True   ...
#                    onyx-dev-ingress-webserver-tls  True   ...

# Zertifikat-Status (TEST)
kubectl get certificate -n onyx-test
# Erwartete Ausgabe: onyx-test-ingress-api-tls       True   ...
#                    onyx-test-ingress-webserver-tls  True   ...

# Bei Problemen: Challenge-Status pruefen
kubectl get challenges --all-namespaces
# Sollte leer sein (= alle Challenges abgeschlossen)
# Falls Challenges haengen:
kubectl describe challenge <name> -n <namespace>
```

### 5.2 Ingress pruefen

```bash
# DEV
kubectl get ingress -n onyx-dev
# Erwartete Ausgabe: Ingress mit HOST = dev.chatbot.<domain>, TLS-Secret zugewiesen

# TEST
kubectl get ingress -n onyx-test
# Erwartete Ausgabe: Ingress mit HOST = test.chatbot.<domain>, TLS-Secret zugewiesen
```

### 5.3 HTTPS-Zugriff testen

```bash
# DEV
curl -v https://dev.chatbot.<domain>/api/health
# Erwartete Ausgabe:
# * SSL connection using TLS...
# * Server certificate: CN=dev.chatbot.<domain>
# * issuer: C=US; O=Let's Encrypt; CN=...
# {"success":true,"message":"ok","data":null}

# TEST
curl -v https://test.chatbot.<domain>/api/health

# Zertifikat-Details pruefen
echo | openssl s_client -connect dev.chatbot.<domain>:443 -servername dev.chatbot.<domain> 2>/dev/null | openssl x509 -noout -dates -subject
# Erwartete Ausgabe:
# notBefore=...
# notAfter=... (90 Tage nach Ausstellung)
# subject=CN=dev.chatbot.<domain>

# HTTP -> HTTPS Redirect pruefen (falls NGINX so konfiguriert)
curl -s -o /dev/null -w "%{http_code}" http://dev.chatbot.<domain>/api/health
# Erwartete Ausgabe: 308 (Permanent Redirect) oder 301
```

### 5.4 Login testen

```bash
# Browser: https://dev.chatbot.<domain> oeffnen
# Login-Seite muss laden, Login muss funktionieren
# Cookies muessen "Secure" Flag haben (weil WEB_DOMAIN mit https:// beginnt)

# Cookie-Check per curl
curl -c - https://dev.chatbot.<domain>/auth/login 2>/dev/null | grep -i secure
```

### 5.5 Checkliste

- [ ] DNS loest auf (DEV + TEST)
- [ ] cert-manager Pods Running
- [ ] ClusterIssuer Ready
- [ ] Zertifikate ausgestellt (Certificate Ready = True)
- [ ] HTTPS antwortet mit gueltigem Zertifikat
- [ ] HTTP redirectet auf HTTPS
- [ ] API Health Check OK ueber HTTPS
- [ ] Login funktioniert im Browser
- [ ] CI/CD Smoke Test funktioniert mit HTTPS

---

## Schritt 6: Rollback auf HTTP-only

Falls cert-manager nicht funktioniert oder die Zertifikate nicht ausgestellt werden koennen:

### 6.1 Helm Values zuruecksetzen

`values-dev.yaml` zurueck auf:

```yaml
configMap:
  DOMAIN: "188.34.74.187"
  WEB_DOMAIN: "http://188.34.74.187"

letsencrypt:
  enabled: false

ingress:
  enabled: false
```

`values-test.yaml` zurueck auf:

```yaml
configMap:
  DOMAIN: "188.34.118.201"
  WEB_DOMAIN: "http://188.34.118.201"

letsencrypt:
  enabled: false

ingress:
  enabled: false
```

### 6.2 Re-Deploy

```bash
# DEV
helm upgrade onyx-dev \
  deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  -f deployment/helm/values/values-dev-secrets.yaml

# TEST (analog)
```

### 6.3 cert-manager kann installiert bleiben

cert-manager verbraucht minimal Ressourcen und stoert nicht, wenn keine ClusterIssuer/Certificates existieren. Deinstallation nur bei Bedarf:

```bash
helm uninstall cert-manager -n cert-manager
kubectl delete namespace cert-manager
# CRDs manuell entfernen (Helm loescht CRDs nicht automatisch)
kubectl delete crd certificaterequests.cert-manager.io certificates.cert-manager.io \
  challenges.acme.cert-manager.io clusterissuers.cert-manager.io issuers.cert-manager.io \
  orders.acme.cert-manager.io
```

### 6.4 Manuell erstellten ClusterIssuer (TEST) entfernen

```bash
kubectl delete clusterissuer onyx-test-letsencrypt
```

---

## Troubleshooting

| Problem | Ursache | Loesung |
|---------|---------|---------|
| Challenge haengt auf `Pending` | DNS loest nicht auf die richtige IP auf | `dig +short <domain>` pruefen, A-Record korrigieren |
| Challenge haengt auf `Invalid` | HTTP-01 Challenge nicht erreichbar | Ingress-Klasse pruefen, Port 80 muss offen sein |
| Certificate `False` / nicht Ready | ClusterIssuer nicht Ready oder Challenge fehlgeschlagen | `kubectl describe clusterissuer` + `kubectl describe certificate` |
| Login-Loop (403 auf `/me`) | `WEB_DOMAIN` ist HTTPS aber kein TLS | Rollback auf `http://` oder TLS fixen |
| Browser zeigt "unsicheres Zertifikat" | Let's Encrypt Staging benutzt (Fake-CA) | Auf Production-Issuer wechseln |
| Rate Limit erreicht | Zu viele Zertifikats-Anfragen | 1 Stunde warten, Staging fuer Tests nutzen |
| cert-manager Pod CrashLoop | Fehlende CRDs oder RBAC | `helm install` mit `--set crds.enabled=true` wiederholen |
| TEST: Challenge geht an falschen Ingress | ClusterIssuer hat `class: nginx` statt `nginx-test` | Manuellen ClusterIssuer mit `class: nginx-test` erstellen (Schritt 3.2) |

---

## Offene Punkte

| Nr. | Thema | Status |
|-----|-------|--------|
| 1 | Domain-Entscheidung durch VoeB | [AUSSTEHEND -- Klaerung mit VoeB] |
| 2 | DNS A-Records durch VoeB IT | [AUSSTEHEND -- nach Domain-Entscheidung] |
| 3 | ACME-Email-Adresse festlegen | [AUSSTEHEND -- Team-Adresse empfohlen] |
| 4 | PROD LoadBalancer IP | [AUSSTEHEND -- PROD noch nicht provisioniert] |
| 5 | Ingress-Verhalten ohne TLS pruefen | Vor Umstellung testen ob `ingress.enabled: true` auch ohne TLS funktioniert |
| 6 | CI/CD Smoke Test HTTPS-Kompatibilitaet | `curl` sollte HTTPS unterstuetzen, ggf. erster Run nach Umstellung manuell |

---

## Referenzen

- [Helm Deploy Runbook](./helm-deploy.md) -- Domain/Cookie-Konfiguration, WEB_DOMAIN-Details
- [Entra ID Kundenfragen](../entra-id-kundenfragen.md) -- DNS-Abhaengigkeit fuer OIDC (Abschnitt 7)
- [StackIT Implementierungsplan](../referenz/stackit-implementierungsplan.md) -- Aktuelle IPs, Infrastruktur-Status
- [cert-manager Dokumentation](https://cert-manager.io/docs/) -- Offizielle Docs
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/) -- 50 Zertifikate/Domain/Woche
- Onyx Helm Chart Templates: `deployment/helm/charts/onyx/templates/lets-encrypt.yaml`, `ingress-api.yaml`, `ingress-webserver.yaml`
