---
paths:
  - "backend/ext/tests/**"
  - "backend/tests/ext/**"
  - "web/src/ext/__tests__/**"
---

# Testing-Strategie für ext_-Code

Ohne Tests kein Merge.

## Test-Lokation
- Backend: `backend/tests/ext/` (pytest)
- Frontend: `web/src/ext/__tests__/` (Jest/Vitest — prüfe was Onyx nutzt)

## Pflicht-Kategorien pro Modul
1. **Unit Tests** — Einzelne Funktionen/Services isoliert
2. **Integration Tests** — API-Endpoint E2E mit Test-DB
3. **Feature Flag Test** — Flag=false → kein Effekt auf Onyx, keine Seiteneffekte
4. **Edge Case Tests** — Ungültige Inputs, leere DB, Concurrent Access

## Regeln
- Folge Onyx-Testpatterns (lies backend/tests/ als Referenz)
- conftest.py für Shared Fixtures (DB-Session, Test-User, Flag-Overrides)
- Isoliert: Keine Seiteneffekte auf Onyx-Testdaten
- Mocke Onyx-Abhängigkeiten (LLM-Calls, Auth) wo nötig
- NICHT testen: Bestehende Onyx-Funktionalität
