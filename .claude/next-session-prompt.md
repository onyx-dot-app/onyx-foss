# Nächste Session — Post-Audit + Post-Upstream-Merge

## Wo wir stehen (2026-03-03)

**DEV + TEST LIVE, Upstream gemerged (415 Commits), Doku-Audit komplett.**

## Was heute erledigt wurde (Session 2026-03-03)

1. ✅ values-test.yaml committed + gepusht
2. ✅ CI/CD workflow_dispatch TEST — grün
3. ✅ LLM in TEST konfiguriert (GPT-OSS 120B + Qwen3-VL 235B)
4. ✅ Enterprise-Doku-Audit durchgeführt (4 kritische, 7 wichtige Findings)
5. ✅ Betriebskonzept komplett überarbeitet (Node.js → Python/FastAPI)
6. ✅ Sicherheitskonzept komplett überarbeitet (SEC-01–07, Secrets, Auth)
7. ✅ Meilensteinplan komplett überarbeitet (M1 an DEV/TEST-Realität)
8. ✅ Testkonzept überarbeitet (JS/Jest → Python/pytest)
9. ✅ ADR-001, ADR-003, ADR-004, README, CHANGELOG, Implementierungsplan, Infrastruktur-Referenz gefixt
10. ✅ DNS/TLS-Runbook erstellt (docs/runbooks/dns-tls-setup.md)
11. ✅ Abnahmeprotokoll-Template Links repariert
12. ✅ Upstream-Merge: 415 Commits, 4 triviale Konflikte, 0 Core-Konflikte
13. ✅ CI/CD Fix: Helm Repo python-sandbox ergänzt
14. ✅ DEV Deploy nach Merge: grün (Smoke Test + Verify OK)
15. ✅ Fork-Management Doku komplett überarbeitet (8-Schritte-Anleitung)
16. ✅ Core-Patches aktualisiert (main.py.original + .patch)
17. ✅ entra-id-kundenfragen.md + terraform.lock.hcl committed

## Commits heute (6 Stück, chronologisch)

1. `c62d47b54` — chore(stackit-infra): TEST-Umgebung live — PG-Host, Domain, IngressClass
2. `600e192d6` — docs(audit): Enterprise-Dokumentation überarbeiten — Faktencheck + Korrekturen
3. `c599fe3db` — docs(audit): Testkonzept, ADRs, DNS/TLS-Runbook, Abnahme-Links korrigieren
4. `a35f54978` — chore(upstream): Merge upstream/main — 415 Commits, 4 triviale Konflikte (Merge-Commit)
5. `5a54be1f8` — fix(ci): Helm Repo python-sandbox hinzufügen (Upstream-Dependency nach Merge)
6. `9f63308e1` — docs(upstream): Fork-Management aktualisieren + untracked Files aufräumen

## Nächste Schritte

### Sofort machbar (keine Blocker)
1. **Embedding-Modell** (E5 Mistral 7B) in DEV + TEST konfigurieren — Browser, Admin UI, Modellname: `intfloat/e5-mistral-7b-instruct`
2. **M1-Abnahmeprotokoll** ausfüllen (Template steht, DEV+TEST-Ergebnisse eintragen)
3. **SEC-02: Node Affinity** — `nodeSelector` in Helm Values
4. **SEC-03: NetworkPolicies** — Namespace-Isolation
5. **SEC-04: Terraform Remote State** — von lokal auf Remote
6. **K8s Upgrade** — 1.32.12 deprecated → 1.33+

### Wartet auf Kunde/Externe
7. **DNS** — Domains mit VÖB klären (Runbook steht bereit: docs/runbooks/dns-tls-setup.md)
8. **TLS/HTTPS** — cert-manager + Helm Values (nach DNS)
9. **Entra ID (Phase 3)** — VÖB IT liefert Zugangsdaten

### Noch offene Doku
10. **DSGVO-Dokumente** (DSFA, AVV) — juristische Abstimmung mit VÖB
11. **Monitoring-Konzept** — vor PROD
12. **Notfall-/Notbetriebsplan** — vor PROD

## Wichtige Details

### Upstream-Merge Erkenntnisse
- Fork-Architektur "Extend, don't modify" validiert
- Neue Helm-Dependencies nach Merge prüfen (python-sandbox war der Fall)
- Core-Patches nach jedem Merge aktualisieren
- DEV zuerst deployen, dann TEST

### LLM Modellnamen (für Admin UI)
- Chat: `openai/gpt-oss-120b` (Provider: `openai`)
- Vision: `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8`
- Embedding: `intfloat/e5-mistral-7b-instruct`
- API Base: `https://api.openai-compat.model-serving.eu01.onstackit.cloud/v1`

### LoadBalancer IPs (stabil, nicht reserviert)
- DEV: `188.34.74.187`
- TEST: `188.34.118.201`
- Stabil solange Ingress Controller Services existieren
- Für DNS: A-Records direkt darauf setzen (DEV/TEST ausreichend)
