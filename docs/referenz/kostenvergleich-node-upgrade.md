# Kostenvergleich: Node-Upgrade — VoeB Service Chatbot

**Stand:** 2026-03-05
**Erstellt von:** Nikolaj Ivanov (CCJ / Coffee Studios)
**Anlass:** Upstream-Aenderung (Onyx PR #9014) erfordert 6 zusaetzliche Worker-Pods pro Environment

---

## 1. Zusammenfassung


|                          | IST (monatlich) | SOLL (monatlich) | Differenz        |
| ------------------------ | --------------- | ---------------- | ---------------- |
| **DEV + TEST**           | 585,29 EUR      | 868,47 EUR       | **+283,18 EUR**  |
| **PROD (geplant)**       | —               | 963,96 EUR       | —                |
| **GESAMT (alle 3 Envs)** | —               | **1.832,43 EUR** | —                |


**Einzige Aenderung:** Worker Nodes von g1a.4d (4 vCPU, 16 GB) auf g1a.8d (8 vCPU, 32 GB).
Alle anderen Services bleiben unveraendert.

---

## 2. IST-Zustand — DEV + TEST (aktuell in Betrieb)

### 2.1 Infrastruktur-Services


| #   | Service                    | Beschreibung                           | Anzahl | EUR/Stunde | EUR/Monat (je) | EUR/Monat (gesamt) | Quelle      |
| --- | -------------------------- | -------------------------------------- | ------ | ---------- | -------------- | ------------------ | ----------- |
| 1   | SKE Cluster                | Cluster `vob-chatbot` (Management Fee) | 1      | 0,09960    | 71,71          | 71,71              | VERIFIZIERT |
| 2   | Worker Node g1a.4d         | 4 vCPU / 16 GB RAM / AMD EPYC          | 2      | 0,19665    | 141,59         | 283,18             | VERIFIZIERT |
| 3   | PostgreSQL Flex 2.4 Single | 2 CPU / 4 GB RAM / 20 GB SSD           | 2      | —          | 105,54         | 211,08             | VERIFIZIERT |
| 4   | Object Storage             | Bucket `vob-dev` + `vob-test`          | 2      | —          | 0,27           | 0,54               | VERIFIZIERT |
| 5   | Load Balancer Essential-10 | DEV Ingress (nginx)                    | 1      | 0,01304    | 9,39           | 9,39               | VERIFIZIERT |
| 6   | Load Balancer Essential-10 | TEST Ingress (nginx-test)              | 1      | 0,01304    | 9,39           | 9,39               | VERIFIZIERT |
|     |                            |                                        |        |            | **GESAMT IST** | **585,29**         |             |


### 2.2 Pods pro Environment (IST)


| Pod                      | DEV    | TEST  | Funktion                                 |
| ------------------------ | ------ | ----- | ---------------------------------------- |
| API Server               | 1      | 1     | Backend REST API                         |
| Web Server               | 1      | 1     | Next.js Frontend                         |
| Celery Beat              | 1      | 1     | Task Scheduler                           |
| Celery Worker Primary    | 1      | 1     | Konsolidierter Worker (Lightweight Mode) |
| Vespa                    | 1      | 1     | Vektor-Datenbank                         |
| Redis                    | 1      | 1     | Cache / Message Broker                   |
| Model Server Inference   | 1      | 1     | LLM-Anfragen                             |
| Model Server Indexing    | 1      | 1     | Embedding-Berechnung                     |
| NGINX Ingress Controller | 1      | 1     | Reverse Proxy / TLS                      |
| Redis Operator           | 1      | —     | Shared im default Namespace              |
| **Gesamt**               | **10** | **9** |                                          |


---

## 3. SOLL-Zustand — DEV + TEST (nach Upstream-Merge + Node-Upgrade)

### 3.1 Infrastruktur-Services


| #   | Service                    | Beschreibung                      | Anzahl | EUR/Stunde  | EUR/Monat (je)  | EUR/Monat (gesamt) | Aenderung    |
| --- | -------------------------- | --------------------------------- | ------ | ----------- | --------------- | ------------------ | ------------ |
| 1   | SKE Cluster                | Cluster `vob-chatbot`             | 1      | 0,09960     | 71,71           | 71,71              | unveraendert |
| 2   | **Worker Node g1a.8d**     | **8 vCPU / 32 GB RAM / AMD EPYC** | 2      | **0,39331** | **283,18**      | **566,36**         | **UPGRADE**  |
| 3   | PostgreSQL Flex 2.4 Single | 2 CPU / 4 GB RAM / 20 GB SSD      | 2      | —           | 105,54          | 211,08             | unveraendert |
| 4   | Object Storage             | Bucket `vob-dev` + `vob-test`     | 2      | —           | 0,27            | 0,54               | unveraendert |
| 5   | Load Balancer Essential-10 | DEV Ingress                       | 1      | 0,01304     | 9,39            | 9,39               | unveraendert |
| 6   | Load Balancer Essential-10 | TEST Ingress                      | 1      | 0,01304     | 9,39            | 9,39               | unveraendert |
|     |                            |                                   |        |             | **GESAMT SOLL** | **868,47**         |              |


### 3.2 Pods pro Environment (SOLL)


| Pod                               | DEV    | TEST   | Funktion                                          | Status         |
| --------------------------------- | ------ | ------ | ------------------------------------------------- | -------------- |
| API Server                        | 1      | 1      | Backend REST API                                  | unveraendert   |
| Web Server                        | 1      | 1      | Next.js Frontend                                  | unveraendert   |
| Celery Beat                       | 1      | 1      | Task Scheduler                                    | unveraendert   |
| Celery Worker Primary             | 1      | 1      | Kern-Tasks, periodische Aufgaben                  | unveraendert   |
| **Celery Worker Light**           | **1**  | **1**  | **Vespa-Sync, Connector-Verwaltung, Permissions** | **NEU**        |
| **Celery Worker Heavy**           | **1**  | **1**  | **Pruning, Gruppen-Sync**                         | **NEU**        |
| **Celery Worker Doc-Fetching**    | **1**  | **1**  | **Dokumente von Datenquellen holen**              | **NEU**        |
| **Celery Worker Doc-Processing**  | **1**  | **1**  | **Chunking, Embedding, Indexierung**              | **NEU**        |
| **Celery Worker Monitoring**      | **1**  | **1**  | **System-Health, Queue-Ueberwachung**             | **NEU**        |
| **Celery Worker User-File-Proc.** | **1**  | **1**  | **Nutzer-Datei-Uploads verarbeiten**              | **NEU**        |
| Vespa                             | 1      | 1      | Vektor-Datenbank                                  | unveraendert   |
| Redis                             | 1      | 1      | Cache / Message Broker                            | unveraendert   |
| Model Server Inference            | 1      | 1      | LLM-Anfragen                                      | unveraendert   |
| Model Server Indexing             | 1      | 1      | Embedding-Berechnung                              | unveraendert   |
| NGINX Ingress Controller          | 1      | 1      | Reverse Proxy / TLS                               | unveraendert   |
| Redis Operator                    | 1      | —      | Shared im default Namespace                       | unveraendert   |
| **Gesamt**                        | **16** | **15** |                                                   | **+6 pro Env** |


---

## 4. PROD-Planung (geplant, noch nicht provisioniert)

PROD bekommt gemaess ADR-004 einen **eigenen SKE-Cluster**.

### 4.1 Infrastruktur-Services PROD


| #   | Service                        | Beschreibung                       | Anzahl | EUR/Monat (je) | EUR/Monat (gesamt) | Quelle      |
| --- | ------------------------------ | ---------------------------------- | ------ | -------------- | ------------------ | ----------- |
| 1   | SKE Cluster                    | Eigener Cluster `vob-chatbot-prod` | 1      | 71,71          | 71,71              | VERIFIZIERT |
| 2   | Worker Node g1a.8d             | 8 vCPU / 32 GB RAM                 | 2      | 283,18         | 566,36             | VERIFIZIERT |
| 3   | PostgreSQL Flex 4.8 Replica    | 4 CPU / 8 GB RAM / HA (3 Nodes)   | 1      | 316,23         | 316,23             | VERIFIZIERT |
| 4   | Object Storage                 | Bucket `vob-prod`                  | 1      | 0,27           | 0,27               | VERIFIZIERT |
| 5   | Load Balancer Essential-10     | PROD Ingress                       | 1      | 9,39           | 9,39               | VERIFIZIERT |
|     |                                |                                    |        | **GESAMT PROD**| **963,96**         |             |


### 4.2 Pods PROD

Identisch zu SOLL DEV/TEST (16 Pods), aber mit:

- Mehrere Replicas fuer API Server (2), Web Server (2)
- Vespa: 1-2 Replicas
- Geschaetzt: **~20 Pods**

---

## 5. Gesamtkosten-Uebersicht

### 5.1 DEV + TEST (bestehender Cluster)


| Position            | IST        | SOLL       | Differenz    |
| ------------------- | ---------- | ---------- | ------------ |
| SKE Cluster         | 71,71      | 71,71      | 0,00         |
| Worker Nodes (2x)   | 283,18     | **566,36** | **+283,18**  |
| PostgreSQL (2x)     | 211,08     | 211,08     | 0,00         |
| Object Storage (2x) | 0,54       | 0,54       | 0,00         |
| Load Balancer (2x)  | 18,78      | 18,78      | 0,00         |
| **GESAMT DEV+TEST** | **585,29** | **868,47** | **+283,18**  |


### 5.2 Alle Environments (nach PROD-Provisionierung)


| Environment | EUR/Monat      |
| ----------- | -------------- |
| DEV + TEST  | 868,47         |
| PROD        | 963,96         |
| **GESAMT**  | **1.832,43**   |


> Alle Preise netto zzgl. MwSt.

---

## 6. Kapazitaetsvergleich


| Metrik                                   | IST (2x g1a.4d) | SOLL (2x g1a.8d) |
| ---------------------------------------- | --------------- | ---------------- |
| vCPU gesamt                              | 8               | 16               |
| RAM gesamt                               | 32 GB           | 64 GB            |
| Allocatable CPU (abzgl. System)          | ~7,0            | ~15,0            |
| Allocatable RAM (abzgl. System)          | ~26 GB          | ~58 GB           |
| CPU-Requests DEV (aktuell 10 Pods)       | ~3,2 (82% Node) | ~3,2 (41% Node)  |
| CPU-Requests DEV (nach Upgrade, 16 Pods) | Reicht nicht    | ~3,7 (47% Node)  |
| Realer CPU-Verbrauch (gemessen, DEV)     | 210m            | 210m             |
| Realer RAM-Verbrauch (gemessen, DEV)     | 4,8 GB          | 4,8 GB           |
| Headroom fuer Lastspitzen                | Keiner          | Ausreichend      |


---

## 7. Begruendung

### Warum ist das Upgrade noetig?

Das Open-Source-Projekt Onyx (Basis unseres Chatbots) hat am 04.03.2026 den "Lightweight Worker Mode"
entfernt (PR #9014). Bisher konnten alle Hintergrundprozesse in einem einzigen Worker-Pod laufen.
Ab dem naechsten Update muessen diese als **6 separate Worker-Pods** betrieben werden.

### Was passiert ohne Upgrade?

Auf den aktuellen g1a.4d Nodes (82% CPU-Scheduling-Auslastung) passen 6 zusaetzliche Pods nicht.
Folgende Funktionen wuerden nach dem Update **nicht mehr arbeiten**:


| Worker               | Funktion                         | Auswirkung bei Fehlen                      |
| -------------------- | -------------------------------- | ------------------------------------------ |
| Light                | Vespa-Sync, Connector-Verwaltung | Suchindex wird nicht aktualisiert          |
| Heavy                | Pruning, Gruppen-Sync            | Geloeschte Dokumente bleiben im Index      |
| Doc-Fetching         | Dokumente von Quellen holen      | Keine neuen Dokumente                      |
| Doc-Processing       | Chunking, Embedding, Indexierung | Geholte Dokumente werden nicht verarbeitet |
| Monitoring           | System-Health, Queues            | Kein Health-Monitoring                     |
| User-File-Processing | Datei-Uploads                    | Nutzer koennen keine Dateien hochladen     |


### Positiver Nebeneffekt

Das gleiche Upstream-Update hebt die Blockade fuer den **Embedding-Modell-Wechsel** auf.
Nach dem Update kann das Embedding von `nomic-embed-text-v1` auf `Qwen3-VL-Embedding 8B`
(StackIT AI Model Serving) umgestellt werden — bessere Suchqualitaet, keine Zusatzkosten.

---

## 8. Umsetzung


| Schritt                                                | Aufwand          | Downtime                           |
| ------------------------------------------------------ | ---------------- | ---------------------------------- |
| Terraform: Node Pool Flavor aendern (g1a.4d -> g1a.8d) | ~5 Min           | ~15-20 Min (Node-Drain + Neustart) |
| Upstream-Merge (57 Commits)                            | ~30 Min          | Keine                              |
| Helm Values anpassen (Worker-Konfiguration)            | ~15 Min          | Keine                              |
| Deploy DEV + Verifikation                              | ~15 Min          | ~5 Min (Recreate-Strategie)        |
| Deploy TEST + Verifikation                             | ~15 Min          | ~5 Min                             |
| Embedding-Modell umstellen (optional, im Anschluss)    | ~10 Min          | Keine (Re-Index im Hintergrund)    |
| **Gesamt**                                             | **~1,5 Stunden** | **~25 Min pro Env**                |


---

## 9. Offene Posten — Preis zu pruefen

Die folgenden Services werden genutzt, sind aber in den obigen Kosten **nicht enthalten**,
da die Preise noch verifiziert werden muessen.

| #   | Service                      | Beschreibung                                            | Betrifft         | Wo pruefen                         |
| --- | ---------------------------- | ------------------------------------------------------- | ---------------- | ---------------------------------- |
| 1   | Block Storage (Vespa PVCs)   | 20 GB PersistentVolumeClaim pro Environment fuer Vespa  | DEV, TEST, PROD  | StackIT Block Storage Preise       |
| 2   | StackIT Container Registry   | Docker Images fuer Backend + Frontend werden dort gespeichert | alle Envs   | StackIT Container Registry Preise  |

> **Hinweis:** PostgreSQL-Backups sind im PG Flex Preis enthalten (Terraform: `backup_schedule = "0 2 * * *"`).
> StackIT AI Model Serving (LLM-Nutzung) ist nutzungsabhaengig und nicht Teil der Infrastruktur-Grundkosten.

---

## 10. Preisquellen


| Quelle                                                                                                         | Status                                                    |
| -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| [StackIT Preisliste](https://stackit.com/en/prices/cloud)                                                      | g1a.4d, g1a.8d, SKE, LB — VERIFIZIERT (2026-03-05)       |
| [StackIT Calculator](https://calculator.stackit.cloud/)                                                        | PG Flex, Object Storage — VERIFIZIERT (2026-03-05)        |
| [StackIT Compute Engine Docs](https://docs.stackit.cloud/products/compute-engine/server/basics/machine-types/) | Machine Type Specs — VERIFIZIERT                          |
| [StackIT SKE Produkt](https://stackit.com/en/products/runtime/stackit-kubernetes-engine)                       | Cluster Management Fee — VERIFIZIERT                      |
| [StackIT Load Balancer](https://stackit.com/en/products/network/stackit-load-balancer)                         | LB Essential-10 Preis — VERIFIZIERT                       |

