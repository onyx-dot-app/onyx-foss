# VÖB Chatbot — Projektstatus

## Projekt
- **Auftraggeber:** VÖB (Bundesverband Öffentlicher Banken Deutschlands)
- **Auftragnehmer:** CCJ / Coffee Studios (Tech Lead: Nikolaj Ivanov)
- **Cloud:** StackIT (Kubernetes, Datensouveränität, Region EU01 Frankfurt)
- **Auth:** Microsoft Entra ID (OIDC)
- **Basis:** Fork von Onyx FOSS (MIT) mit Custom Extension Layer

## Tech Stack (zusätzlich zu Onyx)
- IaC: Terraform (`deployment/terraform/`) — StackIT Provider ~> 0.80
- Helm: Value-Overlays (`deployment/helm/values/`) — Onyx Chart READ-ONLY
- CI/CD: `.github/workflows/stackit-deploy.yml` (Build → StackIT Registry → Helm Deploy)
- CI: `upstream-check.yml` (wöchentlicher Merge-Kompatibilitäts-Check)
- CI: `.github/workflows/pr-checks.yml` (PR-Validierung: Helm + Docker Build)
- Docker: `deployment/docker_compose/` (.env mit EXT_-Feature Flags)
- Enterprise-Docs: `docs/` (Sicherheitskonzept, Testkonzept, Betriebskonzept, ADRs, Abnahme)

## Aktueller Status

- **Phase 0-1.5:** ✅ Grundlagen, Dev Environment, Dokumentation
- **Phase 2 (Cloud / M1 Infrastruktur):** ✅ **DEV LIVE** (2026-02-27)
  - ✅ StackIT-Zugang, CLI, Service Account, Container Registry
  - ✅ Terraform apply: SKE (g1a.8d, upgraded 2026-03-06 ADR-005), PG Flex, Object Storage
  - ✅ K8s Namespace `onyx-dev` + Image Pull Secret + Redis Operator
  - ✅ PostgreSQL: DB `onyx` angelegt, `db_readonly_user` per Terraform
  - ✅ Object Storage: Credentials erstellt, in Helm Secrets konfiguriert
  - ✅ Helm Release `onyx-dev`: Alle 16 Pods (8 Celery-Worker, Standard Mode) 1/1 Running
  - ✅ API Health OK, Login funktioniert unter `http://188.34.74.187`
  - ✅ Runbooks: stackit-projekt-setup.md, stackit-postgresql.md, helm-deploy.md
  - ✅ CI/CD Pipeline: Produktionsreif (2026-03-02) — Parallel-Build ~8 Min, SHA-gepinnte Actions, Smoke Tests, Concurrency
  - ✅ Upstream-Workflows: 21 Onyx-Workflows deaktiviert, nur StackIT Deploy + Upstream Check aktiv
  - ✅ CI/CD Run #5 (ea70a11): 10 Min, alle 10 Pods Running (historisch, jetzt 16 Pods), Health Check OK
  - ✅ EE-Crash gelöst: `LICENSE_ENFORCEMENT_ENABLED: "false"` in values-common.yaml
  - ✅ DNS: A-Records gesetzt (2026-03-05): `dev.chatbot.voeb-service.de` → `188.34.74.187`, `test.chatbot.voeb-service.de` → `188.34.118.201`
  - ✅ DNS: Cloudflare Proxy auf DNS-only umgestellt und verifiziert (2026-03-05)
  - ⏳ TLS/HTTPS: Blockiert — DNS-Architektur (voeb-service.de bei GlobVill, nicht Cloudflare). Leif muss 2 ACME-Challenge CNAMEs bei GlobVill setzen. Token-Fix erledigt, ClusterIssuers READY. HTTP-01 nicht moeglich (Onyx Chart containerPort 1024). Details: docs/runbooks/dns-tls-setup.md
  - ✅ LLM: GPT-OSS 120B + Qwen3-VL 235B via StackIT AI Model Serving (2026-02-27)
  - ✅ LLM: Embedding-Blocker aufgehoben (Upstream PR #9005 — Search Settings Swap re-enabled). nomic-embed-text-v1 noch aktiv, Wechsel auf Qwen3-VL-Embedding 8B jetzt moeglich ueber Admin-UI.
  - 📋 Scope: DEV live, TEST live.
- **Phase 2 TEST:** ✅ **TEST LIVE** (2026-03-03)
  - ✅ SEC-01: PG ACL eingeschränkt (188.34.93.194/32 + Admin)
  - ✅ Node Pool auf 2 Nodes skaliert (DEV + TEST)
  - ✅ Terraform apply TEST: PG Flex `vob-test` + Bucket `vob-test`
  - ✅ Namespace `onyx-test` + Image Pull Secret + DB `onyx` angelegt
  - ✅ GitHub Environment `test` + 5 Secrets (PG, Redis, S3)
  - ✅ Helm Release `onyx-test`: 15 Pods Running (8 Celery-Worker, Standard Mode) (+ redis-operator im default NS), Health Check OK
  - ✅ TEST erreichbar unter `http://188.34.118.201`
  - ✅ Eigene IngressClass `nginx-test` (Conflict mit DEV vermieden)
  - ✅ values-test.yaml Commit + Push (2026-03-03)
  - ✅ CI/CD workflow_dispatch TEST verifiziert — Build + Deploy grün (2026-03-03)
  - ✅ LLM: GPT-OSS 120B + Qwen3-VL 235B in TEST konfiguriert (2026-03-03)
  - ✅ Enterprise-Dokumentation überarbeitet: Betriebskonzept, Sicherheitskonzept, Meilensteinplan, ADR-004, README, CHANGELOG (2026-03-03)
  - ✅ Upstream-Merge: 415 Commits von onyx-foss, 0 Core-Konflikte, DEV grün (2026-03-03)
  - ✅ DNS/TLS-Runbook erstellt (docs/runbooks/dns-tls-setup.md)
  - ✅ Fork-Management Doku überarbeitet (8-Schritte-Anleitung)
  - ✅ LLM: Embedding-Blocker aufgehoben (Upstream PR #9005). Wechsel auf Qwen3-VL-Embedding 8B jetzt moeglich.
  - ✅ DNS: A-Records gesetzt + Cloudflare DNS-only verifiziert (2026-03-05)
  - ⏳ TLS/HTTPS: Blockiert — DNS-Architektur (voeb-service.de bei GlobVill, nicht Cloudflare). Leif muss 2 ACME-Challenge CNAMEs bei GlobVill setzen. Token-Fix erledigt, ClusterIssuers READY. HTTP-01 nicht moeglich (Onyx Chart containerPort 1024). Details: docs/runbooks/dns-tls-setup.md
  - ✅ Cloud-Infrastruktur-Audit durchgeführt (2026-03-04): 10 CRITICAL, 18 HIGH, ~20 MEDIUM, ~12 LOW
  - ✅ 3 Security Quick Wins deployed (2026-03-05): C6 (DB_READONLY→Secret), H8 (Security-Header), H11 (Script Injection Fix)
  - ✅ C5/SEC-03: NetworkPolicies auf DEV + TEST applied (2026-03-05) — 5 Policies, Cross-NS-Isolation verifiziert
  - ✅ Node-Upgrade g1a.4d → g1a.8d (ADR-005, 2026-03-06): 8 vCPU, 32 GB RAM, 100 GB Disk pro Node
  - ✅ Upstream-Merge: 100 Commits (PR #3), 1 Konflikt (AGENTS.md), Core-Patch intakt (2026-03-06)
  - ✅ Celery: 8 separate Worker-Deployments (Lightweight Mode entfernt, Upstream PR #9014)
  - ✅ DEV: 16 Pods Running | TEST: 15 Pods Running (redeployed 2026-03-06)
  - ✅ PR-CI-Workflow (PR #4): helm-validate + build-backend + build-frontend (2026-03-06)
  - ✅ Branch Protection auf main: PR required, 3 Required Status Checks, kein Review-Requirement (Solo-Dev) (2026-03-07)
  - ✅ K8s v1.32 → v1.33 Upgrade (2026-03-08): v1.33.8, Flatcar 4459.2.1, Terraform apply 9m40s, DEV 16/16 + TEST 15/15 Pods Running
- **Phase 3 (Auth):** ⏳ Blockiert — wartet auf Entra ID von VÖB
- **Phase 4 (Extensions):**
  - 4a: ✅ Extension Framework Basis (Config, Feature Flags, Router, Health Endpoint, Docker)
  - 4b-4d: 📋 Geplant — Token Limits, RBAC, weitere Module (nach M1)
- **Phase 5-6:** Geplant (Testing, Production)

## Nächster Schritt
**1. TLS aktivieren (Leif muss 2 ACME-Challenge CNAMEs bei GlobVill setzen, Details: docs/runbooks/dns-tls-setup.md) → 2. M1-Abnahmeprotokoll ausfuellen → 3. Entra ID (wartet auf VÖB) → 4. Embedding auf Qwen3-VL (Blocker aufgehoben, via Admin-UI) → 5. SEC-06 Phase 2: runAsNonRoot (vor PROD). SEC-06 Phase 1 erledigt (privileged: false deployed). SEC-02/04/05 zurückgestellt (P3). SEC-07 erledigt.** Plan: `docs/referenz/stackit-implementierungsplan.md`

## Blocker
| Blocker | Wartet auf | Impact |
|---------|-----------|--------|
| TLS/HTTPS: 2 ACME-Challenge CNAMEs bei GlobVill | Leif (GlobVill DNS-Admin) | TLS fuer DEV + TEST |
| Entra ID Zugangsdaten | VÖB IT | Phase 3 |

## Erledigte Blocker
| Blocker | Gelöst | Datum |
|---------|--------|-------|
| StackIT Zugang | ✅ Zugang vorhanden | Feb 2026 |
| SA `project.admin`-Rolle | ✅ Rolle erteilt | 2026-02-22 |
| LLM API Keys | ✅ StackIT AI Model Serving Token erstellt, GPT-OSS 120B konfiguriert | 2026-02-27 |
| Embedding-Wechsel blockiert (PR #7541) | ✅ Upstream PR #9005 — Search Settings Swap re-enabled | 2026-03-06 |
| Cloudflare API Token Auth Error (10000) | ✅ Leif hat Permissions erweitert, ClusterIssuers READY | 2026-03-07 |
