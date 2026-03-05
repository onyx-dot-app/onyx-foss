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
- Docker: `deployment/docker_compose/` (.env mit EXT_-Feature Flags)
- Enterprise-Docs: `docs/` (Sicherheitskonzept, Testkonzept, Betriebskonzept, ADRs, Abnahme)

## Aktueller Status

- **Phase 0-1.5:** ✅ Grundlagen, Dev Environment, Dokumentation
- **Phase 2 (Cloud / M1 Infrastruktur):** ✅ **DEV LIVE** (2026-02-27)
  - ✅ StackIT-Zugang, CLI, Service Account, Container Registry
  - ✅ Terraform apply: SKE (g1a.4d), PG Flex, Object Storage
  - ✅ K8s Namespace `onyx-dev` + Image Pull Secret + Redis Operator
  - ✅ PostgreSQL: DB `onyx` angelegt, `db_readonly_user` per Terraform
  - ✅ Object Storage: Credentials erstellt, in Helm Secrets konfiguriert
  - ✅ Helm Release `onyx-dev`: Alle 10 Pods 1/1 Running
  - ✅ API Health OK, Login funktioniert unter `http://188.34.74.187`
  - ✅ Runbooks: stackit-projekt-setup.md, stackit-postgresql.md, helm-deploy.md
  - ✅ CI/CD Pipeline: Produktionsreif (2026-03-02) — Parallel-Build ~8 Min, SHA-gepinnte Actions, Smoke Tests, Concurrency
  - ✅ Upstream-Workflows: 21 Onyx-Workflows deaktiviert, nur StackIT Deploy + Upstream Check aktiv
  - ✅ CI/CD Run #5 (ea70a11): 10 Min, alle 10 Pods Running, Health Check OK
  - ✅ EE-Crash gelöst: `LICENSE_ENFORCEMENT_ENABLED: "false"` in values-common.yaml
  - ⏳ DNS: `dev.chatbot.voeb-service.de` → `188.34.74.187`
  - ⏳ TLS/HTTPS (nach DNS-Setup)
  - ✅ LLM: GPT-OSS 120B + Qwen3-VL 235B via StackIT AI Model Serving (2026-02-27)
  - ⚠️ LLM: Embedding-Wechsel auf Qwen3-VL-Embedding 8B blockiert durch Upstream (PR #7541, OpenSearch-Migration). Fallback: nomic-embed-text-v1 (self-hosted) aktiv und funktional.
  - 📋 Scope: DEV live, TEST live.
- **Phase 2 TEST:** ✅ **TEST LIVE** (2026-03-03)
  - ✅ SEC-01: PG ACL eingeschränkt (188.34.93.194/32 + Admin)
  - ✅ Node Pool auf 2 Nodes skaliert (DEV + TEST)
  - ✅ Terraform apply TEST: PG Flex `vob-test` + Bucket `vob-test`
  - ✅ Namespace `onyx-test` + Image Pull Secret + DB `onyx` angelegt
  - ✅ GitHub Environment `test` + 5 Secrets (PG, Redis, S3)
  - ✅ Helm Release `onyx-test`: 9 Pods Running (+ redis-operator im default NS), Health Check OK
  - ✅ TEST erreichbar unter `http://188.34.118.201`
  - ✅ Eigene IngressClass `nginx-test` (Conflict mit DEV vermieden)
  - ✅ values-test.yaml Commit + Push (2026-03-03)
  - ✅ CI/CD workflow_dispatch TEST verifiziert — Build + Deploy grün (2026-03-03)
  - ✅ LLM: GPT-OSS 120B + Qwen3-VL 235B in TEST konfiguriert (2026-03-03)
  - ✅ Enterprise-Dokumentation überarbeitet: Betriebskonzept, Sicherheitskonzept, Meilensteinplan, ADR-004, README, CHANGELOG (2026-03-03)
  - ✅ Upstream-Merge: 415 Commits von onyx-foss, 0 Core-Konflikte, DEV grün (2026-03-03)
  - ✅ DNS/TLS-Runbook erstellt (docs/runbooks/dns-tls-setup.md)
  - ✅ Fork-Management Doku überarbeitet (8-Schritte-Anleitung)
  - ⚠️ LLM: Embedding-Wechsel auf Qwen3-VL blockiert (Upstream PR #7541). nomic-embed-text-v1 aktiv als Fallback.
  - ⏳ DNS + TLS (Runbook bereit, wartet auf Domain-Entscheidung mit VÖB)
  - ✅ Cloud-Infrastruktur-Audit durchgeführt (2026-03-04): 10 CRITICAL, 18 HIGH, ~20 MEDIUM, ~12 LOW
  - ✅ 3 Security Quick Wins deployed (2026-03-05): C6 (DB_READONLY→Secret), H8 (Security-Header), H11 (Script Injection Fix)
  - ✅ C5/SEC-03: NetworkPolicies auf DEV + TEST applied (2026-03-05) — 5 Policies, Cross-NS-Isolation verifiziert
- **Phase 3 (Auth):** ⏳ Blockiert — wartet auf Entra ID von VÖB
- **Phase 4 (Extensions):**
  - 4a: ✅ Extension Framework Basis (Config, Feature Flags, Router, Health Endpoint, Docker)
  - 4b-4d: 📋 Geplant — Token Limits, RBAC, weitere Module (nach M1)
- **Phase 5-6:** Geplant (Testing, Production)

## Nächster Schritt
**1. DNS/TLS aktivieren (wartet auf Leif) → 2. M1-Abnahmeprotokoll ausfüllen → 3. Entra ID (Termin 06.03) → 4. Embedding auf Qwen3-VL (nach Upstream-Fix) → 5. SEC-02 bis SEC-04 (vor PROD).** Plan: `docs/referenz/stackit-implementierungsplan.md`

## Blocker
| Blocker | Wartet auf | Impact |
|---------|-----------|--------|
| Entra ID Zugangsdaten | VÖB IT | Phase 3 |

## Erledigte Blocker
| Blocker | Gelöst | Datum |
|---------|--------|-------|
| StackIT Zugang | ✅ Zugang vorhanden | Feb 2026 |
| SA `project.admin`-Rolle | ✅ Rolle erteilt | 2026-02-22 |
| LLM API Keys | ✅ StackIT AI Model Serving Token erstellt, GPT-OSS 120B konfiguriert | 2026-02-27 |
