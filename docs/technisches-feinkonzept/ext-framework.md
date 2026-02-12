# Modulspezifikation: Extension Framework Basis

**Dokumentstatus**: Entwurf
**Version**: 1.0.0
**Autor**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Datum**: 2026-02-12
**Status**: [x] Entwurf | [ ] Review | [ ] Freigegeben
**Priorität**: [x] Kritisch | [ ] Hoch | [ ] Normal | [ ] Niedrig

---

## Modulübersicht

| Feld | Wert |
|------|------|
| **Modulname** | Extension Framework Basis |
| **Modul-ID** | `ext_framework` |
| **Version** | 1.0.0 |
| **Phase** | 4a |

---

## Zweck und Umfang

### Zweck
Das Extension Framework bildet die technische Grundlage für alle VÖB-spezifischen Erweiterungen des Onyx-Forks. Es stellt die Ordnerstruktur, Feature-Flag-Konfiguration, Router-Registrierung und einen Health-Check-Endpoint bereit. Alle nachfolgenden Module (Token Limits, RBAC, Analytics, Branding, etc.) bauen auf diesem Framework auf.

### Im Umfang enthalten
- Backend-Ordnerstruktur (`backend/ext/`)
- Frontend-Ordnerstruktur (`web/src/ext/`)
- Feature-Flag-Konfiguration via Environment Variables
- Router-Registrierungsmechanismus
- Health-Check-Endpoint als Proof-of-Concept
- Minimale Core-Datei-Änderung in `backend/onyx/main.py`
- Dokumentation der Pfad-Korrekturen (Regeln vs. tatsächliche Codebasis)

### Nicht im Umfang
- Datenbankmodelle/-migrationen (kommt mit Phase 4b+)
- Einzelne Feature-Module (Token Limits, RBAC, etc.)
- Frontend-Komponenten (kommt mit spezifischen Modulen)
- Alembic-Migration-Setup für ext (kommt wenn erstes DB-Modul implementiert wird)

### Abhängige Module / Prerequisites
- [x] Onyx Basis-Installation (vorhanden)
- [x] Git Fork-Setup (vorhanden, Branch `develop`)

---

## WICHTIG: Pfad-Korrekturen

Die Regeln in `.claude/rules/core-dateien.md` und `.claude/rules/codebase-orientierung.md` referenzieren Dateipfade, die nicht mit der tatsächlichen Codebasis übereinstimmen. Folgende Korrekturen gelten:

| # | Regel sagt | Tatsächlicher Pfad | Funktion |
|---|---|---|---|
| CORE #1 | `backend/onyx/server/app.py` | **`backend/onyx/main.py`** | FastAPI App + Router-Registrierung |
| CORE #2 | `backend/onyx/llm/llm_call.py` | **`backend/onyx/llm/multi_llm.py`** | LLM-Aufrufe |
| CORE #3 | `backend/onyx/auth/permissions.py` | **`backend/onyx/access/access.py`** | Permissions/Access Control |
| CORE #4 | `web/src/app/layout.tsx` | `web/src/app/layout.tsx` | *(stimmt)* |
| CORE #5 | `web/src/components/header/` | `web/src/components/header/` | *(stimmt)* |
| CORE #6 | `web/src/lib/constants.ts` | `web/src/lib/constants.ts` | *(stimmt)* |
| CORE #7 | `backend/onyx/chat/prompt_builder.py` | **`backend/onyx/chat/prompt_utils.py`** | System Prompts |

> **ADR-Empfehlung:** Die Regel-Dateien sollten nach Freigabe aktualisiert werden, um die korrekten Pfade zu reflektieren.

---

## Architektur

### Komponenten-Übersicht

```
backend/onyx/main.py (CORE #1)
        │
        │  try/except Hook (3 Zeilen)
        ↓
backend/ext/
  ├── __init__.py              ← Package-Marker
  ├── config.py                ← Feature Flags (EXT_ENABLED, EXT_*_ENABLED)
  └── routers/
      ├── __init__.py          ← register_ext_routers(app) Funktion
      └── health.py            ← GET /api/ext/health (Proof-of-Concept)

web/src/ext/
  ├── .gitkeep                 ← Platzhalter (noch keine Komponenten)
  └── README.md                ← Kurzbeschreibung der Struktur
```

### Datenfluss

1. Onyx-Server startet (`backend/onyx/main.py`)
2. `get_application()` registriert alle Onyx-Router
3. **Neuer Hook:** `try: from ext.config import EXT_ENABLED` → Bei `ImportError`: Skip (Onyx normal)
4. Wenn `EXT_ENABLED=true`: `register_ext_routers(app)` wird aufgerufen
5. `register_ext_routers()` prüft je Feature-Flag welche Sub-Router registriert werden
6. Health-Check-Endpoint wird registriert (immer wenn `EXT_ENABLED=true`)
7. `check_router_auth()` validiert alle Routen — ext-Routen haben Auth-Dependency

### Kritisches Detail: `check_router_auth()`

In `backend/onyx/main.py:558` wird `check_router_auth(application)` aufgerufen. Diese Funktion prüft, dass JEDE registrierte Route ein Auth-Dependency hat (z.B. `current_user`, `current_admin_user`, etc.) oder explizit als public deklariert ist.

**Konsequenz für ext-Routen:**
- Jeder ext-Endpoint MUSS ein Auth-Dependency haben
- ODER der Endpoint muss in `PUBLIC_ENDPOINT_SPECS` eingetragen werden (in `auth_check.py`)
- Der Health-Check-Endpoint wird `current_user` als Dependency haben (authentifizierter Health-Check)

---

## Betroffene Core-Dateien

### CORE #1: `backend/onyx/main.py`

**Änderung:** 7 Zeilen nach der letzten Router-Registrierung (Zeile ~421), VOR `check_router_auth()` (Zeile ~558):

```python
# === VÖB Extension Framework Hook ===
try:
    from ext.config import EXT_ENABLED
    if EXT_ENABLED:
        from ext.routers import register_ext_routers
        register_ext_routers(application)
        logger.info("VÖB Extension routers registered")
except ImportError:
    pass  # ext/ not present — Onyx runs normally
```

**Import-Pfad:** `from ext.xxx` (top-level, analog zu `from onyx.xxx` und `from ee.xxx`).
PYTHONPATH ist `/app` in Docker; `backend/ext/` wird als `/app/ext/` gemounted.

**Platzierung:** Nach Zeile 421 (`include_router_with_global_prefix_prepended(application, pat_router)`), vor dem Auth-Type-Block (Zeile 423).

**Backup:**
```bash
mkdir -p backend/ext/_core_originals/
cp backend/onyx/main.py backend/ext/_core_originals/main.py.original
# Nach Änderung:
diff -u backend/ext/_core_originals/main.py.original backend/onyx/main.py > backend/ext/_core_originals/main.py.patch
```

---

## Neue Dateien

### 1. `backend/ext/__init__.py`

Leerer Package-Marker mit Docstring:
```python
"""VÖB Extension Framework for Onyx.

All VÖB-specific extensions live in this package.
This code is NOT part of upstream Onyx and lives in a separate directory
to ensure zero merge conflicts during upstream syncs.
"""
```

### 2. `backend/ext/config.py`

Feature-Flag-Konfiguration, geladen aus Environment Variables:

```python
"""VÖB Extension Feature Flags.

All flags default to false (disabled).
EXT_ENABLED is the master switch — if false, nothing loads.
Individual module flags are AND-gated with EXT_ENABLED.
"""
import os

EXT_ENABLED: bool = os.getenv("EXT_ENABLED", "false").lower() == "true"

# Individual module flags (all gated behind EXT_ENABLED)
EXT_TOKEN_LIMITS_ENABLED: bool = EXT_ENABLED and os.getenv("EXT_TOKEN_LIMITS_ENABLED", "false").lower() == "true"
EXT_USER_GROUPS_ENABLED: bool = EXT_ENABLED and os.getenv("EXT_USER_GROUPS_ENABLED", "false").lower() == "true"
EXT_ANALYTICS_ENABLED: bool = EXT_ENABLED and os.getenv("EXT_ANALYTICS_ENABLED", "false").lower() == "true"
EXT_BRANDING_ENABLED: bool = EXT_ENABLED and os.getenv("EXT_BRANDING_ENABLED", "false").lower() == "true"
EXT_CUSTOM_PROMPTS_ENABLED: bool = EXT_ENABLED and os.getenv("EXT_CUSTOM_PROMPTS_ENABLED", "false").lower() == "true"
EXT_DOC_ACCESS_ENABLED: bool = EXT_ENABLED and os.getenv("EXT_DOC_ACCESS_ENABLED", "false").lower() == "true"
```

### 3. `backend/ext/routers/__init__.py`

Router-Registry-Funktion:

```python
"""Extension router registration.

Registers all enabled extension routers with the FastAPI application.
Uses the same include_router_with_global_prefix_prepended() pattern as Onyx.
"""
import logging

from fastapi import FastAPI

from onyx.main import include_router_with_global_prefix_prepended

logger = logging.getLogger("ext")


def register_ext_routers(application: FastAPI) -> None:
    """Register all enabled extension routers."""
    from ext.config import EXT_ENABLED

    if not EXT_ENABLED:
        return

    # Health check is always available when EXT_ENABLED
    from ext.routers.health import router as ext_health_router
    include_router_with_global_prefix_prepended(application, ext_health_router)
    logger.info("Extension health router registered")

    # Future module routers will be registered here behind their flags:
    # from ext.config import EXT_TOKEN_LIMITS_ENABLED
    # if EXT_TOKEN_LIMITS_ENABLED:
    #     from ext.routers.token_limits import router as token_limits_router
    #     include_router_with_global_prefix_prepended(application, token_limits_router)
```

### 4. `backend/ext/routers/health.py`

Health-Check-Endpoint (Proof-of-Concept, authentifiziert):

```python
"""Extension health check endpoint."""
from fastapi import APIRouter, Depends

from onyx.auth.users import current_user
from onyx.db.models import User
from ext.config import (
    EXT_ENABLED,
    EXT_TOKEN_LIMITS_ENABLED,
    EXT_USER_GROUPS_ENABLED,
    EXT_ANALYTICS_ENABLED,
    EXT_BRANDING_ENABLED,
    EXT_CUSTOM_PROMPTS_ENABLED,
    EXT_DOC_ACCESS_ENABLED,
)

router = APIRouter(prefix="/ext", tags=["ext"])


@router.get("/health")
def ext_health_check(
    _: User | None = Depends(current_user),
) -> dict:
    """Returns extension framework status and enabled modules."""
    return {
        "status": "ok",
        "ext_enabled": EXT_ENABLED,
        "modules": {
            "token_limits": EXT_TOKEN_LIMITS_ENABLED,
            "user_groups": EXT_USER_GROUPS_ENABLED,
            "analytics": EXT_ANALYTICS_ENABLED,
            "branding": EXT_BRANDING_ENABLED,
            "custom_prompts": EXT_CUSTOM_PROMPTS_ENABLED,
            "doc_access": EXT_DOC_ACCESS_ENABLED,
        },
    }
```

### 5. `web/src/ext/.gitkeep`

Leere Datei als Platzhalter für die Frontend-Extension-Struktur.

---

## Konfiguration

### Environment Variables

| Variable | Typ | Pflicht | Default | Beschreibung |
|----------|-----|---------|---------|-------------|
| `EXT_ENABLED` | boolean | Nein | `false` | Master-Schalter für alle Extensions |
| `EXT_TOKEN_LIMITS_ENABLED` | boolean | Nein | `false` | Token Limits Modul |
| `EXT_USER_GROUPS_ENABLED` | boolean | Nein | `false` | User Groups/RBAC Modul |
| `EXT_ANALYTICS_ENABLED` | boolean | Nein | `false` | Analytics Modul |
| `EXT_BRANDING_ENABLED` | boolean | Nein | `false` | Branding Modul |
| `EXT_CUSTOM_PROMPTS_ENABLED` | boolean | Nein | `false` | Custom Prompts Modul |
| `EXT_DOC_ACCESS_ENABLED` | boolean | Nein | `false` | Doc Access Modul |

### Verhalten bei `EXT_ENABLED=false` (Default)

- `ImportError` in `main.py` → `pass` → Onyx startet normal
- Keine ext-Router registriert
- `/api/ext/*` gibt 404
- Zero Performance-Impact
- Zero Seiteneffekte

### Verhalten bei `EXT_ENABLED=true`

- ext-Router werden registriert
- `/api/ext/health` ist erreichbar (authentifiziert)
- Einzelne Module nur wenn ihr Flag ebenfalls `true` ist

---

## Fehlerbehandlung

| Fehlerfall | Strategie |
|------------|-----------|
| `backend/ext/` existiert nicht | `ImportError` → `pass` → Onyx normal |
| `ext/config.py` hat Syntax-Fehler | `ImportError` → `pass` → Onyx normal |
| `EXT_ENABLED=false` | Kein Router registriert, keine Seiteneffekte |
| Einzelner Router-Import fehlschlägt | `try/except` in `register_ext_routers()` → Log + Skip |
| `check_router_auth()` findet Route ohne Auth | RuntimeError → muss VORHER behoben werden |

---

## Logging

| Level | Event | Wo |
|-------|-------|----|
| `INFO` | "Extension health router registered" | `register_ext_routers()` |
| `ERROR` | "Extension hook failed" | Nur bei unerwarteten Fehlern |
| `DEBUG` | Einzelne Flag-Werte | `config.py` (optional, nicht in v1) |

Logger-Name: `ext` (separater Logger für alle Extension-Logs)

---

## Verzeichnisstruktur nach Implementierung

```
backend/ext/
  ├── __init__.py
  ├── config.py
  ├── _core_originals/
  │   ├── main.py.original
  │   └── main.py.patch
  └── routers/
      ├── __init__.py
      └── health.py

web/src/ext/
  └── .gitkeep
```

---

## Tests

### Teststrategie
Unit Tests für Config und Router-Registrierung. Kein externer Service benötigt.

### Test 1: Feature Flags
```
Datei: backend/ext/tests/test_config.py
- Test: Alle Flags false wenn EXT_ENABLED=false
- Test: Einzelne Flags true nur wenn EXT_ENABLED=true UND eigenes Flag=true
- Test: EXT_ENABLED=true aber einzelnes Flag=false → Modul-Flag bleibt false
```

### Test 2: Health Endpoint
```
Datei: backend/ext/tests/test_health.py
- Test: GET /api/ext/health gibt 200 mit korrekter Struktur
- Test: Unauthentifizierter Request gibt 401
- Test: Response enthält alle Module-Flags
```

---

## Gelöste Punkte

- [x] **[OPEN-1]** Regel-Dateien aktualisiert mit korrekten Core-Datei-Pfaden
  - **Gelöst am**: 2026-02-12
  - **Ergebnis**: `.claude/rules/core-dateien.md` und `codebase-orientierung.md` korrigiert

- [x] **[OPEN-2]** Import-Pfad für `ext` — `from ext.xxx import ...` (top-level)
  - **Gelöst am**: 2026-02-12
  - **Ergebnis**: Onyx nutzt `PYTHONPATH=/app` in Docker (Dockerfile Zeile 161). Damit ist `ext` automatisch als Top-Level-Package importierbar — OHNE Änderung an `pyproject.toml` oder `Dockerfile`.
  - **Dev:** docker-compose Volume-Mount `./backend/ext:/app/ext`
  - **Lokal (ohne Docker):** `PYTHONPATH=backend` setzen
  - **Production (StackIT):** Eigenes `Dockerfile.voeb` das Onyx-Base-Image erweitert (in unserem Verzeichnis, NICHT im Onyx-Dockerfile)

- [x] **[OPEN-3]** Health-Endpoint bleibt authentifiziert
  - **Gelöst am**: 2026-02-12
  - **Entscheidung**: Authentifiziert (Depends `current_user`). Kein Informationsleak über aktivierte Module.

## Offene Punkte

Keine offenen Punkte.

### Gelöst: OPEN-4 (docker-compose + Dockerfile.voeb)
- **`deployment/docker_compose/docker-compose.voeb.yml`** — Volume-Mount `backend/ext:/app/ext` für `api_server` + `background`
- **`deployment/docker_compose/Dockerfile.voeb`** — Production-Image: `FROM onyxdotapp/onyx-backend:${IMAGE_TAG}` + `COPY ./ext /app/ext`
- Weder `pyproject.toml` noch `backend/Dockerfile` werden verändert

---

## Approvals

| Rolle | Name | Datum | Status |
|------|------|-------|--------|
| Tech Lead | Nikolaj Ivanov | TBD | Ausstehend |

---

## Revisions-Historie

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|-----------|
| 1.0 | 2026-02-12 | Claude (Entwurf) | Initialer Entwurf basierend auf Tiefenanalyse |
