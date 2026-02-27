# VÖB Chatbot — Projektstatus

## Projekt
- **Auftraggeber:** VÖB (Bundesverband Öffentlicher Banken Deutschlands)
- **Auftragnehmer:** CCJ / Coffee Studios (Tech Lead: Nikolaj Ivanov)
- **Cloud:** StackIT (Kubernetes, Datensouveränität, Region EU01 Frankfurt)
- **Auth:** Microsoft Entra ID (OIDC)
- **Basis:** Fork von Onyx FOSS (MIT) mit Custom Extension Layer

## Tech Stack (zusätzlich zu Onyx)
- IaC: Terraform (`deployment/terraform/`) — StackIT Provider ~> 0.56
- Helm: Value-Overlays (`deployment/helm/values/`) — Onyx Chart READ-ONLY
- CI/CD: `.github/workflows/stackit-deploy.yml` (Build → StackIT Registry → Helm Deploy)
- CI: `upstream-check.yml` (wöchentlicher Merge-Kompatibilitäts-Check)
- Docker: `deployment/docker_compose/` (.env mit EXT_-Feature Flags)
- Enterprise-Docs: `docs/` (Sicherheitskonzept, Testkonzept, Betriebskonzept, ADRs, Abnahme)

## Aktueller Status

- **Phase 0-1.5:** ✅ Grundlagen, Dev Environment, Dokumentation
- **Phase 2 (Cloud / M1 Infrastruktur):** 🔧 **IN ARBEIT**
  - ✅ StackIT-Zugang vorhanden
  - ✅ Terraform-Module erstellt (SKE, PostgreSQL Flex, Object Storage)
  - ✅ Helm Value-Overlays erstellt (values-common.yaml, values-dev.yaml)
  - ✅ CI/CD Pipeline erstellt (stackit-deploy.yml)
  - ✅ Implementierungsplan: `docs/referenz/stackit-implementierungsplan.md`
  - ✅ StackIT CLI installiert + Login
  - ✅ Service Account `voeb-terraform` erstellt + Key generiert
  - ✅ Container Registry aktiviert
  - ✅ Terraform init + plan erfolgreich (5 Ressourcen: SKE, PG, Storage)
  - ✅ Terraform-Code Fix: `default_region` (Provider v0.80)
  - ✅ Runbooks erstellt: `docs/runbooks/`
  - ✅ SA `project.admin`-Rolle erteilt (2026-02-22)
  - ✅ Terraform apply (DEV) erfolgreich (2026-02-22) — SKE, PG Flex, Object Storage provisioniert
  - ⏳ K8s Namespace + Secrets erstellen
  - ⏳ Erster Helm Deploy (DEV)
  - 📋 Scope: **Nur DEV-Umgebung.** TEST/PROD folgt nach stabilem DEV.
- **Phase 3 (Auth):** ⏳ Blockiert — wartet auf Entra ID von VÖB
- **Phase 4 (Extensions):**
  - 4a: ✅ Extension Framework Basis (Config, Feature Flags, Router, Health Endpoint, Docker)
  - 4b-4d: 📋 Geplant — Token Limits, RBAC, weitere Module (nach M1)
- **Phase 5-6:** Geplant (Testing, Production)

## Nächster Schritt
**K8s Namespace + Secrets einrichten, dann erster Helm Deploy (DEV).** Plan: `docs/referenz/stackit-implementierungsplan.md`

## Blocker
| Blocker | Wartet auf | Impact |
|---------|-----------|--------|
| Entra ID Zugangsdaten | VÖB IT | Phase 3 |
| LLM API Keys | StackIT | Chat nicht testbar |
| JNnovate Scope | JNnovate | Aufgabenverteilung |

## Erledigte Blocker
| Blocker | Gelöst | Datum |
|---------|--------|-------|
| StackIT Zugang | ✅ Zugang vorhanden | Feb 2026 |
| SA `project.admin`-Rolle | ✅ Rolle erteilt | 2026-02-22 |
