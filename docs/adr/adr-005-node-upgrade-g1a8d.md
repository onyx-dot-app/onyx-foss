# ADR-005: Node-Upgrade g1a.4d → g1a.8d

**Status**: Akzeptiert
**Datum**: 2026-03-06
**Entscheider**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Bezug**: ADR-004 (Umgebungstrennung), Upstream PR #9014 (Lightweight Mode entfernt)

---

## Kontext

Upstream Onyx hat mit PR #9014 den Lightweight Background Worker Mode entfernt. Statt eines konsolidierten Workers werden jetzt 8 separate Celery-Deployments benoetigt:

1. celery-beat (Scheduler)
2. celery-worker-primary (Koordination)
3. celery-worker-light (Vespa-Ops, Permissions)
4. celery-worker-heavy (Pruning)
5. celery-worker-docfetching (Connector-Daten)
6. celery-worker-docprocessing (Indexing Pipeline)
7. celery-worker-monitoring (Health, Metrics)
8. celery-worker-user-file-processing (User-Uploads)

Mit dem bisherigen g1a.4d Node-Typ (4 vCPU, 16 GB RAM, 50 GB Disk) reichen die Ressourcen nicht fuer 16 Pods (DEV) bzw. 15 Pods (TEST) pro Environment.

## Entscheidung

**Upgrade von g1a.4d auf g1a.8d** (8 vCPU, 32 GB RAM, 100 GB Disk) fuer den bestehenden Node Pool `devtest` (2 Nodes).

## Alternativen

| Alternative | vCPU | RAM | Nodes | Gesamt CPU | Gesamt RAM | Kosten/Mo |
|-------------|------|-----|-------|-----------|-----------|-----------|
| **A: 2x g1a.4d (Status quo)** | 4 | 16 GB | 2 | ~7 CPU | ~31 GB | ~426 EUR |
| **B: 3x g1a.4d** | 4 | 16 GB | 3 | ~10.5 CPU | ~46 GB | ~568 EUR |
| **C: 2x g1a.8d (gewaehlt)** | 8 | 32 GB | 2 | ~15.8 CPU | ~56.6 GB | ~868 EUR |

## Begruendung

- **Alternative A** scheidet aus: Nicht genug CPU/RAM fuer 8 Celery-Worker pro Environment
- **Alternative B** waere moeglich, aber: 3 Nodes = hoehere Management-Komplexitaet, Node-Affinity-Probleme (welcher Pod auf welchem Node?), kein klarer Vorteil gegenueber C
- **Alternative C** gewaehlt:
  - Einfachste Loesung: 1 Node pro Environment, klare Zuordnung
  - CPU-Auslastung nach Upgrade: ~5% (813m/15.820m) — massig Headroom
  - RAM-Auslastung nach Upgrade: ~28% (16.345 Mi/56.6 Gi)
  - PROD-Sizing: 2x g1a.8d reicht fuer ~150 gleichzeitige User (~40% CPU, ~25% RAM)
  - Disk: 100 GB loest FreeDiskSpaceFailed-Warning (vorher 50 GB)

## Kosten-Impact

| Umgebung | Vorher (g1a.4d) | Nachher (g1a.8d) | Delta |
|----------|-----------------|-------------------|-------|
| DEV+TEST | ~426 EUR/Mo | ~868 EUR/Mo | +442 EUR/Mo |
| PROD (geplant) | ~426 EUR/Mo | ~964 EUR/Mo | +538 EUR/Mo |

## Umsetzung

- Terraform: `deployment/terraform/environments/dev/main.tf` → `machine_type = "g1a.8d"`, `volume_size = 100`
- Terraform apply: 10m11s, 0 added, 1 changed, 0 destroyed
- Helm: 8 Celery-Worker in values-dev.yaml und values-test.yaml aktiviert
- Verifiziert: DEV 16/16 Pods Running, TEST 15/15 Pods Running, 0 Restarts, Health OK

## Konsequenzen

- K8s v1.32.12 ist laut StackIT deprecated — Update auf v1.33+ einplanen
- Recreate-Strategie (kubectl patch) moeglicherweise nicht mehr noetig (genug CPU fuer RollingUpdate)
- PROD-Sizing steht fest: 2x g1a.8d (eigener Cluster, ADR-004)
