# StackIT Infrastruktur — Technische Referenz

**Stand**: März 2026
**Region**: EU01 (Frankfurt)
**Provider**: StackIT (Deutsche Telekom)

> Dieses Dokument enthält ausschließlich technische Spezifikationen.
> Preise und Kostenschätzungen liegen in separaten Dokumenten (nicht im Repository).

---

## Cluster-Architektur

### Kubernetes (SKE — STACKIT Kubernetes Engine)

| Parameter | Wert |
|-----------|------|
| Cluster | 1 (shared für alle Environments) |
| Kubernetes-Version | v1.32.12 (SKE-zugewiesen) |
| Namespaces | `onyx-dev`, `onyx-test`, `onyx-prod` |
| Ingress Controller | NGINX via Essential Network Load Balancer (NLB-10) |
| TLS | Let's Encrypt oder StackIT-bereitgestellt |
| Network Policies | Noch nicht implementiert (SEC-03, P1 vor PROD). Geplant: Namespace-isoliert; PROD zusätzlich Egress-Rules |

### Worker Nodes (Compute Engine g1a-Serie, AMD, kein Overprovisioning)

| Environment | Node-Typ | vCPU | RAM | Anzahl | Pool |
|-------------|----------|------|-----|--------|------|
| DEV + TEST | g1a.4d | 4 | 16 GB | 2 (1 pro Env) | `devtest` |
| PROD (dedicated) | g1a.4d | 4 | 16 GB | 2 (bei Bedarf 3) | eigener Cluster |

**DEV+TEST allokierbare Kapazität (2× g1a.4d):** ~7 CPU / ~31 GB RAM — je ~3.5 CPU / ~15 GB pro Env
**PROD allokierbare Kapazität (2× g1a.4d):** ~7 CPU / ~31 GB RAM
**PROD geschätzte Auslastung:** CPU ~70–80%, RAM ausreichend

> **Entscheidung (ADR-004):** Eigene Nodes pro Umgebung statt geteilter Node.
> Begründung: CPU-Isolation, Ausfallsicherheit, Enterprise-Standard.

---

## PostgreSQL (Flex — Managed Database)

| Environment | Konfiguration | vCPU | RAM | HA |
|-------------|---------------|------|-----|-----|
| DEV | Flex 2.4 Single | 2 | 4 GB | Nein |
| TEST | Flex 2.4 Single | 2 | 4 GB | Nein |
| PROD | Flex 4.8 Replica | 4 | 8 GB | Ja (3-Node Set) |

**Disk Performance:** Premium Performance Tier 2 (`premium-perf2-stackit`, SSD-level IOPS), 1 Disk pro Node
**Backup:** PostgreSQL PITR (automatisch), Object Storage für Backup-Daten
**PROD-Besonderheit:** 3-Node Replica Set (Primary + 2 Standby) als ein verwaltetes Set

**Managed PG Einschränkungen:**
- Kein `CREATEROLE` / `SUPERUSER` für App-User
- User-Verwaltung ausschließlich über StackIT API (Terraform)
- Datenbank muss manuell angelegt werden (Terraform erstellt nur Instanz + User)
- Details: [PostgreSQL Runbook](../runbooks/stackit-postgresql.md)

---

## Storage

| Typ | Zweck | Technologie |
|-----|-------|-------------|
| Object Storage | Dokumente, Uploads, Connector-Daten, Backups | S3-kompatibel |
| Block Storage SSD | K8s PersistentVolumeClaims, Vespa-Indizes | Capacity-Klasse |

**Buckets (Object Storage):** `vob-dev`, `vob-test`, `vob-prod`
**PROD Backups:** PG PITR + Object Store Versioning

---

## Netzwerk

| Komponente | Spezifikation |
|------------|---------------|
| Load Balancer | Essential Network Load Balancer (NLB-10) |
| Public IP | 1× IPv4 (Floating IP für Ingress) |
| Egress/Traffic | Derzeit nicht separat bepreist bei StackIT |
| DNS | Nicht enthalten — über bestehende Client-Infrastruktur |

---

## LLM / AI Model Serving (StackIT-hosted)

| Modell | StackIT Model ID | Verwendung | Status |
|--------|------------------|------------|--------|
| GPT-OSS 120B | `openai/gpt-oss-120b` | Chat-Antworten (primär) | ✅ Verifiziert (DEV) |
| Qwen3-VL 235B | `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8` | Chat + Vision/OCR | ✅ Verifiziert (DEV) |
| E5 Mistral 7B | `intfloat/e5-mistral-7b-instruct` | Embedding / Vektor-Suche | ⏳ Geplant |

**Weitere verfuegbare Modelle (Fallback):** Llama 3.3 70B, Gemma 3 27B, Mistral-Nemo 12B, Llama 3.1 8B

**Wichtig:** LLM laeuft auf StackIT AI Model Serving (OpenAI-kompatible API, vLLM-Backend) — kein OpenAI, keine Daten verlassen Deutschland.

---

## PROD Sizing Detail (80–100 gleichzeitige Nutzer)

### Onyx-Komponenten Resource Requests

| Komponente | CPU Request | RAM Request | Replicas |
|------------|------------|-------------|----------|
| Backend API (FastAPI) | 500m | 512 Mi | 2–3 |
| Frontend (Next.js) | 250m | 256 Mi | 2 |
| Background Worker (Celery) | 500m | 1 Gi | 2 |
| Redis | 250m | 512 Mi | 1 |
| Vespa (Vektor-Suche) | 2000m | 4 Gi | 1 |
| System-Overhead (kube-system) | 500m | 512 Mi | — |
| **TOTAL PROD** | **~5–7 CPU** | **~7–10 Gi** | — |

### Skalierung

- 2× g1a.4d Worker Nodes decken den erwarteten Bedarf
- Bei Lastspitzen: 3. Node hinzufügen (HPA-ready)
- Vespa als In-Cluster Deployment (PROD: 1–2 Replicas)
- Redis als In-Cluster Pod (kein Managed Redis notwendig)

---

## Environments-Übersicht

| Aspekt | DEV | TEST | PROD |
|--------|-----|------|------|
| Namespace | `onyx-dev` | `onyx-test` | `onyx-prod` |
| Cluster | shared (`vob-chatbot`) | shared (`vob-chatbot`) | **eigener Cluster** (ADR-004) |
| Worker Nodes | eigener Node (g1a.4d) | eigener Node (g1a.4d) | 2× g1a.4d dedicated |
| PostgreSQL | Flex 2.4 Single (`vob-dev`) | Flex 2.4 Single (`vob-test`) | Flex 4.8 Replica (3 Nodes HA) |
| Object Storage | `vob-dev` | `vob-test` | `vob-prod` |
| Vespa | In-Cluster (1 Replica) | In-Cluster (1 Replica) | In-Cluster (1–2 Replicas) |
| Redis | In-Cluster Pod | In-Cluster Pod | In-Cluster Pod |
| LLM | StackIT AI Serving | gleich | gleich + Monitoring |
| Backups | PG PITR (auto) | PG PITR (auto) | PG PITR + ObjStore Versioning |
| Resource Quotas | Entfernt (DEV) | Entfernt (TEST) | CPU: 8, RAM: 24 GB |
| Network Policy | Noch nicht implementiert (SEC-03) | Noch nicht implementiert (SEC-03) | Geplant: Namespace-isoliert + Egress-Rules |

---

## Token-Kalkulation (Sizing-Annahmen)

| Parameter | DEV | Erwartet (80 User) | Peak (100 User) |
|-----------|-----|---------------------|------------------|
| Aktive Nutzer/Tag | 5 | 80 | 100 |
| Queries/Nutzer/Tag | 5 | 10 | 15 |
| Arbeitstage/Monat | 22 | 22 | 22 |
| Ø Input-Tokens/Query | 3.000 | 4.000 | 5.000 |
| Ø Output-Tokens/Query | 500 | 750 | 1.000 |
| **Queries/Monat** | 550 | 17.600 | 33.000 |
| **Input-Tokens/Monat** | 1,65 Mio | 70,4 Mio | 165 Mio |
| **Output-Tokens/Monat** | 0,28 Mio | 13,2 Mio | 33 Mio |

---

## Nicht enthalten (optional hinzubuchbar)

- **Observability/Logging:** StackIT LogMe (ab ~274 EUR/Monat) — Alternative: Self-hosted Prometheus/Grafana/ELK auf Cluster
- **DNS-Zone:** 1,92 EUR/Monat — ggf. über bestehende VÖB-Infrastruktur
- **WAF/DDoS:** Abhängig von StackIT-Angebot

---

## Quellen

- StackIT Pricing API (`pim.api.stackit.cloud`), Stand Februar 2026
- Kostenaufstellung und Architecture Sizing: Coffee Studios (intern, nicht im Repository)
