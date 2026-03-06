# Antwort auf Review: Node-Upgrade Kalkulation

**Datum:** 2026-03-05
**Von:** Nikolaj Ivanov (CCJ / Coffee Studios)
**Betreff:** Technische Pruefung der Gegenvorschlaege zum Node-Upgrade

---

## Zusammenfassung

Der Review-Vorschlag, die 6 neuen Worker-Pods durch aggressives Resource-Tuning auf den bestehenden g1a.4d Nodes unterzubringen, ist im Grundgedanken nachvollziehbar. Bei der technischen Pruefung gegen die tatsaechlichen Helm-Chart-Definitionen und Codebase-Fakten zeigen sich jedoch mehrere Fehler, die eine 1:1-Uebernahme des Vorschlags ausschliessen.

---

## 1. Helm-Value-Keys sind falsch

Der Review schlaegt folgende YAML-Struktur vor:

```yaml
celeryWorker:
  light:
    resources: ...
  docFetching:
    resources: ...
```

Die tatsaechlichen Keys im Onyx Helm Chart (`deployment/helm/charts/onyx/values.yaml`) lauten:

```yaml
celery_worker_light:
  resources: ...
celery_worker_docfetching:
  resources: ...
```

Die vorgeschlagene YAML-Struktur wuerde von Helm vollstaendig ignoriert, da die Keys nicht existieren. Es wuerden die Chart-Defaults greifen (500m–4000m CPU), womit die Pods definitiv nicht auf g1a.4d passen.

**Bewertung:** Formaler Fehler, leicht korrigierbar. Aendert nichts an der inhaltlichen Diskussion.

---

## 2. "Die neuen Worker sind leichtgewichtige Hintergrundprozesse"

Der Review stuft alle 6 neuen Worker als leichtgewichtig ein und leitet daraus niedrige Resource-Requests ab.

**Pruefung gegen den Code:**

- **celery_worker_docprocessing** verarbeitet die gesamte Indexierungs-Pipeline: Dokumente in PostgreSQL upserten, Chunks erstellen, Embeddings ueber den Model Server berechnen lassen, Ergebnisse nach Vespa schreiben. Dieser Worker haelt Dokumentdaten im RAM und koordiniert CPU-intensive Operationen. Chart-Default: 500m CPU / 2 GB RAM Request.

- **celery_worker_docfetching** laedt Dokumente aus externen Datenquellen herunter (Confluence, SharePoint, Dateisysteme etc.). Je nach Dokumentgroesse und -anzahl kann der Memory-Bedarf erheblich sein. Chart-Default: 500m CPU / 2 GB RAM Request.

- **celery_worker_light**, **celery_worker_monitoring** und **celery_worker_user_file_processing** sind tatsaechlich leichtgewichtig. Chart-Defaults: 250–500m CPU / 512 Mi RAM.

- **celery_worker_heavy** fuehrt Pruning und Gruppen-Sync durch — moderat ressourcenintensiv.

**Bewertung:** 4 von 6 Workern sind leichtgewichtig. 2 Worker (docProcessing, docFetching) haben begruendet hohe Memory-Anforderungen, die nicht beliebig reduziert werden koennen.

---

## 3. Memory-Vorschlaege bergen OOMKill-Risiko

| Worker | Review-Vorschlag (Limit) | Chart-Default (Request) | Bewertung |
|---|---|---|---|
| docFetching | 512 Mi | 2 GB | OOMKill-Risiko bei groesseren Dokumenten |
| docProcessing | 1 GB | 2 GB | OOMKill-Risiko bei Chunking/Embedding-Batches |
| light | 512 Mi | 512 Mi | Identisch, kein Problem |
| heavy | 1 GB | 512 Mi | Ausreichend |
| monitoring | 256 Mi | 512 Mi | Knapp, aber moeglich |
| userFileProcessing | 512 Mi | 512 Mi | Identisch, kein Problem |

Die Onyx-Upstream-Entwickler haben die Defaults von 2 GB fuer docFetching und docProcessing bewusst gewaehlt. Diese Worker verarbeiten reale Dokumente (PDFs, Office-Dateien, HTML) im Arbeitsspeicher. Ein 128 Mi Memory-Request mit 512 Mi Limit (wie im Review vorgeschlagen) fuehrt bei Produktivdaten mit hoher Wahrscheinlichkeit zu OOMKills.

---

## 4. CPU-Durchschnittsberechnung ist irrefuehrend

Der Review rechnet: 210m gemessener CPU-Gesamtverbrauch / 10 Pods = 21m Durchschnitt pro Pod.

**Problem:** Die 210m wurden im Idle gemessen — ohne aktives Document Processing. Im Lightweight-Modus liefen alle Hintergrundprozesse in einem einzigen Worker-Pod. Es gibt keine Messdaten fuer die separaten Worker unter Last.

Zudem ist der Durchschnitt irrefuehrend: Vespa allein verbraucht real deutlich mehr als die anderen Pods zusammen. Der tatsaechliche CPU-Bedarf der neuen Worker unter Last ist unbekannt und laesst sich nur durch Monitoring nach dem Deploy ermitteln.

---

## 5. Rechnung betrachtet nur 1 Environment auf 1 Node

Der Review rechnet mit einem einzelnen Node (4 vCPU = 4000m, davon ~3300m schedulable) fuer ein Environment.

**Tatsaechliche Situation:**

- 2 Nodes teilen sich DEV + TEST + System-Pods
- DEV: 10 Pods (~2.000m CPU Requests)
- TEST: 9 Pods (~1.900m CPU Requests)
- System (CoreDNS, kube-proxy, Gardener Node-Agent): ~500m
- **Aktuell: ~4.400m von ~6.600m schedulable = 67%**

Nach Hinzufuegen von 12 neuen Worker-Pods (6 pro Environment) mit reduzierten Requests (100m je):

- **Zusaetzlich: ~1.200m**
- **Neu: ~5.600m von ~6.600m = 85%**

Das passt rechnerisch, laesst aber keinen Headroom fuer Lastspitzen, Pod-Restarts oder Node-Drain bei Updates.

---

## 6. Was am Review korrekt ist

- **Grundkonzept stimmt:** Resource Requests bestimmen das Scheduling, nicht der reale Verbrauch. Ueberhoehte Requests verschwenden Scheduling-Kapazitaet.
- **Unsere Requests sind bereits reduziert:** Die values-dev.yaml setzt z.B. Model Server Inference auf 250m statt 2000m (Chart-Default). Das Tuning-Prinzip wenden wir bereits an.
- **Die Verifizierungsmethode ist korrekt:** `kubectl top nodes` und `kubectl describe node` sind die richtigen Werkzeuge.
- **Die Kosteneinsparung ist real:** 283 EUR/Monat bei DEV+TEST, wenn g1a.4d beibehalten wird.

---

## 7. Empfohlenes Vorgehen

Statt sofort auf g1a.8d zu upgraden, kann ein gestufter Ansatz verfolgt werden:

**Schritt 1: Upstream-Merge + Deploy mit reduzierten Requests auf g1a.4d**

Die 6 neuen Worker mit angepassten, aber realistischen Requests deployen:

```yaml
celery_worker_light:
  replicaCount: 1
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits: { cpu: 500m, memory: 1Gi }

celery_worker_heavy:
  replicaCount: 1
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits: { cpu: 500m, memory: 1Gi }

celery_worker_docfetching:
  replicaCount: 1
  resources:
    requests: { cpu: 100m, memory: 512Mi }
    limits: { cpu: 500m, memory: 4Gi }

celery_worker_docprocessing:
  replicaCount: 1
  resources:
    requests: { cpu: 100m, memory: 512Mi }
    limits: { cpu: 500m, memory: 4Gi }

celery_worker_monitoring:
  replicaCount: 1
  resources:
    requests: { cpu: 50m, memory: 128Mi }
    limits: { cpu: 250m, memory: 512Mi }

celery_worker_user_file_processing:
  replicaCount: 1
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits: { cpu: 500m, memory: 1Gi }
```

Wichtiger Unterschied zum Review: docFetching und docProcessing bekommen 512 Mi Request und 4 Gi Limit (statt 128 Mi / 512 Mi), um OOMKills bei realen Dokumenten zu vermeiden.

**Schritt 2: Monitoring nach Deploy**

```bash
kubectl top nodes
kubectl describe node <node-name> | grep -A 10 "Allocated resources"
kubectl top pods -n onyx-dev --sort-by=memory
```

**Schritt 3: Entscheidung auf Basis realer Daten**

- Scheduling-Auslastung unter 85% und keine OOMKills → g1a.4d beibehalten
- OOMKills, Scheduling-Fehler oder unzureichender Headroom → Upgrade auf g1a.8d

---

## 8. Fazit

Der Node-Upgrade auf g1a.8d ist **nicht zwingend sofort noetig**, sofern die neuen Worker mit realistisch reduzierten Resource Requests deployed werden. Der Review hat in der Grundidee recht — die Umsetzungsdetails (falsche Helm-Keys, zu niedrige Memory-Limits, Rechenfehler bei der Node-Kapazitaet) muessen jedoch korrigiert werden.

Die empfohlene Strategie ist: zuerst mit optimierten Requests auf g1a.4d deployen, per Monitoring verifizieren, und nur bei nachgewiesenem Bedarf upgraden. Das spart 283 EUR/Monat, solange die Auslastung es zulaesst.
