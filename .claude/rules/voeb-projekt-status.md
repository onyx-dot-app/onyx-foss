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
  - ⏳ DNS: `dev.chatbot.voeb.example.com` → `188.34.74.187`
  - ⏳ TLS/HTTPS (nach DNS-Setup)
  - ✅ LLM: GPT-OSS 120B + Qwen3-VL 235B via StackIT AI Model Serving (2026-02-27)
  - ⏳ LLM: Embedding-Modell (E5 Mistral 7B) noch nicht konfiguriert
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
  - ⏳ values-test.yaml Commit + Push (DOMAIN/WEB_DOMAIN eingetragen)
  - ⏳ CI/CD workflow_dispatch für TEST verifizieren
  - ⏳ LLM-Konfiguration in TEST Admin UI
  - ⏳ DNS + TLS
- **Phase 3 (Auth):** ⏳ Blockiert — wartet auf Entra ID von VÖB
- **Phase 4 (Extensions):**
  - 4a: ✅ Extension Framework Basis (Config, Feature Flags, Router, Health Endpoint, Docker)
  - 4b-4d: 📋 Geplant — Token Limits, RBAC, weitere Module (nach M1)
- **Phase 5-6:** Geplant (Testing, Production)

## Nächster Schritt
**1. Commit + Push (values-test.yaml + Projektstatus) → 2. CI/CD workflow_dispatch TEST verifizieren → 3. LLM in TEST Admin UI → 4. Embedding-Modell → 5. DNS + TLS.** Plan: `docs/referenz/stackit-implementierungsplan.md`, Phase 7

## Blocker
| Blocker | Wartet auf | Impact |
|---------|-----------|--------|
| Entra ID Zugangsdaten | VÖB IT | Phase 3 |
| JNnovate Scope | JNnovate | Aufgabenverteilung |

## Erledigte Blocker
| Blocker | Gelöst | Datum |
|---------|--------|-------|
| StackIT Zugang | ✅ Zugang vorhanden | Feb 2026 |
| SA `project.admin`-Rolle | ✅ Rolle erteilt | 2026-02-22 |
| LLM API Keys | ✅ StackIT AI Model Serving Token erstellt, GPT-OSS 120B konfiguriert | 2026-02-27 |
