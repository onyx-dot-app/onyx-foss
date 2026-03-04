# Naechste Session — Entra ID Vorbereitung + M1-Abnahme + Doku-Fixes

## Wo wir stehen (2026-03-04)

**Warten auf Leif (DNS + CF Token). Termin Freitag 06.03, 11:00 (Entra ID).**

### Was heute passiert ist
- Tiefenanalyse aller offenen Tasks (64 Tasks identifiziert, priorisiert)
- Embedding-Modell: E5 Mistral 7B → Qwen3-VL-Embedding 8B (bessere Deutsch-Unterstuetzung)
- Embedding-Wechsel via UI **blockiert** durch Upstream (PR #7541, OpenSearch-Migration)
- Fallback `nomic-embed-text-v1` (self-hosted) ist aktiv — RAG funktioniert
- 18 Doku-Dateien aktualisiert (Modell, Domain, Status)
- Neues Runbook: `docs/runbooks/llm-konfiguration.md` (Chat + Embedding Anleitung)
- Alle `voeb.example.com` → `voeb-service.de` korrigiert (0 veraltete Referenzen)
- Uncommitted Changes: 13+ Dateien (Doku-Updates, neues Runbook)

---

## Prioritaeten fuer naechste Session

### 1. Uncommitted Changes committen (nach Nikos Review)
Viele Doku-Aenderungen aus dieser Session. Dateien:
- `docs/betriebskonzept.md`, `docs/sicherheitskonzept.md`, `docs/CHANGELOG.md`
- `docs/referenz/stackit-infrastruktur.md`, `docs/referenz/stackit-implementierungsplan.md`
- `docs/abnahme/meilensteinplan.md`
- `docs/runbooks/llm-konfiguration.md` (NEU), `docs/runbooks/README.md`, `docs/runbooks/helm-deploy.md`
- `.claude/rules/voeb-projekt-status.md`, `.claude/next-session-prompt.md`

### 2. Entra ID vorbereiten (Termin Fr 06.03, 11:00)
- Helm Values Template fuer OIDC vorbereiten (AUTH_TYPE, OAUTH_CLIENT_ID, etc.)
- Redirect URIs dokumentieren: `https://dev.chatbot.voeb-service.de/auth/oidc/callback`
- Checkliste fuer den Termin mit Leif erstellen
- Onyx OIDC-Code pruefen: welche Env-Vars/Config werden gebraucht?
- **Voraussetzung:** HTTPS muss laufen! Falls Leif bis Freitag DNS + Token liefert, erst TLS aktivieren.

### 3. Falls Leif vorher liefert — HTTPS aktivieren (~30 Min)
Runbook: `docs/runbooks/dns-tls-setup.md` (komplett, alle Befehle drin)

### 4. M1-Abnahmeprotokoll erstellen
- Template: `docs/abnahme/abnahmeprotokoll-template.md`
- Ist-Zustand befuellen (was funktioniert, was blockiert)
- VoEB-Termin fuer Abnahme-Meeting ansetzen

### 5. Weitere Quick-Wins (ohne Blocker)
- `values-prod.yaml` Grundgeruest erstellen (CI/CD referenziert die Datei, existiert aber nicht!)
- PROD Deploy-Job fixen (fehlender Smoke Test + `--create-namespace`)
- `upstream-check.yml` SHA-pinning (actions/checkout@v4 → SHA)
- ADR-003 ENTWURF-Abschnitte ausfuellen (Infra ist live, Details bekannt)
- IP-Allowlisting fuer DEV/TEST vorbereiten (Nginx Ingress Annotations, BAIT)

---

## Finale URLs

| Environment | URL | IP |
|---|---|---|
| DEV | `https://dev.chatbot.voeb-service.de` | `188.34.74.187` |
| TEST | `https://test.chatbot.voeb-service.de` | `188.34.118.201` |
| PROD | `https://chatbot.voeb-service.de` | noch nicht provisioniert |

## Blocker

| Was | Wer | Status |
|-----|-----|--------|
| 2x DNS A-Records (DNS-only!) | Leif | Mail raus, ausstehend |
| Cloudflare API Token | Leif | Mail raus, ausstehend |
| Entra ID App-Registrierung | Leif + Niko | Termin Fr 06.03, 11:00 |
| Embedding-Modell-Wechsel (Qwen3-VL) | Onyx Upstream (PR #7541) | Warten auf Re-Enablement |

## Embedding-Status (wichtig!)

- **Aktuell aktiv:** `nomic-ai/nomic-embed-text-v1` (self-hosted auf Model Server, 768 Dim)
- **Ziel:** `Qwen/Qwen3-VL-Embedding-8B` (StackIT, 4096 Dim, multilingual, 32k Context)
- **Blocker:** Onyx hat Embedding-Wechsel via Admin UI deaktiviert (PR #7541, OpenSearch-Migration)
- **Impact:** RAG funktioniert mit nomic, aber nicht optimal fuer Deutsch
- **Naechster Schritt:** Bei jedem Upstream-Merge pruefen ob Endpoint reaktiviert
- **Runbook:** `docs/runbooks/llm-konfiguration.md` (komplett, inkl. Troubleshooting)
- **Admin UI Pfad:** Search Settings → Embedding Model → Cloud-based → LiteLLM
- **Kritisch:** Embedding API URL muss `/v1/embeddings` sein (nicht nur `/v1`)

## Dateien

- Runbook DNS/TLS: `docs/runbooks/dns-tls-setup.md`
- Runbook LLM: `docs/runbooks/llm-konfiguration.md` (NEU)
- Memory: `memory/MEMORY.md`
- Zeitplanung: `memory/clickup-zeitplanung.md`
- Helm DEV: `deployment/helm/values/values-dev.yaml` (noch HTTP/IP)
- Helm TEST: `deployment/helm/values/values-test.yaml` (noch HTTP/IP)
- Upstream-Blocker Code: `backend/onyx/server/manage/search_settings.py:50`
