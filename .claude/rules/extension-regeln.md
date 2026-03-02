---
paths:
  - "backend/ext/**"
  - "web/src/ext/**"
---

# Extension-Code Regeln

## Backend (`backend/ext/`)
```
backend/ext/
  __init__.py
  config.py                  ← Feature Flags (EXT_{MODUL}_ENABLED)
  requirements.txt           ← Eigene Dependencies
  routers/                   ← FastAPI Router pro Modul
  models/                    ← SQLAlchemy Models (ext_-Prefix)
  schemas/                   ← Pydantic Schemas
  services/                  ← Business Logic
  migrations/versions/       ← Eigene Alembic-Migrationen
  tests/                     ← pytest Tests
  _core_originals/           ← Backups der Core-Dateien vor Änderung
```

## Frontend (`web/src/ext/`)
```
web/src/ext/
  components/                ← Eigene React-Komponenten
  pages/                     ← Eigene Seiten (/ext/admin/...)
  hooks/                     ← Eigene React Hooks
  lib/api.ts                 ← Eigener API-Client (/api/ext/...)
  styles/                    ← Eigene Styles (ext- Prefix für Klassen)
  __tests__/                 ← Frontend-Tests
```

## Import-Regeln
- ext → Onyx: ERLAUBT (read-only)
- Onyx → ext: NUR in 7 Core-Dateien (einzige Brücke)
- Sichere Imports: `onyx.db.models`, `onyx.db.engine`, `onyx.auth.users`, `onyx.configs.*`, `onyx.server.schemas`
- Vorsicht: `onyx.llm.*`, `onyx.chat.*`, `onyx.indexing.*` (Git-History prüfen)
- Verboten: `onyx.utils.internal`, `onyx.cli`, `onyx.background`

## Feature Flags
```python
# backend/ext/config.py
EXT_ENABLED = os.getenv("EXT_ENABLED", "true").lower() == "true"
EXT_TOKEN_LIMITS_ENABLED = EXT_ENABLED and os.getenv("EXT_TOKEN_LIMITS_ENABLED", "false").lower() == "true"
# ... pro Modul
```
Flag=false → Router nicht registriert, Hooks feuern nicht, keine DB-Queries. Onyx läuft 100% normal.

## Frontend-Regeln (Merge-Konflikt-Prävention)
- NIEMALS bestehende Onyx-Komponenten/CSS editieren
- Wrapper-Pattern: ExtHeader wraps Header, Fallback auf Original
- Eigene Routes unter /ext/ Prefix
- Tailwind + CSS Variables (--ext-*)
- Klassen-Prefix: ext-
