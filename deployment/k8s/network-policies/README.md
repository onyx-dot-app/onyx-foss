# NetworkPolicies — VoeB Chatbot (C5/SEC-03)

## Uebersicht

5 Kubernetes NetworkPolicies zur Namespace-Isolation und Least-Privilege-Netzwerkkontrolle.

| Datei | Zweck |
|-------|-------|
| `01-default-deny-all.yaml` | Zero-Trust Baseline (kein Traffic erlaubt) |
| `02-allow-dns-egress.yaml` | DNS-Aufloesung via CoreDNS |
| `03-allow-intra-namespace.yaml` | Pod-zu-Pod innerhalb des Namespace |
| `04-allow-external-ingress-nginx.yaml` | LoadBalancer → nginx Controller |
| `05-allow-external-egress.yaml` | PostgreSQL (5432) + HTTPS (443) |

## Anwendung

```bash
# DEV
./apply.sh onyx-dev

# TEST
./apply.sh onyx-test
```

## Rollback (Notfall)

```bash
./rollback.sh onyx-dev
```

Loescht alle Policies → Kubernetes-Default "allow-all".

## Voraussetzungen

- `kubectl` konfiguriert mit Cluster-Zugang
- Calico CNI (auf StackIT SKE vorinstalliert)
- Namespaces `onyx-dev` / `onyx-test` existieren

## Detaillierte Dokumentation

Vollstaendige Analyse mit Traffic-Matrix, Label-Tabelle, Design-Entscheidungen:
→ `docs/audit/networkpolicy-analyse.md`
