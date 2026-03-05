# Naechste Session — Security-Haertung Woche 1 fortsetzen

## Wo wir stehen (2026-03-05, Ende der Session)

### Commits (chronologisch)
1. `27dec3dcf` — 3 Security Quick Wins (C6, H8, H11) deployed auf DEV + TEST
2. `2657712b7` — Doku-Nachtrag (CHANGELOG, Projektstatus, Runbook-Fixes, Next-Session-Prompt)

### Diese Session erstellt (NOCH NICHT COMMITTED)

**1. NetworkPolicies (C5/SEC-03) — komplett erstellt:**
- `docs/audit/networkpolicy-analyse.md` — Vollstaendige Audit-Dokumentation:
  - Calico CNI auf StackIT SKE verifiziert
  - Komplette Traffic-Matrix (Pod-zu-Pod + extern)
  - Pod-Labels aus Helm Chart verifiziert
  - Design-Entscheidungen dokumentiert (pragmatisch, kein ipBlock.except)
  - Verifikationsplan, Risiken, Quellen
- `deployment/k8s/network-policies/` (8 Dateien):
  - `01-default-deny-all.yaml` — Zero-Trust Baseline
  - `02-allow-dns-egress.yaml` — DNS → CoreDNS (kube-system:53)
  - `03-allow-intra-namespace.yaml` — Intra-Namespace (alle Ports)
  - `04-allow-external-ingress-nginx.yaml` — Extern → nginx Controller
  - `05-allow-external-egress.yaml` — PG:5432 + HTTPS:443
  - `apply.sh` — Sichere Apply-Reihenfolge (Allows vor Deny)
  - `rollback.sh` — Notfall: alle Policies loeschen
  - `README.md` — Kurzanleitung

**2. values-prod.yaml Grundgeruest:**
- `deployment/helm/values/values-prod.yaml` — PROD-Template mit TBD-Platzhaltern
  - HA-Replicas (api: 2, web: 2, celery-primary: 2)
  - PROD-Ressource-Limits (2-4x DEV/TEST)
  - Domain: `chatbot.voeb-service.de` (HTTPS)
  - AUTH_TYPE: `oidc` (Entra ID)
  - POSTGRES_HOST: `[TBD]` (Infra nicht provisioniert)
  - Vespa: 50Gi Storage (statt 20Gi)

**3. CI/CD-Fixes:**
- `.github/workflows/stackit-deploy.yml` — PROD Smoke Test hinzugefuegt (18 Attempts, 3 Min)
- `.github/workflows/upstream-check.yml` — SHA-Pinning: `@v4` → `@34e11487...`

---

## NAECHSTE SCHRITTE (Woche 1 fortsetzen)

### Schritt 1: Uncommitted Changes committen
Alle Dateien aus dieser Session committen (nach Nikos Review):

```bash
git add docs/audit/networkpolicy-analyse.md
git add deployment/k8s/network-policies/
git add deployment/helm/values/values-prod.yaml
git add .github/workflows/stackit-deploy.yml
git add .github/workflows/upstream-check.yml
```

Vorgeschlagener Commit:
```
chore(security): NetworkPolicies, values-prod.yaml, CI/CD-Fixes

- C5/SEC-03: 5 NetworkPolicies + Apply/Rollback-Skripte + Audit-Dokumentation
- values-prod.yaml: PROD-Grundgeruest mit TBD-Platzhaltern (HA, Ressourcen, OIDC)
- CI/CD: PROD Smoke Test hinzugefuegt, upstream-check SHA-Pinning
```

### Schritt 2: NetworkPolicies auf DEV anwenden
```bash
cd deployment/k8s/network-policies/
./apply.sh onyx-dev
```
Verifikation: siehe `docs/audit/networkpolicy-analyse.md` Abschnitt 7.

### Schritt 3: NetworkPolicies auf TEST anwenden
```bash
./apply.sh onyx-test
```

### Schritt 4: DNS/TLS Setup (BLOCKER: Cloudflare DNS-only)
Wartet auf Leif (Cloudflare Proxy → DNS-only umstellen).
Pruefung: `dig +short dev.chatbot.voeb-service.de` → nur `188.34.74.187`
Runbook: `docs/runbooks/dns-tls-setup.md`

---

## REFERENZ-DOKUMENTE

| Thema | Datei |
|-------|-------|
| NetworkPolicy-Analyse (Traffic, Labels, Entscheidungen) | `docs/audit/networkpolicy-analyse.md` |
| NetworkPolicy YAMLs + Skripte | `deployment/k8s/network-policies/` |
| Cloud-Infrastruktur-Audit (alle Findings) | `docs/audit/cloud-infrastruktur-audit-2026-03-04.md` |
| DNS/TLS-Runbook (komplett, Schritte 1-6) | `docs/runbooks/dns-tls-setup.md` |
| PROD Helm Values (Grundgeruest) | `deployment/helm/values/values-prod.yaml` |
| CI/CD Pipeline | `.github/workflows/stackit-deploy.yml` |
| Upstream-Check | `.github/workflows/upstream-check.yml` |
| Projektstatus | `.claude/rules/voeb-projekt-status.md` |
| CHANGELOG | `docs/CHANGELOG.md` |
| Implementierungsplan | `docs/referenz/stackit-implementierungsplan.md` |

---

## OFFENE PUNKTE (Woche 1, noch nicht angegangen)

Aus der Tiefenanalyse am Anfang dieser Session (vollstaendige Liste):

### Sofort machbar (keine Blocker)
- DSFA erstellen (C8, Art. 35 DSGVO) — 4-6h
- Loeschkonzept (C9, Art. 17 DSGVO) — 3-4h
- Terraform Remote State (C3/SEC-04) — 2h
- Resource Limits fuer DEV/TEST (M3) — 2h (PROD bereits in values-prod.yaml)
- M1-Abnahmeprotokoll ausfuellen — 1-2h
- CSP-Header (M1) — 1h
- Kubeconfig-Erneuerung planen (H10, laeuft 2026-05-28 ab) — 1h
- Backup-Strategie dokumentieren (M7) — 2h

### Blockiert
- C1: TLS/HTTPS — wartet auf Cloudflare DNS-only (Leif)
- Entra ID — wartet auf TLS + VoeB Credentials (Termin 06.03)
- H1: PG createdb-Rolle — braucht Wartungsfenster
- C4/H5: Container non-root — Upstream-Dockerfiles (READ-ONLY)

---

## Regeln (Erinnerung)
- `--no-verify` nutzen
- NIEMALS Co-Authored-By fuer Claude
- Helm Chart Templates READ-ONLY
- Kein Commit ohne Nikos Freigabe
- Tiefenanalyse → Plan → Besprechung → Ausfuehrung (pro Aufgabe)
