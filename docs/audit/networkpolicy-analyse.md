# NetworkPolicy-Analyse (C5/SEC-03)

> **Datum:** 2026-03-05
> **Autor:** Nikolaj Ivanov (CCJ / Coffee Studios)
> **Status:** DEV + TEST angewendet (2026-03-05)
> **Audit-Referenz:** C5 (CRITICAL) + SEC-03 (P1) aus `cloud-infrastruktur-audit-2026-03-04.md`
> **Cluster:** StackIT SKE, K8s v1.32.12, Region EU01 Frankfurt

---

## 1. Ausgangslage

### 1.1 Problem

Es existieren **keine NetworkPolicies** im gesamten Projekt — weder im Onyx Helm Chart noch als Custom-Ressourcen. Kubernetes erlaubt standardmaessig jegliche Kommunikation zwischen allen Pods in allen Namespaces ("default allow-all").

**Konsequenzen:**

- DEV-Pods (`onyx-dev`) koennen uneingeschraenkt TEST-Pods (`onyx-test`) erreichen und umgekehrt
- Kompromittierte Pods koennen lateral zu jedem anderen Service im Cluster kommunizieren
- Keine Einhaltung des Least-Privilege-Prinzips (BSI IT-Grundschutz, BAIT)
- Kein Nachweis der Umgebungstrennung fuer die VoeB-Abnahme (ISO 27002 Control 8.31)

### 1.2 Pruefung: Existierende NetworkPolicies

```bash
# Suchergebnis (2026-03-05): 0 Treffer
find . -name "*networkpolic*" -o -name "*network-polic*"
grep -r "NetworkPolicy" deployment/helm/charts/onyx/templates/
```

**Einzige Referenz:** `values.yaml:1049` unter Code Interpreter (deaktiviert: `codeInterpreter.enabled: false`), nicht relevant.

### 1.3 CNI-Plugin: Calico (verifiziert)

StackIT SKE basiert auf Gardener und verwendet **Calico** als CNI-Plugin.

**Nachweis:**

1. Eigene Infrastruktur-Doku (`docs/referenz/stackit-implementierungsplan.md`, Zeile 318-321):
   ```
   kube-system (Calico, DNS, VPN, Metrics) | ~1.4 CPU | ~2 Gi
   ```
2. StackIT SKE Security-Hardening-Guide empfiehlt explizit NetworkPolicies mit YAML-Beispielen
   (Quelle: docs.stackit.cloud — "How to enhance the security of your SKE cluster")
3. Gardener verwendet `gardener-extension-networking-calico` als Standard-CNI
   (Quelle: gardener.cloud — Extension-Dokumentation)

**Fazit:** NetworkPolicies funktionieren out-of-the-box. Kein zusaetzliches Setup erforderlich.

---

## 2. Cluster-Topologie

### 2.1 Namespaces und Environments

| Environment | Namespace | Helm Release | Nodes | IngressClass | LoadBalancer IP |
|-------------|-----------|-------------|-------|-------------|-----------------|
| DEV | `onyx-dev` | `onyx-dev` | shared | `nginx` | `188.34.74.187` |
| TEST | `onyx-test` | `onyx-test` | shared | `nginx-test` | `188.34.118.201` |

- Node Pool: `devtest` (2x g1a.4d), geteilt zwischen DEV und TEST
- Egress-IP (Cluster): `188.34.93.194`
- redis-operator laeuft im `default` Namespace (kommuniziert nur ueber K8s API, kein pod-to-pod)

### 2.2 Aktive Pods pro Environment

Lightweight-Modus (`USE_LIGHTWEIGHT_BACKGROUND_WORKER: "true"`): Separate Celery-Worker sind deaktiviert (replicaCount: 0).

| # | Pod | Deployment-Name (DEV) | Service-Port | Funktion |
|---|-----|-----------------------|-------------|----------|
| 1 | nginx Controller | `onyx-dev-nginx-controller` | 80 (LB) → 1024 (container) | Reverse Proxy, Entrypoint |
| 2 | API Server | `onyx-dev-api-server` | 8080 (ClusterIP) | FastAPI Backend |
| 3 | Web Server | `onyx-dev-web-server` | 3000 (ClusterIP) | Next.js Frontend |
| 4 | Inference Model Server | `onyx-dev-inference-model` | 9000 (ClusterIP) | NLP-Modelle (Inference) |
| 5 | Indexing Model Server | `onyx-dev-indexing-model` | 9000 (ClusterIP) | NLP-Modelle (Indexing) |
| 6 | Celery Beat | `onyx-dev-celery-beat` | -- (kein Service) | Task-Scheduler |
| 7 | Celery Worker Primary | `onyx-dev-celery-worker-primary` | -- (kein Service) | Background-Tasks (alle) |
| 8 | Vespa | `da-vespa` (StatefulSet) | 8081 + 19071 (Headless) | Vektor-Datenbank |
| 9 | Redis | `onyx-dev` (CRD) | 6379 (ClusterIP) | Cache + Celery Broker |

TEST ist identisch, aber 9 Pods (redis-operator laeuft nur einmal im `default` NS).

---

## 3. Traffic-Matrix (verifiziert aus Helm Chart Templates)

### 3.1 Interne Kommunikation (Pod-zu-Pod)

Quellen: `templates/nginx-conf.yaml`, `templates/configmap.yaml`, `backend/onyx/configs/app_configs.py`

```
QUELLE                  → ZIEL                           PORT    ZWECK
─────────────────────────────────────────────────────────────────────────────
nginx                   → api-server                     8080    /api/* Reverse Proxy
nginx                   → web-server                     3000    /* Frontend Proxy

web-server              → api-server                     8080    INTERNAL_URL (SSR)

api-server              → redis                          6379    Cache + Sessions
api-server              → vespa                          8081    Query + Feed
api-server              → vespa                          19071   Config + Tenant API
api-server              → inference-model-server          9000    NLP Inference

celery-beat             → redis                          6379    Celery Broker

celery-worker-primary   → redis                          6379    Celery Broker
celery-worker-primary   → vespa                          8081    Document Sync
celery-worker-primary   → vespa                          19071   Schema Management
celery-worker-primary   → inference-model-server          9000    NLP fuer Search
celery-worker-primary   → indexing-model-server           9000    Embedding bei Indexierung
celery-worker-primary   → api-server                     8080    INTERNAL_URL
```

### 3.2 Externe Kommunikation (Egress)

| Pod(s) | Ziel | Port | Protokoll | Zweck |
|--------|------|------|-----------|-------|
| api-server, celery-beat, celery-primary | `*.postgresql.eu01.onstackit.cloud` | 5432 | TCP/TLS | Managed PostgreSQL |
| api-server, celery-primary | `object.storage.eu01.onstackit.cloud` | 443 | HTTPS | StackIT S3 |
| api-server, celery-primary | `api.openai-compat.model-serving.eu01.onstackit.cloud` | 443 | HTTPS | LLM API (GPT-OSS, Qwen3) |
| inference-/indexing-model-server | Evtl. externe Embedding API | 443 | HTTPS | Remote Embeddings (nomic) |
| nginx Controller | K8s API (`kubernetes.default.svc`) | 443 | HTTPS | Ingress-Resource-Watch |
| celery-beat | K8s API (`kubernetes.default.svc`) | 443 | HTTPS | Leader Election (Lease) |
| Alle Pods | CoreDNS (`kube-system`) | 53 + 8053 | UDP+TCP | DNS-Aufloesung (Service:53, Pod:8053 nach DNAT) |

### 3.3 Eingehender Traffic (Ingress)

```
Internet → LoadBalancer:80 → nginx Controller:1024 → api-server:8080 / web-server:3000
```

Keine Kubernetes-Ingress-Objekte aktiv (`ingress.enabled: false`). Routing erfolgt ueber Custom nginx ConfigMap.

### 3.4 Cross-Namespace-Kommunikation

**Nicht erforderlich.** Der redis-operator (`default` NS) kommuniziert ausschliesslich ueber die K8s API, nicht per Pod-zu-Pod. Redis-Pods werden im Application-Namespace erstellt.

### 3.5 Reine Empfaenger (kein Egress erforderlich)

- **Vespa:** Empfaengt nur Anfragen auf 8081 + 19071
- **Redis:** Empfaengt nur Anfragen auf 6379

---

## 4. Pod-Labels (verifiziert aus Helm Chart `_helpers.tpl` + Templates)

### 4.1 Label-Schema

Die meisten Onyx-Pods verwenden das Standard-Schema:
```yaml
app.kubernetes.io/name: onyx                  # Chart-Name
app.kubernetes.io/instance: onyx-dev          # Release-Name (onyx-test fuer TEST)
app: <component>                              # Deployment-spezifisch
```

### 4.2 Vollstaendige Label-Tabelle

| Pod | Selector Labels (matchLabels) | Besonderheit |
|-----|-------------------------------|-------------|
| api-server | `app.kubernetes.io/name: onyx`, `app.kubernetes.io/instance: onyx-dev`, `app: api-server` | Standard |
| web-server | `app.kubernetes.io/name: onyx`, `app.kubernetes.io/instance: onyx-dev`, `app: web-server` | Standard |
| celery-beat | `app.kubernetes.io/name: onyx`, `app.kubernetes.io/instance: onyx-dev`, `app: celery-beat` | Standard |
| celery-worker-primary | `app.kubernetes.io/name: onyx`, `app.kubernetes.io/instance: onyx-dev`, `app: celery-worker-primary` | Standard |
| indexing-model-server | `app.kubernetes.io/name: onyx`, `app.kubernetes.io/instance: onyx-dev`, `app: indexing-model-server` | Standard |
| **inference-model-server** | `app: inference-model-server` | **NUR `app`-Label, KEIN `app.kubernetes.io/name`!** Eigenes Key-Value-Template. |
| **vespa** | `app: vespa`, `app.kubernetes.io/instance: onyx`, `app.kubernetes.io/name: vespa` | **Hardcoded Name `da-vespa`, `instance: onyx` (ohne `-dev`)** |
| **redis** | `app: onyx-dev` | **Operator-generiert, Label = Release-Name** |
| **nginx Controller** | `app.kubernetes.io/name: nginx`, `app.kubernetes.io/instance: onyx-dev`, `app.kubernetes.io/component: controller` | **Eigenes Chart (nginx-4.13.3), NICHT `ingress-nginx`!** |

### 4.3 Auswirkung auf NetworkPolicy-Design

Die **inkonsistenten Labels** (inference-model-server, vespa, redis, nginx haben jeweils andere Schemata) machen **per-Pod-Selektoren fehleranfaellig**. Deshalb verwenden wir `podSelector: {}` (Namespace-weit) fuer die meisten Policies.

Der **einzige pod-spezifische Selektor** wird fuer die nginx-Ingress-Policy benoetigt:
```yaml
podSelector:
  matchLabels:
    app.kubernetes.io/name: nginx       # NICHT ingress-nginx!
    app.kubernetes.io/component: controller
```

> **Lesson Learned (2026-03-05):** Das Onyx Helm Chart benennt den nginx-Chart als `nginx` (nicht `ingress-nginx`). Die Pod-Labels werden von `_helpers.tpl` des Sub-Charts generiert — immer mit `kubectl get pod --show-labels` verifizieren, nie aus der Chart-Doku annehmen.

---

## 5. Design-Entscheidungen

### 5.1 Pragmatischer Egress-Ansatz (statt granular)

**Entscheidung:** Alle Pods duerfen Egress auf TCP 443 + 5432. Keine per-Pod-Einschraenkung.

**Begruendung:**

| Kriterium | Granular | Pragmatisch (gewaehlt) |
|-----------|----------|----------------------|
| Sicherheitsgewinn | Marginal (Vespa/Redis initiieren sowieso keinen Egress) | Namespace-Isolation ist Hauptziel — wird gleichwertig erreicht |
| Label-Abhaengigkeit | Erfordert korrekte Pod-Selektoren (fragil bei inkonsistenten Labels) | `podSelector: {}` — robust gegen Chart-Updates |
| Wartbarkeit | 7-8 Policies pro Namespace | 5 Policies pro Namespace |
| PROD-Upgrade | Muss fuer PROD sowieso angepasst werden | Gleicher Aufwand, saubere Basis |
| Risiko | Hoeher (eine falsche Regel bricht Verbindung) | Niedriger (einfacher, weniger Fehlerquellen) |

**Fuer PROD-Haertung:** Granulare per-Pod-Selektoren hinzufuegen, nachdem die Label-Struktur stabilisiert ist.

### 5.2 Kein `ipBlock.except` fuer private Ranges

**Entscheidung:** Externer Egress wird NICHT auf `0.0.0.0/0 except RFC1918` eingeschraenkt.

**Begruendung:**

Der K8s API Server (`kubernetes.default.svc:443`) hat eine **ClusterIP in privaten Ranges** (typisch 10.x.x.x). Wuerde man private Ranges ausschliessen, koennte:

- nginx Controller keine Ingress-Resources watchen → **502-Fehler**
- celery-beat kein Leader-Election durchfuehren → **Task-Scheduling bricht**

**Cross-Namespace-Isolation** wird stattdessen durch **default-deny Ingress auf beiden Namespaces** erreicht. Selbst wenn ein Pod in onyx-dev theoretisch Egress zu onyx-test:443 hat — der Ingress-Deny in onyx-test blockiert die Verbindung.

### 5.3 Namespace-unabhaengige YAML-Dateien

**Entscheidung:** Policies werden OHNE `metadata.namespace` geschrieben. Das Skript uebergibt den Namespace per `-n` Parameter.

**Vorteil:** Keine Duplikation, identische Policies fuer DEV und TEST.

### 5.4 DNS-Egress: Port 53 + 8053 (StackIT/Gardener-spezifisch)

**Entscheidung:** DNS-Egress erlaubt sowohl Port 53 als auch Port 8053, ohne `podSelector`/`namespaceSelector`.

**Begruendung:**

StackIT SKE (Gardener) betreibt CoreDNS auf **Port 8053** (nicht 53). Der kube-dns Service mapped `53 → 8053` per `targetPort`. Da Calico NetworkPolicies **nach DNAT** evaluiert werden, sieht die Policy den tatsaechlichen Ziel-Port (8053), nicht den Service-Port (53).

| Ansatz | Problem |
|--------|---------|
| Nur Port 53 | Blockiert DNS — Calico sieht Port 8053 nach DNAT |
| Port 53 + `namespaceSelector: kube-system` + `podSelector: k8s-app=kube-dns` | Blockiert DNS — ClusterIP wird per DNAT aufgeloest, Port 8053 matcht nicht |
| Port 53 + 8053, ohne Selektor (gewaehlt) | Funktioniert — Port-basierte Filterung, robust gegen CNI-Verhalten |

**Nachweis:**
```
# kube-dns Service: port 53 → targetPort 8053
kubectl get endpoints -n kube-system kube-dns
→ 100.64.1.21:8053, 100.64.1.8:8053

# DNS-Aufloesung verifiziert nach Fix
kubectl exec -n onyx-dev deploy/onyx-dev-api-server -- python3 -c \
  "import socket; print(socket.getaddrinfo('google.com', 443)[0][4])"
→ ('142.250.186.78', 443)
```

---

## 6. Policy-Uebersicht

### 6.1 Zusammenfassung

| # | Datei | policyTypes | podSelector | Zweck |
|---|-------|------------|-------------|-------|
| 01 | `default-deny-all.yaml` | Ingress, Egress | `{}` (alle) | Zero-Trust Baseline |
| 02 | `allow-dns-egress.yaml` | Egress | `{}` (alle) | DNS-Aufloesung (Port 53 + 8053, siehe 5.4) |
| 03 | `allow-intra-namespace.yaml` | Ingress, Egress | `{}` (alle) | Intra-Namespace-Kommunikation |
| 04 | `allow-external-ingress-nginx.yaml` | Ingress | nginx Controller | Externer Traffic → nginx |
| 05 | `allow-external-egress.yaml` | Egress | `{}` (alle) | PG:5432 + HTTPS:443 |

### 6.2 Traffic-Fluss nach Aktivierung

```
ERLAUBT:
  ✅ Internet → nginx → api-server/web-server (via 04 + 03)
  ✅ api-server → redis, vespa, model-server (via 03)
  ✅ celery-* → redis, vespa, model-server, api-server (via 03)
  ✅ Alle Pods → CoreDNS:53/8053 (via 02)
  ✅ Alle Pods → PG:5432, S3/LLM:443 (via 05)
  ✅ Alle Pods → K8s API:443 (via 05)

BLOCKIERT:
  ❌ onyx-dev Pods → onyx-test Pods (und umgekehrt)
  ❌ Egress auf nicht-erlaubte Ports (z.B. TCP 22, 25, 3306)
  ❌ Externer Ingress zu Nicht-nginx-Pods (api-server, redis, vespa nicht direkt erreichbar)
```

---

## 7. Verifikationsplan

### 7.1 Nach Apply (pro Namespace)

| # | Test | Befehl | Erwartung |
|---|------|--------|-----------|
| 1 | Policies vorhanden | `kubectl get networkpolicy -n onyx-dev` | 5 Policies |
| 2 | API Health (intra-NS) | `kubectl exec -n onyx-dev deploy/onyx-dev-api-server -- python3 -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8080/health'); print(r.status)"` | `200` |
| 3 | Cross-NS blockiert | `kubectl exec -n onyx-dev deploy/onyx-dev-api-server -- python3 -c "import urllib.request; urllib.request.urlopen('http://onyx-test-api-server.onyx-test:8080/health', timeout=3)"` | Timeout (blockiert) |
| 4 | DNS funktioniert | `kubectl exec -n onyx-dev deploy/onyx-dev-api-server -- python3 -c "import socket; print(socket.getaddrinfo('google.com', 443)[0][4])"` | IP-Adresse aufgeloest |
| 5 | Intra-NS via nginx | `kubectl run test-curl --image=curlimages/curl --rm -it --restart=Never -n onyx-dev -- curl -s -o /dev/null -w '%{http_code}' http://onyx-dev-nginx-controller/health` | `200` oder `307` |
| 6 | LoadBalancer | `curl -sf http://188.34.74.187/health` | `307` (Redirect zu Login) |

> **Hinweis:** Die Onyx-Container enthalten weder `curl` noch `nslookup`. Fuer In-Pod-Tests `python3` verwenden. Fuer Cluster-interne HTTP-Tests: temporaeren `curlimages/curl`-Pod starten. Der Health-Endpoint ist `/health` (nicht `/api/health`).

### 7.2 Rollback-Kriterien

Sofortiger Rollback wenn:
- LoadBalancer-Health-Check fehlschlaegt (> 30 Sekunden)
- API Server nicht erreichbar
- Pods in CrashLoopBackOff

---

## 8. Risiken und Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| DNS-Egress vergessen → alles bricht | Eliminiert (Policy 02) | CRITICAL | DNS-Policy wird VOR default-deny applied |
| nginx-Ingress blockiert → 502 | Eliminiert (Policy 04) | CRITICAL | Dedizierte nginx-Ingress-Policy |
| Vespa:19071 vergessen → Schema-Deploy bricht | Eliminiert (Policy 03) | HIGH | Intra-NS erlaubt alle Ports |
| K8s API blockiert → nginx/celery bricht | Eliminiert (Policy 05) | HIGH | Port 443 Egress erlaubt K8s API |
| Helm Upgrade aendert Labels | Niedrig | MEDIUM | `podSelector: {}` ist label-unabhaengig |
| PROD braucht granularere Policies | Sicher | LOW | Geplant fuer PROD-Haertung (SEC-06) |

---

## 9. Quellen

- StackIT: [How to enhance the security of your SKE cluster](https://docs.stackit.cloud/stackit/en/how-to-enhance-the-security-of-your-ske-cluster-328565447.html)
- StackIT: [SKE Networking](https://docs.stackit.cloud/products/runtime/kubernetes-engine/basics/networking/)
- Gardener: [Calico CNI Extension](https://gardener.cloud/docs/extensions/network-extensions/gardener-extension-networking-calico/)
- Kubernetes: [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- Calico: [Default Deny Policy](https://docs.tigera.io/calico/latest/network-policy/get-started/kubernetes-default-deny)
- BSI: IT-Grundschutz NET.1.1 (Netzsegmentierung)
- ISO 27002: Control 8.31 (Trennung von Entwicklungs-, Test- und Produktionsumgebungen)

---

## 10. Aenderungshistorie

| Datum | Aenderung | Autor |
|-------|----------|-------|
| 2026-03-05 | Erstanalyse, Traffic-Matrix, Design-Entscheidungen | Nikolaj Ivanov (CCJ) |
| 2026-03-05 | Fix: nginx-Label `ingress-nginx` → `nginx` (Policy 04), DNS-Port 8053 hinzugefuegt (Policy 02), Abschnitt 5.4 ergaenzt, DEV applied | Nikolaj Ivanov (CCJ) |
