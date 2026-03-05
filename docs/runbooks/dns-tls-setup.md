# Runbook: DNS + HTTPS Setup (Cloudflare DNS-01)

**Status:** Bereit zur Umsetzung
**Erstellt:** 2026-03-03 | **Aktualisiert:** 2026-03-04
**Erstellt von:** Nikolaj Ivanov (CCJ / Coffee Studios)

---

## Uebersicht

### Aktueller Stand

| Environment | Zugriff | Status |
|-------------|---------|--------|
| DEV | `http://188.34.74.187` | HTTP-only, IP-basiert |
| TEST | `http://188.34.118.201` | HTTP-only, IP-basiert |
| PROD | Noch nicht provisioniert | — |

### Zielzustand

| Environment | Zugriff | Status |
|-------------|---------|--------|
| DEV | `https://dev.chatbot.voeb-service.de` | HTTPS, Let's Encrypt |
| TEST | `https://test.chatbot.voeb-service.de` | HTTPS, Let's Encrypt |
| PROD | `https://chatbot.voeb-service.de` | HTTPS, Let's Encrypt |

> **Subdomain-Name:** `chatbot` (festgelegt durch VoeB, Mail von Leif Rasch, 2026-03-04).
> PROD-URL: `https://chatbot.voeb-service.de`

### Ansatz: cert-manager + Let's Encrypt + Cloudflare DNS-01

```
VoeB: Subdomain festlegen + A-Records + Cloudflare API Token
  -> CCJ: cert-manager installieren
    -> CCJ: ClusterIssuer (Cloudflare DNS-01) erstellen
      -> CCJ: Helm Values anpassen + Deploy
        -> Let's Encrypt stellt Zertifikat automatisch aus
          -> HTTPS funktioniert
            -> Entra ID App-Registrierung moeglich (Phase 3)
```

### Warum DNS-01 statt HTTP-01?

| Kriterium | HTTP-01 | DNS-01 (Cloudflare) |
|-----------|---------|---------------------|
| Validierung | Let's Encrypt ruft Port 80 auf | Let's Encrypt prueft DNS TXT-Record |
| IngressClass-Problem | Ja — Onyx Chart hardcoded `class: nginx`, bricht TEST (`nginx-test`) | Nein — validiert ueber DNS, kein Ingress involviert |
| Cloudflare Proxy | Kann HTTP-01 blockieren wenn Proxy aktiv | Funktioniert immer (DNS-Ebene) |
| Port 80 noetig? | Ja, muss von aussen erreichbar sein | Nein |
| Wildcard-Zertifikate | Nicht moeglich | Moeglich (falls spaeter benoetigt) |
| Setup-Aufwand | Weniger (kein API Token noetig) | Etwas mehr (Cloudflare API Token) |
| **Empfehlung fuer VoeB** | | **<-- Empfohlen** |

**Entscheidend:** Die Domain `voeb-service.de` liegt auf Cloudflare (Pro Account). DNS-01 nutzt die Cloudflare API direkt — das ist der sauberste Weg. cert-manager hat native Cloudflare-Unterstuetzung (kein Webhook/Plugin noetig).

### BSI TR-02102-2 Compliance (Pflicht fuer Bankenumfeld)

Die BSI Technical Guideline TR-02102-2 (Version 2026-01) verlangt:

| Algorithmus | Minimum | BSI-Anforderung seit |
|-------------|---------|----------------------|
| RSA | **3.072 Bit** | Januar 2024 |
| ECDSA | **P-256** (250 Bit minimum), **P-384 empfohlen** | Januar 2024 |

**Problem:** Let's Encrypt RSA-Intermediates nutzen nur 2.048-Bit-Keys — das erfuellt BSI TR-02102-2 **NICHT**. P-256 wuerde technisch genuegen (256 > 250 Bit Minimum), aber ein P-256-Leaf-Zertifikat koennte von Let's Encrypt ueber eine RSA-2048-Intermediate signiert werden — die gesamte Chain muss BSI-konform sein, nicht nur das Leaf.

**Loesung:** Zertifikate explizit als **ECDSA P-384** anfordern. cert-manager unterstuetzt das ueber die `privateKey`-Konfiguration auf Certificate-Ressourcen. Let's Encrypt signiert P-384-Leafs automatisch ueber die ECDSA P-384 Intermediate Chain (aktuell E7/E8), die BSI-konform ist. Damit ist die gesamte Chain ECDSA: Leaf (P-384) → Intermediate E7/E8 (P-384) → Root ISRG X1 (RSA 4096, BSI-konform).

> **Auswirkung auf dieses Runbook:** Wir erstellen explizite Certificate-Ressourcen mit `privateKey.algorithm: ECDSA` und `privateKey.size: 384` (Schritt 3c), statt uns auf die automatische Erstellung durch Ingress-Annotations zu verlassen.

### Datensouveraenitaet — Warum DNS-only (graue Wolke) Pflicht ist

- **Cloudflare Proxy (orange Cloud) wird NICHT verwendet** — kein Traffic ueber Cloudflare
- A-Records werden auf **DNS-only (graue Cloud)** gesetzt
- Cloudflare API wird nur fuer Zertifikats-Validierung genutzt (TXT-Record setzen/loeschen)
- Gesamter Nutzer-Traffic geht direkt zu StackIT (Frankfurt, EU01)
- Kein DSGVO-Risiko durch US-Infrastruktur

> **Verifiziert (2026-03-05, 3 Opus-Agenten mit Quellenrecherche):**
>
> Im Proxy-Modus (orange Wolke) terminiert Cloudflare TLS am Edge und entschluesselt **allen Traffic** — auch bei "Full (Strict)" SSL. Das bedeutet: Chat-Inhalte (LLM-Queries + Responses von Bankmitarbeitern) wuerden im Klartext auf Cloudflare-Servern verarbeitet.
>
> **3 Gruende warum Proxy fuer VoeB nicht in Frage kommt:**
>
> 1. **TLS-Kontrolle:** Cloudflare-Edge-Zertifikate sind ECDSA P-256 (Universal SSL). Unser BSI-konformes P-384-Zertifikat wuerde nur fuer die Cloudflare→Origin-Verbindung genutzt — der Browser sieht es nie. Es gibt keine Moeglichkeit, P-384 auf Cloudflares Edge zu erzwingen (nur mit Enterprise Custom Certs).
> 2. **Datensouveraenitaet:** VoeB Cloudflare-Account ist Pro-Plan. Die Data Localization Suite (EU-only Traffic) ist nur im Enterprise-Plan verfuegbar. Ohne DLS gibt es keine Garantie, dass Traffic in der EU bleibt.
> 3. **DSGVO/Schrems II:** Cloudflare ist US-Unternehmen unter CLOUD Act/FISA 702. EU-US DPF ist zwar aktuell gueltig (General Court Sept 2025), aber CJEU-Appeal laeuft seit Oktober 2025. Fuer Banken-Chat-Daten ist das Restrisiko zu hoch.
>
> **Im DNS-only-Modus sieht Cloudflare nur DNS-Queries (Domainaufloesung) — keine Inhalte, keine Credentials, keine Chat-Daten.**

### Sicherheitshinweis: DEV/TEST-Zugriff einschraenken

Gemaess BAIT und ISO 27002 (Control 8.31) muessen Entwicklungs-, Test- und Produktionsumgebungen getrennt sein. DEV/TEST sollten **nicht** uneingeschraenkt oeffentlich erreichbar sein.

**Empfehlung (Minimum):** IP-Allowlisting auf Ingress-Ebene:
- VoeB Buero-IPs
- CCJ Entwickler-IPs
- StackIT Cluster-Egress-IP (fuer interne Kommunikation)

> Dies kann ueber NGINX Ingress Annotations (`nginx.ingress.kubernetes.io/whitelist-source-range`) oder Kubernetes NetworkPolicies umgesetzt werden. Details werden in einem separaten Schritt nach dem TLS-Setup konfiguriert.

### PROD-Zertifikat: Diskussionspunkt mit VoeB

Fuer **DEV/TEST** ist Let's Encrypt mit ECDSA P-384 vollkommen ausreichend.

Fuer **PROD** (kundensichtbar) sollte mit VoeB diskutiert werden:

| Option | Pro | Contra |
|--------|-----|--------|
| Let's Encrypt (ECDSA P-384) | Kostenlos, automatisiert, BSI-konform | Kein OV/EV, kein SLA, keine Warranty |
| Bezahlte CA (z.B. DigiCert) | OV/EV moeglich, SLA, Warranty, Auditor-freundlich | Kosten (mehrere hundert EUR/Jahr) |

> Beide Optionen koennen mit cert-manager automatisiert werden (DigiCert unterstuetzt ACME). Die Entscheidung betrifft nur PROD und kann spaeter getroffen werden — DEV/TEST starten mit Let's Encrypt.

---

## Teil A: Was VoeB tun muss

> Dieser Abschnitt kann als Grundlage fuer die Mail an Leif/Pascal dienen.

### A1. Subdomain-Name — ERLEDIGT

**Festgelegt:** `chatbot` (Mail von Leif Rasch, 2026-03-04)

| Environment | URL |
|-------------|-----|
| DEV | `https://dev.chatbot.voeb-service.de` |
| TEST | `https://test.chatbot.voeb-service.de` |
| PROD | `https://chatbot.voeb-service.de` |

### A2. DNS A-Records in Cloudflare anlegen (Leif)

In Cloudflare Dashboard → DNS → Records:

| Type | Name | Content (IPv4) | Proxy | TTL |
|------|------|-----------------|-------|-----|
| A | `dev.chatbot` | `188.34.74.187` | **DNS only** (graue Wolke) | 300 |
| A | `test.chatbot` | `188.34.118.201` | **DNS only** (graue Wolke) | 300 |

> **WICHTIG: Proxy-Status MANUELL auf "DNS only" (graue Wolke) umstellen!**
> Cloudflare setzt neue A-Records standardmaessig auf **"Proxied" (orange Wolke)**.
> Das muss aktiv auf "DNS only" (graue Wolke) umgestellt werden — Cloud-Icon anklicken bis es grau ist.
> Grund: Der Traffic soll direkt zu StackIT gehen, nicht ueber Cloudflare geroutet werden.
> Mit "Proxied" wuerde Cloudflare TLS terminieren und unser cert-manager Setup waere wirkungslos.

> **TTL 300** (5 Minuten) fuer die Anfangsphase. Nach Verifikation auf 3600 (1 Stunde) erhoehen.

> PROD A-Record kommt spaeter, wenn der PROD-Cluster provisioniert ist.

### A3. Cloudflare API Token erstellen (Leif)

cert-manager benoetigt einen Cloudflare API Token um DNS-TXT-Records fuer die Zertifikats-Validierung automatisch zu setzen und zu loeschen.

**Schritt-fuer-Schritt:**

1. Cloudflare Dashboard → Profil (oben rechts) → **API Tokens**
2. **"Create Token"** klicken
3. Template **"Edit zone DNS"** auswaehlen, dann **manuell erweitern**:

| Einstellung | Wert |
|-------------|------|
| Token name | `cert-manager-voeb-chatbot` |
| Permissions | **Zone : DNS : Edit** (vom Template) |
| | **Zone : Zone : Read** (MANUELL HINZUFUEGEN — "Add more" klicken!) |
| Zone Resources | Include → Specific zone → `voeb-service.de` |
| Client IP Address Filtering | Keine (cert-manager laeuft im Cluster) |
| TTL | Kein Ablaufdatum (oder z.B. 1 Jahr) |

> **Hinweis:** Das Template "Edit zone DNS" vergibt nur `Zone:DNS:Edit`. cert-manager benoetigt zusaetzlich `Zone:Zone:Read` um die Zone-ID aufzuloesen. Ohne diese Permission schlaegt die Zertifikatsausstellung mit einem Permission-Error fehl.

4. **"Continue to summary"** → **"Create Token"**
5. **Token kopieren und sicher an CCJ (Niko) uebermitteln**

> Der Token wird als Kubernetes Secret im Cluster gespeichert. Er hat ausschliesslich Lese-/Schreibzugriff auf DNS-Records der Zone `voeb-service.de` — kein Zugriff auf andere Cloudflare-Einstellungen, Firewall, Proxy, etc.

### Zusammenfassung fuer VoeB

| # | Aufgabe | Wer | Status |
|---|---------|-----|--------|
| 1 | Subdomain-Name festlegen | Pascal/Leif | **ERLEDIGT** — `chatbot` |
| 2 | 2x DNS A-Record anlegen (DNS-only!) | Leif | Ausstehend |
| 3 | Cloudflare API Token erstellen | Leif | Ausstehend |

**Sobald wir diese 3 Dinge haben, koennen wir HTTPS innerhalb von ~30 Minuten aktivieren.**

---

## Teil B: Was CCJ tut (nach Zulieferung von VoeB)

### Schritt 1: cert-manager installieren

> Einmalig pro Cluster. cert-manager verwaltet Zertifikate automatisch (Ausstellung + Renewal).

```bash
# Namespace erstellen
kubectl create namespace cert-manager

# Helm Repo hinzufuegen
helm repo add jetstack https://charts.jetstack.io
helm repo update

# cert-manager installieren (inkl. CRDs)
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set crds.enabled=true \
  --set crds.keep=true \
  --version v1.18.2
```

**Verifikation:**

```bash
# Alle 3 Pods muessen Running sein
kubectl get pods -n cert-manager
# Erwartete Ausgabe:
# cert-manager-...              1/1   Running
# cert-manager-cainjector-...   1/1   Running
# cert-manager-webhook-...      1/1   Running

# CRDs pruefen
kubectl get crds | grep cert-manager
# Erwartete Ausgabe: clusterissuers, certificates, challenges, ...
```

> **Version:** v1.18.x empfohlen (v1.17.x ist seit Oktober 2025 End-of-Life).
> v1.18.x unterstuetzt K8s 1.29-1.33 (unser Cluster: v1.32). Check: https://cert-manager.io/docs/releases/
>
> **StackIT-Kompatibilitaet (verifiziert 2026-03-05):** cert-manager ist offiziell auf SKE unterstuetzt.
> StackIT bietet eigenes cert-manager Tutorial + Webhook (fuer StackIT DNS). Fuer Cloudflare DNS-01
> wird der native cert-manager Cloudflare-Solver verwendet — kein Webhook noetig.
> Outbound-Zugriff auf Let's Encrypt ACME + Cloudflare API ist auf SKE standardmaessig erlaubt.

### Schritt 2: Cloudflare API Token als Kubernetes Secret

```bash
# Secret in cert-manager Namespace erstellen
# (Token von Leif erhalten, siehe Teil A, Schritt A3)
kubectl create secret generic cloudflare-api-token \
  --namespace cert-manager \
  --from-literal=api-token="<CLOUDFLARE_API_TOKEN>"
```

> **Sicherheit:** Der Token liegt nur als K8s Secret im Cluster. Nicht in Git, nicht in Helm Values.

### Schritt 3: ClusterIssuers erstellen (DNS-01 + Cloudflare)

Wir erstellen **zwei ClusterIssuers** — einen pro Environment. Die Namen muessen exakt mit dem uebereinstimmen, was die Onyx Helm Chart Ingress-Templates erwarten:
- DEV: `onyx-dev-letsencrypt` (Ingress-Annotation referenziert `{{ fullname }}-letsencrypt`)
- TEST: `onyx-test-letsencrypt`

> **Warum nicht den Chart-eigenen ClusterIssuer?**
> Der Onyx Chart (`lets-encrypt.yaml`) erstellt einen ClusterIssuer mit HTTP-01 und hardcoded `class: nginx`. Das funktioniert nicht mit DNS-01 und nicht mit TEST (`nginx-test`). Daher: `letsencrypt.enabled: false` im Chart, eigene ClusterIssuers mit DNS-01.

#### 3a. Staging ClusterIssuers (Empfohlen fuer ersten Test)

Let's Encrypt Staging hat keine Rate Limits. Zertifikate sind nicht browser-trusted, aber beweisen dass der Flow funktioniert.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: onyx-dev-letsencrypt
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: nikolaj.ivanov@coffee-studios.de
    privateKeySecretRef:
      name: onyx-dev-letsencrypt-account
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: onyx-test-letsencrypt
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: nikolaj.ivanov@coffee-studios.de
    privateKeySecretRef:
      name: onyx-test-letsencrypt-account
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
EOF
```

**Verifikation:**

```bash
kubectl get clusterissuer
# Erwartete Ausgabe:
# NAME                      READY   AGE
# onyx-dev-letsencrypt      True    ...
# onyx-test-letsencrypt     True    ...
```

> Falls READY = False: `kubectl describe clusterissuer onyx-dev-letsencrypt` — meistens liegt es am API Token (falsch, abgelaufen, falsche Permissions).

#### 3b. Auf Production umschalten (nach erfolgreichem Staging-Test)

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: onyx-dev-letsencrypt
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: nikolaj.ivanov@coffee-studios.de
    privateKeySecretRef:
      name: onyx-dev-letsencrypt-account
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: onyx-test-letsencrypt
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: nikolaj.ivanov@coffee-studios.de
    privateKeySecretRef:
      name: onyx-test-letsencrypt-account
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
EOF
```

> **Unterschied:** `server:` zeigt auf `acme-v02` statt `acme-staging-v02`.
> Nach dem Wechsel muessen die alten Staging-Zertifikate geloescht werden, damit cert-manager neue (browser-trusted) Zertifikate ausstellt:

```bash
# Nur die spezifischen Certificates loeschen (NICHT --all!)
kubectl delete certificate onyx-dev-ingress-webserver-tls onyx-dev-ingress-api-tls -n onyx-dev
kubectl delete certificate onyx-test-ingress-webserver-tls onyx-test-ingress-api-tls -n onyx-test
# Dann Schritt 3c wiederholen (Certificate-Ressourcen neu erstellen)
# cert-manager stellt automatisch neue Zertifikate ueber den Production-Issuer aus (1-2 Min)
```

> **Rate-Limit-Warnung:** Let's Encrypt Production erlaubt max. **5 identische Zertifikate pro Domain pro Woche**. Bei Debugging immer ZUERST den Staging-Issuer verwenden (Schritt 3a). Nur auf Production wechseln wenn Staging erfolgreich war. Staging hat KEINE Rate Limits.

### Schritt 3c: Explizite Certificate-Ressourcen (ECDSA P-384, BSI-konform)

> **Warum explizite Certificates?** Die Onyx Ingress-Templates enthalten hardcoded Annotations (`cert-manager.io/cluster-issuer` + `kubernetes.io/tls-acme: "true"`), die cert-manager veranlassen wuerden, automatisch Certificate-Ressourcen zu erstellen — allerdings mit dem Default **RSA 2048**, was BSI TR-02102-2 **nicht erfuellt**. Durch explizite Certificate-Ressourcen erzwingen wir ECDSA P-384.
>
> **KRITISCH — Reihenfolge beachten:**
> Diese Certificates **MUESSEN VOR dem Helm Deploy** (Schritt 5) erstellt werden und **READY = True** sein.
> cert-manager's Ingress-Shim prueft beim Ingress-Deploy: Existiert bereits ein Certificate fuer diesen secretName? Wenn ja (und es hat keinen ownerReference auf den Ingress), wird es **NICHT ueberschrieben**.
> Wenn die Certificates NICHT existieren, erstellt der Ingress-Shim automatisch RSA-2048-Certificates — BSI-Verstoss!
>
> **Bekannte Einschraenkung (Chart READ-ONLY):** Die `tls-acme` und `cluster-issuer` Annotations koennen nicht entfernt werden, da der Onyx Helm Chart nicht veraenderbar ist. Der Workaround (explizite Certificates VOR Deploy) ist stabil, solange die Reihenfolge eingehalten wird. Falls jemand die Certificates manuell loescht (z.B. beim Debugging), wuerde der Ingress-Shim sofort RSA-2048-Replacements erstellen. In dem Fall: Explicit Certificates neu erstellen und die auto-erstellten loeschen.

> **Subdomain-Name steht fest: `chatbot`.** Die folgenden YAML-Manifeste verwenden die finalen Domainnamen.

#### DEV Certificates

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: onyx-dev-ingress-webserver-tls
  namespace: onyx-dev
spec:
  secretName: onyx-dev-ingress-webserver-tls
  issuerRef:
    name: onyx-dev-letsencrypt
    kind: ClusterIssuer
  privateKey:
    algorithm: ECDSA
    size: 384
  dnsNames:
    - dev.chatbot.voeb-service.de
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: onyx-dev-ingress-api-tls
  namespace: onyx-dev
spec:
  secretName: onyx-dev-ingress-api-tls
  issuerRef:
    name: onyx-dev-letsencrypt
    kind: ClusterIssuer
  privateKey:
    algorithm: ECDSA
    size: 384
  dnsNames:
    - dev.chatbot.voeb-service.de
EOF
```

#### TEST Certificates

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: onyx-test-ingress-webserver-tls
  namespace: onyx-test
spec:
  secretName: onyx-test-ingress-webserver-tls
  issuerRef:
    name: onyx-test-letsencrypt
    kind: ClusterIssuer
  privateKey:
    algorithm: ECDSA
    size: 384
  dnsNames:
    - test.chatbot.voeb-service.de
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: onyx-test-ingress-api-tls
  namespace: onyx-test
spec:
  secretName: onyx-test-ingress-api-tls
  issuerRef:
    name: onyx-test-letsencrypt
    kind: ClusterIssuer
  privateKey:
    algorithm: ECDSA
    size: 384
  dnsNames:
    - test.chatbot.voeb-service.de
EOF
```

**Verifikation:**

```bash
# Zertifikate muessen nach 1-2 Minuten READY = True sein
kubectl get certificate -n onyx-dev
kubectl get certificate -n onyx-test

# Schluesseltyp pruefen (nach Ausstellung)
kubectl get secret onyx-dev-ingress-webserver-tls -n onyx-dev -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text | grep "Public Key Algorithm"
# Erwartete Ausgabe: id-ecPublicKey (= ECDSA)

kubectl get secret onyx-dev-ingress-webserver-tls -n onyx-dev -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text | grep "ASN1 OID"
# Erwartete Ausgabe: secp384r1 (= P-384)
```

### Schritt 4: Helm Values anpassen

#### 4.1 values-dev.yaml — Aenderungen

```yaml
# VORHER:
configMap:
  DOMAIN: "188.34.74.187"
  WEB_DOMAIN: "http://188.34.74.187"

letsencrypt:
  enabled: false

# NACHHER:
configMap:
  DOMAIN: "dev.chatbot.voeb-service.de"
  WEB_DOMAIN: "https://dev.chatbot.voeb-service.de"

letsencrypt:
  enabled: false  # Wir nutzen eigenen ClusterIssuer (DNS-01), nicht den Chart-eigenen (HTTP-01)

ingress:
  enabled: true
  className: "nginx"
  api:
    host: "dev.chatbot.voeb-service.de"
  webserver:
    host: "dev.chatbot.voeb-service.de"
```

#### 4.2 values-test.yaml — Aenderungen

```yaml
# VORHER:
configMap:
  DOMAIN: "188.34.118.201"
  WEB_DOMAIN: "http://188.34.118.201"

letsencrypt:
  enabled: false

# NACHHER:
configMap:
  DOMAIN: "test.chatbot.voeb-service.de"
  WEB_DOMAIN: "https://test.chatbot.voeb-service.de"

letsencrypt:
  enabled: false  # Eigener ClusterIssuer (DNS-01)

ingress:
  enabled: true
  className: "nginx-test"
  api:
    host: "test.chatbot.voeb-service.de"
  webserver:
    host: "test.chatbot.voeb-service.de"
```

#### 4.3 Wichtige Hinweise

> **`WEB_DOMAIN` mit `https://`:** Onyx setzt `cookie_secure` basierend auf diesem Prefix (Quelle: `backend/onyx/auth/users.py`, Funktion `cookie_secure`). Wenn `WEB_DOMAIN` auf `https://` steht aber kein TLS aktiv ist, entsteht ein Login-Loop (403 auf `/me`).
>
> **Reihenfolge beachten:**
> 1. DNS muss aufloesen (A-Records gesetzt)
> 2. ClusterIssuers muessen READY sein
> 3. ERST DANN Helm Values umstellen + deployen
>
> **`letsencrypt.enabled` bleibt `false`:** Der Chart-eigene ClusterIssuer (HTTP-01, hardcoded `class: nginx`) wird NICHT genutzt. Unsere manuell erstellten ClusterIssuers (DNS-01, Cloudflare) uebernehmen.

#### 4.4 CI/CD Smoke Test

Der Smoke Test in `.github/workflows/stackit-deploy.yml` liest `WEB_DOMAIN` aus der ConfigMap:

```yaml
DOMAIN=$(kubectl get configmap env-configmap -n onyx-dev -o jsonpath='{.data.WEB_DOMAIN}')
curl --silent --fail --max-time 5 "${DOMAIN}/api/health"
```

Nach der Umstellung auf HTTPS kann der erste Deploy fehlschlagen, weil cert-manager 1-2 Minuten fuer die Zertifikatsausstellung braucht. Beim ersten TLS-Deploy empfohlen:

```yaml
# Temporaer: --retry hinzufuegen oder manuell deployen
curl --silent --fail --max-time 10 --retry 3 --retry-delay 15 "${DOMAIN}/api/health"
```

Alternativ: Ersten Deploy nach TLS-Umstellung manuell per `helm upgrade` ausfuehren (nicht ueber CI/CD), und erst danach CI/CD nutzen.

### Schritt 5: Deploy ausfuehren

#### Reihenfolge (kritisch!)

1. DNS A-Records muessen aufloesen (**VoeB**, Schritt A2)
2. cert-manager muss installiert sein (Schritt 1)
3. Cloudflare API Token Secret muss existieren (Schritt 2)
4. ClusterIssuers muessen READY sein (Schritt 3a/3b)
5. Certificate-Ressourcen muessen existieren + READY sein (Schritt 3c)
6. **Erst jetzt:** Helm Values committen und deployen

#### Gate-Check vor Deploy (PFLICHT)

```bash
# ALLE Voraussetzungen pruefen bevor Helm Deploy gestartet wird:

# 1. DNS
dig +short dev.chatbot.voeb-service.de | grep -q "188.34.74.187" && echo "DNS DEV: OK" || echo "STOP: DNS DEV nicht aufgeloest!"

# 2. ClusterIssuers
kubectl get clusterissuer onyx-dev-letsencrypt -o jsonpath='{.status.conditions[0].status}' | grep -q "True" && echo "Issuer DEV: OK" || echo "STOP: ClusterIssuer DEV nicht ready!"
kubectl get clusterissuer onyx-test-letsencrypt -o jsonpath='{.status.conditions[0].status}' | grep -q "True" && echo "Issuer TEST: OK" || echo "STOP: ClusterIssuer TEST nicht ready!"

# 3. Certificates (KRITISCH — ohne diese erstellt Ingress-Shim RSA-2048-Certs!)
kubectl get certificate onyx-dev-ingress-webserver-tls -n onyx-dev -o jsonpath='{.status.conditions[0].status}' | grep -q "True" && echo "Cert DEV Web: OK" || echo "STOP: Certificate DEV Web nicht ready!"
kubectl get certificate onyx-dev-ingress-api-tls -n onyx-dev -o jsonpath='{.status.conditions[0].status}' | grep -q "True" && echo "Cert DEV API: OK" || echo "STOP: Certificate DEV API nicht ready!"
kubectl get certificate onyx-test-ingress-webserver-tls -n onyx-test -o jsonpath='{.status.conditions[0].status}' | grep -q "True" && echo "Cert TEST Web: OK" || echo "STOP: Certificate TEST Web nicht ready!"
kubectl get certificate onyx-test-ingress-api-tls -n onyx-test -o jsonpath='{.status.conditions[0].status}' | grep -q "True" && echo "Cert TEST API: OK" || echo "STOP: Certificate TEST API nicht ready!"

# Nur weitermachen wenn ALLE Checks "OK" zeigen!
```

#### DEV Deploy

```bash
# Option A: CI/CD (empfohlen nach erstem erfolgreichen TLS-Deploy)
# values-dev.yaml committen + pushen auf main
# Pipeline deployt automatisch (oder workflow_dispatch)

# Option B: Manuell (empfohlen fuer ersten TLS-Deploy)
helm upgrade --install onyx-dev \
  deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  -f deployment/helm/values/values-dev-secrets.yaml \
  --atomic --timeout 10m
```

#### TEST Deploy

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
  --set "auth.dbreadonly.values.db_readonly_password=<READONLY_PW>" \
  --atomic --timeout 10m
```

### Schritt 6: Verifikation

#### 6.1 DNS pruefen

```bash
dig +short dev.chatbot.voeb-service.de
# Erwartete Ausgabe: 188.34.74.187

dig +short test.chatbot.voeb-service.de
# Erwartete Ausgabe: 188.34.118.201
```

#### 6.2 cert-manager Status pruefen

```bash
# ClusterIssuers
kubectl get clusterissuer
# Erwartete Ausgabe: onyx-dev-letsencrypt True, onyx-test-letsencrypt True

# Zertifikate DEV
kubectl get certificate -n onyx-dev
# Erwartete Ausgabe:
# onyx-dev-ingress-api-tls         True   ...
# onyx-dev-ingress-webserver-tls   True   ...

# Zertifikate TEST
kubectl get certificate -n onyx-test
# Erwartete Ausgabe:
# onyx-test-ingress-api-tls         True   ...
# onyx-test-ingress-webserver-tls   True   ...

# Falls Certificate NICHT True:
kubectl describe certificate onyx-dev-ingress-webserver-tls -n onyx-dev
kubectl get challenges --all-namespaces
kubectl describe challenge <name> -n <namespace>
```

#### 6.3 Ingress pruefen

```bash
kubectl get ingress -n onyx-dev
# HOST = dev.chatbot.voeb-service.de, TLS-Secret zugewiesen

kubectl get ingress -n onyx-test
# HOST = test.chatbot.voeb-service.de, TLS-Secret zugewiesen
```

#### 6.4 HTTPS testen

```bash
# DEV
curl -v https://dev.chatbot.voeb-service.de/api/health
# Erwartete Ausgabe:
# * SSL connection using TLSv1.3
# * Server certificate: CN=dev.chatbot.voeb-service.de
# * issuer: C=US; O=Let's Encrypt; CN=...
# {"success":true,"message":"ok","data":null}

# TEST
curl -v https://test.chatbot.voeb-service.de/api/health

# Zertifikat-Details
echo | openssl s_client -connect dev.chatbot.voeb-service.de:443 \
  -servername dev.chatbot.voeb-service.de 2>/dev/null | \
  openssl x509 -noout -dates -subject -issuer
```

#### 6.5 BSI-Konformitaet pruefen (ECDSA P-384)

```bash
# Schluesseltyp pruefen (muss ECDSA/secp384r1 sein, NICHT RSA 2048)
echo | openssl s_client -connect dev.chatbot.voeb-service.de:443 \
  -servername dev.chatbot.voeb-service.de 2>/dev/null | \
  openssl x509 -noout -text | grep -A2 "Public Key Algorithm"
# Erwartete Ausgabe:
# Public Key Algorithm: id-ecPublicKey
#   Public-Key: (384 bit)
#   ASN1 OID: secp384r1

# Intermediate-Chain pruefen (muss ECDSA sein, nicht RSA 2048)
echo | openssl s_client -connect dev.chatbot.voeb-service.de:443 \
  -servername dev.chatbot.voeb-service.de -showcerts 2>/dev/null | \
  openssl x509 -noout -issuer
# Erwartete Ausgabe: issuer= ... O=Let's Encrypt, CN=E7 (oder E8)
# E7/E8 = aktive ECDSA P-384 Intermediates (BSI-konform, seit Juni 2024)
# E5/E6 = retired, E9 = Emergency Backup
# R10-R14 = RSA 2048 Intermediates (NICHT BSI-konform)
```

> **Falls RSA statt ECDSA:** Certificate-Ressource loeschen und neu erstellen (Schritt 3c). cert-manager erstellt dann ein neues Zertifikat mit dem richtigen Schluesseltyp.

#### 6.6 HTTP → HTTPS Redirect pruefen

```bash
curl -s -o /dev/null -w "%{http_code}" http://dev.chatbot.voeb-service.de/api/health
# Erwartete Ausgabe: 308 (Permanent Redirect)
```

#### 6.7 Login testen

```bash
# Browser: https://dev.chatbot.voeb-service.de oeffnen
# Login-Seite muss laden, Login muss funktionieren
# Bei Basic Auth: Normaler Login
# Cookies muessen "Secure" Flag haben (weil WEB_DOMAIN mit https:// beginnt)
```

#### 6.8 Checkliste

- [ ] DNS loest auf (DEV + TEST)
- [ ] cert-manager 3 Pods Running
- [ ] ClusterIssuers Ready = True
- [ ] Zertifikate ausgestellt (Certificate Ready = True)
- [ ] Zertifikat ist ECDSA P-384 (BSI TR-02102-2 konform)
- [ ] Intermediate Chain ist ECDSA (E5-E9, nicht R10-R14)
- [ ] HTTPS antwortet mit gueltigem Zertifikat (nicht Staging!)
- [ ] HTTP redirectet auf HTTPS (308)
- [ ] API Health Check OK ueber HTTPS
- [ ] Login funktioniert im Browser
- [ ] CI/CD Smoke Test funktioniert mit HTTPS

---

## Rollback auf HTTP-only

Falls etwas schiefgeht:

### Helm Values zuruecksetzen

**values-dev.yaml:**

```yaml
configMap:
  DOMAIN: "188.34.74.187"
  WEB_DOMAIN: "http://188.34.74.187"

letsencrypt:
  enabled: false

# ingress: Block komplett entfernen oder:
ingress:
  enabled: false
```

**values-test.yaml:**

```yaml
configMap:
  DOMAIN: "188.34.118.201"
  WEB_DOMAIN: "http://188.34.118.201"

letsencrypt:
  enabled: false

ingress:
  enabled: false
```

### Certificate-Ressourcen entfernen

```bash
kubectl delete certificate onyx-dev-ingress-webserver-tls onyx-dev-ingress-api-tls -n onyx-dev
kubectl delete certificate onyx-test-ingress-webserver-tls onyx-test-ingress-api-tls -n onyx-test
```

### Re-Deploy

```bash
helm upgrade onyx-dev deployment/helm/charts/onyx \
  --namespace onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  -f deployment/helm/values/values-dev-secrets.yaml \
  --atomic --timeout 10m

# TEST analog (mit --set fuer Secrets)
```

### Aufraeum-Optionen

```bash
# ClusterIssuers entfernen (optional, stoeren nicht)
kubectl delete clusterissuer onyx-dev-letsencrypt onyx-test-letsencrypt

# cert-manager kann installiert bleiben (minimal Ressourcen)
# Deinstallation nur bei Bedarf:
helm uninstall cert-manager -n cert-manager
kubectl delete namespace cert-manager
kubectl delete crd certificaterequests.cert-manager.io certificates.cert-manager.io \
  challenges.acme.cert-manager.io clusterissuers.cert-manager.io \
  issuers.cert-manager.io orders.acme.cert-manager.io
```

---

## Zertifikat-Erneuerung (Auto-Renewal)

cert-manager erneuert Zertifikate **automatisch** — kein manuelles Eingreifen noetig.

| Parameter | Wert |
|-----------|------|
| Let's Encrypt Zertifikatslaufzeit | 90 Tage (geplant: 45 Tage ab 2028) |
| cert-manager Renewal-Zeitpunkt | 2/3 der Laufzeit (= ca. Tag 60 bei 90 Tagen) |
| Retry bei Fehler | Automatisch mit exponentiellem Backoff |
| ACME-Email-Benachrichtigung | 14, 7, 1 Tag vor Ablauf (falls Renewal fehlschlaegt) |

**Pruefen ob Renewal funktioniert:**

```bash
kubectl get certificate --all-namespaces -o wide
# READY = True, NOT AFTER zeigt das Ablaufdatum
# RENEWAL zeigt wann cert-manager erneuern wird

# Events pruefen bei Problemen:
kubectl describe certificate onyx-dev-ingress-webserver-tls -n onyx-dev
```

> **ACME-Email:** Let's Encrypt sendet Ablauf-Warnungen an die in den ClusterIssuers konfigurierte Email-Adresse. Empfehlung: Team-Mailbox statt persoenliche Adresse (z.B. `infra@coffee-studios.de`), damit Warnungen nicht untergehen.

## Cloudflare API Token Rotation

Falls Leif den Cloudflare API Token erneuert (z.B. Sicherheitsrotation):

```bash
# Altes Secret loeschen und neues erstellen
kubectl delete secret cloudflare-api-token -n cert-manager
kubectl create secret generic cloudflare-api-token \
  --namespace cert-manager \
  --from-literal=api-token="<NEUER_TOKEN_VON_LEIF>"

# Verifikation: ClusterIssuers pruefen (muessen READY bleiben)
kubectl get clusterissuer
# Falls Status sich auf False aendert: Token-Permissions pruefen (Zone:Zone:Read + Zone:DNS:Edit)
```

> Token-Rotation hat keinen Einfluss auf bestehende Zertifikate — nur auf zukuenftige Ausstellungen und Renewals. Idealerweise Token rotieren, wenn die naechste Renewal noch >30 Tage entfernt ist.

## Troubleshooting

| Problem | Ursache | Loesung |
|---------|---------|---------|
| ClusterIssuer READY = False | Cloudflare API Token falsch oder abgelaufen | `kubectl describe clusterissuer` — Token pruefen, Secret neu erstellen |
| Challenge haengt auf `Pending` | DNS propagiert noch nicht | `dig +short <domain>` pruefen, 5-30 Min warten |
| Challenge `Failed` / `Invalid` | Cloudflare API Token hat falsche Permissions | Token braucht Zone:Zone:Read + Zone:DNS:Edit fuer `voeb-service.de` |
| Certificate nicht True nach 5 Min | Challenge fehlgeschlagen | `kubectl describe challenge <name>` — Details pruefen |
| Browser: "Unsicheres Zertifikat" | Staging-Issuer statt Production | Auf Production umschalten (Schritt 3b), Zertifikate loeschen |
| Login-Loop (403 auf `/me`) | `WEB_DOMAIN` ist HTTPS aber kein TLS aktiv | Rollback auf `http://` oder TLS fixen |
| Ingress 404 | `ingress.enabled: false` oder Host stimmt nicht | Helm Values pruefen: `ingress.enabled: true`, Hosts korrekt |
| Kein Redirect HTTP→HTTPS | NGINX Config fehlt | NGINX default-ssl-redirect steht normalerweise auf true |
| CI/CD Smoke Test schlaegt fehl | Zertifikat noch nicht bereit beim ersten Deploy | Manuell deployen oder `--retry` im curl |
| `Forbidden` beim DNS-01 Challenge | Cloudflare Token auf falsche Zone eingeschraenkt | Token muss Zone `voeb-service.de` einschliessen |
| A-Record zeigt auf orange Wolke | Cloudflare Proxy aktiv statt DNS-only | In Cloudflare auf graue Wolke (DNS-only) umstellen |
| Zertifikat ist RSA 2048 statt ECDSA P-384 | Ingress-Shim hat auto-erstellt (Schritt 3c uebersprungen oder Cert geloescht) | Explicit Certificates aus Schritt 3c neu erstellen, auto-erstellte loeschen |
| Renewal schlaegt fehl | Cloudflare API Token abgelaufen oder rotiert | Token im K8s Secret aktualisieren (siehe "Token Rotation" oben) |
| `Zone not found` Fehler bei Challenge | Cloudflare Token hat kein `Zone:Zone:Read` | Token mit korrekten Permissions neu erstellen (Schritt A3) |

---

## Offene Punkte

| Nr. | Thema | Status | Wer |
|-----|-------|--------|-----|
| 1 | Subdomain-Name festlegen | **ERLEDIGT** — `chatbot` (2026-03-04) | Pascal/Leif (VoeB) |
| 2 | DNS A-Records in Cloudflare anlegen | **ERLEDIGT** (2026-03-05) — ⚠️ Proxy auf DNS-only umstellen! | Leif (VoeB) |
| 3 | Cloudflare API Token erstellen + uebermitteln | **ERLEDIGT** (2026-03-05) | Leif (VoeB) |
| 4 | ACME-Email-Adresse — Team-Adresse statt persoenliche? | Empfehlung: Team-Adresse | CCJ + VoeB |
| 5 | PROD: LoadBalancer IP + A-Record | Spaeter (PROD nicht provisioniert) | CCJ + VoeB |
| 6 | Let's Encrypt Zertifikat-Renewal verifizieren | Nach 60 Tagen pruefen (auto-renew) | CCJ |

---

## Zeitplan

| Schritt | Dauer | Abhaengigkeit |
|---------|-------|---------------|
| VoeB: Subdomain + A-Records + Token | 1-3 Tage | Pascal + Leif |
| CCJ: cert-manager + ClusterIssuers | ~15 Min | Token von Leif |
| CCJ: Helm Values + Deploy DEV | ~15 Min | DNS muss aufloesen |
| CCJ: Verifikation DEV | ~10 Min | Deploy abgeschlossen |
| CCJ: Deploy + Verifikation TEST | ~15 Min | DEV erfolgreich |
| **Gesamt CCJ-Aufwand** | **~1 Stunde** | |

---

## Referenzen

- [cert-manager Cloudflare DNS-01 Docs](https://cert-manager.io/docs/configuration/acme/dns01/cloudflare/)
- [cert-manager Certificate privateKey Config](https://cert-manager.io/docs/reference/api-docs/#cert-manager.io/v1.CertificatePrivateKey)
- [Cloudflare API Tokens erstellen](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
- [Let's Encrypt Challenge Types](https://letsencrypt.org/docs/challenge-types/) — DNS-01 vs HTTP-01
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/) — 50 Zertifikate/Domain/Woche
- [Let's Encrypt Generation Y Hierarchy](https://letsencrypt.org/2025/11/24/gen-y-hierarchy) — ECDSA P-384 Intermediates
- [BSI TR-02102-2 TLS-Richtlinie (2026-01)](https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.html) — RSA 3072 / ECDSA P-384 Minimum
- [Helm Deploy Runbook](./helm-deploy.md) — Domain/Cookie-Konfiguration
- [Entra ID Kundenfragen](../entra-id-kundenfragen.md) — HTTPS-Abhaengigkeit fuer OIDC (Abschnitt 7)
- [StackIT Implementierungsplan](../referenz/stackit-implementierungsplan.md) — IPs, Infrastruktur
- Onyx Helm Chart Templates: `deployment/helm/charts/onyx/templates/lets-encrypt.yaml`, `ingress-api.yaml`, `ingress-webserver.yaml`
