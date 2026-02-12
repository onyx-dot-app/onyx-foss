# VÖB Chatbot — Projektstatus

## Projekt
- **Auftraggeber:** VÖB (Bundesverband Öffentlicher Banken Deutschlands)
- **Auftragnehmer:** CCJ / Coffee Studios (Tech Lead: Nikolaj Ivanov)
- **Cloud:** StackIT (Kubernetes, Datensouveränität)
- **Auth:** Microsoft Entra ID (OIDC)
- **Basis:** Fork von Onyx FOSS (MIT) mit Custom Extension Layer

## Tech Stack (zusätzlich zu Onyx)
- CI: upstream-check.yml (wöchentlicher Merge-Kompatibilitäts-Check)
- Docker: deployment/docker_compose/ (.env mit EXT_-Feature Flags)
- Enterprise-Docs: docs/ (Sicherheitskonzept, Testkonzept, Betriebskonzept, ADRs, Abnahme)

## Aktueller Status

- **Phase 0-1.5:** ✅ Grundlagen, Dev Environment, Dokumentation
- **Phase 2 (Cloud):** ⏳ Blockiert — wartet auf JNnovate + StackIT
- **Phase 3 (Auth):** ⏳ Blockiert — wartet auf Entra ID von VÖB
- **Phase 4 (Extensions):**
  - 4a: ✅ Extension Framework Basis (Config, Feature Flags, Router, Health Endpoint, Docker)
  - 4b-4d: 📋 **NÄCHSTER SCHRITT** — Token Limits, RBAC, weitere Module
  - **Beginne mit 4b. Rufe `/ext-framework` auf.**
- **Phase 5-6:** Geplant (Testing, Production)

## Blocker
| Blocker | Wartet auf | Impact |
|---------|-----------|--------|
| Entra ID Zugangsdaten | VÖB IT | Phase 3 |
| StackIT Zugang | VÖB / StackIT | Phase 2 |
| LLM API Keys | StackIT | Chat nicht testbar |
| JNnovate Scope | JNnovate | Aufgabenverteilung |
