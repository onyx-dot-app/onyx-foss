---
paths:
  - "backend/ext/**"
  - "web/src/ext/**"
---

# Extension-Code Regeln

## Backend (`backend/ext/`)

Aktueller Stand (Phase 4a) und geplante Erweiterungen:

```
backend/ext/
  __init__.py                ← Package-Marker (existiert)
  config.py                  ← Feature Flags (existiert)
  routers/                   ← FastAPI Router (existiert: health.py)
  tests/                     ← pytest Tests (existiert: test_config.py)
  _core_originals/           ← Backups der Core-Dateien (existiert: main.py.*)
  # --- Ab Phase 4b werden diese Verzeichnisse erstellt: ---
  models/                    ← SQLAlchemy Models (ext_-Prefix)
  schemas/                   ← Pydantic Schemas
  services/                  ← Business Logic
```

> **Hinweis:** `models/`, `schemas/`, `services/` werden erst mit dem jeweils ersten
> Modul erstellt, das sie benoetigt. Nicht vorher leere Ordner anlegen.

## Frontend (`web/src/ext/`)

Aktuell nur `.gitkeep`. Wird ab Phase 4b befuellt:

```
web/src/ext/
  components/                ← Eigene React-Komponenten
  pages/                     ← Eigene Seiten (/ext/admin/...)
  hooks/                     ← Eigene React Hooks
  lib/api.ts                 ← Eigener API-Client (/api/ext/...)
  styles/                    ← Eigene Styles (ext- Prefix fuer Klassen)
  __tests__/                 ← Frontend-Tests
```

## Import-Regeln
- ext → Onyx: ERLAUBT (read-only)
- Onyx → ext: NUR in 9 Core-Dateien (einzige Brücke)
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
