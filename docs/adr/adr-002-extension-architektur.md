# ADR-002: Extension-Architektur ("Extend, don't modify")

**Status**: Akzeptiert
**Aktualisiert**: 2026-02-12 (Pfade und Core-Dateien nach Phase 4a korrigiert)
**Author**: CCJ / Coffee Studios

---

## Context

Basierend auf **ADR-001** haben wir Onyx FOSS als Basis gewählt. Nun müssen wir folgende Frage klären:

### Herausforderung
Wie bauen wir **Custom Features** (Token Limits, RBAC, Branding, Analytics) für die VÖB **ohne** den Onyx FOSS Kern zu modifizieren?

### Anforderungen
- **Upstream-Sync**: Regelmäßige Updates von Onyx FOSS einfach zu integrieren
- **Custom Features**: Enterprise-Anforderungen implementieren (Token Limits, RBAC, etc.)
- **Wartbarkeit**: Code soll klar zwischen Core und Extensions getrennt sein
- **Skalierbarkeit**: Neue Features einfach hinzufügbar ohne Kern zu beeinflussen
- **Clear Ownership**: Welcher Code gehört zu welchem Modul?

### Nicht-Anforderungen
- **Dynamisches Plugin-System**: Plugins zur Runtime laden (zu komplex)
- **Komplett isolierte Extensions**: Völlige Isolation nicht praktisch für Datenbank

---

## Decision

**Wir folgen dem "Extend, don't modify"-Prinzip mit folgender Architektur:**

```
┌─────────────────────────────────────────────────────────────────┐
│ Git Repository: voeb-chatbot                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Onyx FOSS Core (unverändert, nur Merge)                     │ │
│ │ Backend:  backend/onyx/        (Python, FastAPI)            │ │
│ │ Frontend: web/src/             (Next.js, React, TypeScript) │ │
│ │ DB:       backend/alembic/     (Core Migrations)            │ │
│ │ [READONLY – nur upstream merges]                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                          ↓                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Custom Extension Layer (VÖB-Specific)                       │ │
│ │                                                             │ │
│ │ backend/ext/                    (Python, FastAPI)           │ │
│ │ ├── config.py                   (Feature Flags)            │ │
│ │ ├── routers/                    (FastAPI Router)            │ │
│ │ ├── models/                     (SQLAlchemy, ext_-Prefix)  │ │
│ │ ├── schemas/                    (Pydantic Schemas)         │ │
│ │ ├── services/                   (Business Logic)           │ │
│ │ ├── migrations/                 (Alembic, eigener Branch)  │ │
│ │ └── tests/                      (pytest)                   │ │
│ │                                                             │ │
│ │ web/src/ext/                    (TypeScript, React)        │ │
│ │ ├── components/                 (UI-Komponenten)           │ │
│ │ ├── pages/                      (Eigene Seiten /ext/...)   │ │
│ │ ├── hooks/                      (React Hooks)              │ │
│ │ └── lib/api.ts                  (API-Client)               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Integration Points (10 Core-Dateien, minimale Änderungen)  │ │
│ │ 1. backend/onyx/main.py         (Route Registration)       │ │
│ │ 2. backend/onyx/llm/multi_llm.py (Token Hook)             │ │
│ │ 3. backend/onyx/access/access.py (Access Control Hook)     │ │
│ │ 4. backend/onyx/chat/prompt_utils.py (Prompt Injection)    │ │
│ │ 5. web/src/app/layout.tsx        (Navigation)              │ │
│ │ 6. web/src/components/header/    (Branding)                │ │
│ │ 7. web/src/lib/constants.ts      (CSS Variables)           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Kern-Prinzipien

#### 1. Additive Extensions
- **Datenbank**: `ext_*` Tabellen für Custom Data
  - Nicht: Bestehende Core-Tabellen modifizieren
  - Beispiel: `ext_limits_quota`, `ext_rbac_groups`, `ext_branding_config`

- **API Routes**: `/api/ext/<modul>/*` für Custom Endpoints
  - Nicht: Bestehende `/api/` Routes modifizieren
  - Routing-Registry für Extensions

- **Frontend**: Custom Components in `web/src/ext/`
  - Injection Points für Custom UI (z. B. in Chat-Sidebar)
  - Nicht: Bestehende Komponenten modifizieren

#### 2. Minimale Core-Änderungen (7 nur)

Nur folgende **7 Files** dürfen im Core modifiziert werden:

```
1. backend/onyx/main.py                (Extension Routes registrieren)
2. backend/onyx/llm/multi_llm.py       (Token Hook nach LLM-Response)
3. backend/onyx/access/access.py        (Additiver Permission-Check)
4. backend/onyx/chat/prompt_utils.py    (Custom Prompt Injection)
5. web/src/app/layout.tsx               (Nav-Items für ext/-Seiten)
6. web/src/components/header/           (Branding mit Fallback)
7. web/src/lib/constants.ts             (CSS Variables mit --ext- Prefix)
```

> Details zu erlaubten Änderungen pro Datei: siehe `.claude/rules/core-dateien.md`

**Alles andere bleibt unverändert!**

#### 3. Feature Flag Pattern (Extension Registry)

Datei: `backend/ext/config.py`

```python
"""VÖB Extension Feature Flags."""
import os

# Master Switch — wenn false, lädt nichts
EXT_ENABLED: bool = os.getenv("EXT_ENABLED", "false").lower() == "true"

# Modul-Flags (AND-gated mit EXT_ENABLED)
EXT_TOKEN_LIMITS_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_TOKEN_LIMITS_ENABLED", "false").lower() == "true"
)
EXT_RBAC_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_RBAC_ENABLED", "false").lower() == "true"
)
# ... weitere Modul-Flags
```

Router-Registration in `backend/ext/routers/__init__.py`:

```python
def register_ext_routers(application: FastAPI) -> None:
    """Register all enabled extension routers."""
    from onyx.main import include_router_with_global_prefix_prepended
    from ext.config import EXT_ENABLED

    if not EXT_ENABLED:
        return

    # Health ist immer aktiv wenn EXT_ENABLED
    from ext.routers.health import router as ext_health_router
    include_router_with_global_prefix_prepended(application, ext_health_router)

    # Weitere Module hinter ihren Flags:
    # from ext.config import EXT_TOKEN_LIMITS_ENABLED
    # if EXT_TOKEN_LIMITS_ENABLED:
    #     from ext.routers.token_limits import router as token_limits_router
    #     include_router_with_global_prefix_prepended(application, token_limits_router)
```

Hook in `backend/onyx/main.py` (einzige bisherige Core-Änderung):

```python
# === VÖB Extension Framework Hook ===
try:
    from ext.config import EXT_ENABLED
    if EXT_ENABLED:
        from ext.routers import register_ext_routers
        register_ext_routers(application)
except ImportError:
    pass  # ext/ nicht vorhanden — Onyx läuft normal
```

#### 4. Datenbank-Isolation

**Onyx Core Tabellen**: `user`, `conversation`, `message`, `api_key`, etc.
- Nicht anfassen! Read-Only

**Extension Tabellen**: `ext_*` Konvention
- `ext_limits_quota`
- `ext_limits_usage_log`
- `ext_limits_alerts`
- `ext_rbac_groups`
- `ext_rbac_roles`
- `ext_branding_config`
- `ext_system_prompts`
- `ext_analytics_events`
- Etc.

**Foreign Keys**: Extensions können auf Core-Tabellen verweisen (z. B. FK zu `user.id`), aber Core referenziert nicht auf Extension-Tabellen.

```sql
-- Extension Table Example
CREATE TABLE ext_limits_quota (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES user(id),  -- FK to core
  monthly_limit_tokens INTEGER NOT NULL,
  current_month_tokens INTEGER DEFAULT 0,
  reset_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. Core-Hook-Pattern

Jeder Hook in einer Core-Datei folgt demselben Muster — Feature Flag + try/except, Onyx nie brechen:

```python
try:
    from ext.config import EXT_FEATURE_ENABLED
    if EXT_FEATURE_ENABLED:
        from ext.services.feature import do_something
        do_something(...)
except ImportError:
    pass  # ext/ nicht vorhanden → Onyx läuft normal
except Exception:
    import logging
    logging.getLogger("ext").error("Extension hook failed", exc_info=True)
    # NIEMALS Onyx-Funktionalität brechen
```

#### 6. Frontend Extensions

Frontend-Extensions leben in `web/src/ext/` und werden über die 3 Frontend-Core-Dateien eingebunden:
- `layout.tsx`: Nav-Items für ext/-Seiten (Conditional Rendering)
- `header/`: Logo/Titel durch Config-Werte mit Fallback auf Original
- `constants.ts`: Neue CSS Properties mit `--ext-` Prefix

---

## Rationale

### Warum Additive Approach?

1. **Upstream-Sync**: Bei neuen Onyx-Versionen einfache Merges
   - `git merge upstream/main` sollte funktionieren
   - Konflikte minimal, klar zu lösen

2. **Maintenance**: Zukünftige Entwickler verstehen schnell was Core vs. Extension ist
   - Klare Grenzen (`ext_*` Konvention)
   - Nicht versteckte Modifikationen im Core

3. **Testing**: Extensions können isoliert getestet werden
   - Unit Tests für Extension ohne Core zu starten
   - Integration Tests für Extension + Core zusammen

4. **Skalierbarkeit**: Neue Extensions ohne Kern-Änderungen hinzufügbar
   - Neue Feature = neuer Ordner in `backend/ext/` + `web/src/ext/`
   - Registrierung über Feature Flag in `backend/ext/config.py`
   - Keine Angst vor Breaking Changes

### Warum 10 Core-Änderungen nötig?

1. **backend/onyx/main.py**: Extension Routes müssen in FastAPI registriert werden
2. **backend/onyx/llm/multi_llm.py**: Token-Tracking nach LLM-Calls
3. **backend/onyx/access/access.py**: Additiver Permission-Check (Access Control)
4. **backend/onyx/chat/prompt_utils.py**: Custom Prompt Injection (prepend)
5. **web/src/app/layout.tsx**: Navigation für Extension-Seiten
6. **web/src/components/header/**: Branding (Logo/Titel über Config)
7. **web/src/lib/constants.ts**: CSS Variables für Extension-Theming
8. **web/src/app/auth/login/LoginText.tsx**: Login-Tagline durch Branding-Wert ersetzen (seit ext-branding)
9. **web/src/components/auth/AuthFlowContainer.tsx**: Login-Logo + App-Name (seit ext-branding)
10. **web/src/sections/sidebar/AdminSidebar.tsx**: Billing→Branding in Admin-Sidebar (seit ext-branding)

Punkte 1-7 sind **minimal notwendig** für das Extension Framework. Punkte 8-10 kamen durch ext-branding Whitelabel hinzu.

---

## Alternatives Considered

### Alternative 1: Microservices Approach

**Ansatz**: Extensions als separate Microservices (z. B. Token Limits als eigener Service)

**Vorteile**:
- Völlige Isolation
- Unabhängige Deployments
- Leicht zu skalieren

**Nachteile**:
- **Komplexität**: Service-to-Service Communication, Distributed Transactions
- **Latency**: API Calls zwischen Services
- **Operational Overhead**: Mehr Services zu monitoren, deployen
- **Overkill für Enterprise Chatbot**: Features sind eng verwoben (z. B. Token Limits + Chat)

**Entscheidung**: Abgelehnt – zu viel Overhead für diesen Use Case

---

### Alternative 2: Komplett isoliertes Plugin-System

**Ansatz**: Runtime-loadbare Plugins (z. B. über .wasm oder ähnlich)

**Vorteile**:
- Größte Isolation
- Keine Core-Änderungen nötig

**Nachteile**:
- **Sehr komplex**: Plugin-Loader, Versioning, Dependency Management
- **Schwer zu debuggen**: Runtime-loaded Code ist tricky
- **Overkill**: VÖB braucht das nicht
- **Zeitaufwand**: Monatelange Entwicklung

**Entscheidung**: Abgelehnt – nicht wirtschaftlich

---

### Alternative 3: Fork + Rebasing

**Ansatz**: Kompletter Fork von Onyx, regelmäßiges Rebasing auf Upstream

**Vorteile**:
- Vollständige Kontrolle
- Keine Constraints

**Nachteile**:
- **Merge-Nightmare**: Rebases werden immer komplizierter
- **Langfristig unmöglich**: Zu viele Divergenzen
- **Antithese zu Upstream-Sync**: Würde ADR-001 untergraben

**Entscheidung**: Abgelehnt – zu fragil

---

## Consequences

### Positive Auswirkungen

1. **Einfache Upstream-Merges**
   - Neue Onyx-Versionen alle 3-6 Monate integrierbar
   - Konflikt-Potential minimal
   - Security Updates einfach einzuspielen

2. **Klare Struktur**
   - Jeder weiß: Was ist Core? Was ist Extension?
   - `ext_*` Konvention macht es offensichtlich
   - Dokumentation selbst-erklärend

3. **Skalierbarkeit**
   - Neue Features hinzufügbar ohne Kern zu berühren
   - Keine Angst vor Breaking Changes
   - Langfristige Wartbarkeit

4. **Testing**
   - Extensions können isoliert getestet werden
   - Integration Tests für Extension + Core
   - CI/CD Pipeline einfacher

5. **Governance**
   - Klare Ownership: Core = Upstream, Extensions = VÖB
   - Code Review einfacher
   - Compliance/Audit trail klar

### Negative Auswirkungen / Mitigation

1. **10 Core-Änderungen nötig**
   - Mitigation: Diese 10 Files sind stabil, selten ändern sich
   - Impact: Minimal (nur beim initialen Setup + bei Major Onyx Updates)

2. **Extension Registry könnte komplex werden**
   - Mitigation: Gut dokumentieren, Beispiele geben
   - Impact: Engineering-Aufwand im Setup, aber zahlt sich aus

3. **Datenbank-Migrationen zwei separate Pfade**
   - Mitigation: Klare Konvention (core vs. ext_* files)
   - Impact: Migration-Scripts müssen beide laden

---

## Implementation Notes

### Folder Structure (Stand Phase 4a)

```
voeb-chatbot/
├── backend/
│   ├── onyx/                    (Core – READONLY, upstream merges)
│   │   ├── main.py              (CORE #1 – Extension Route Hook)
│   │   ├── llm/multi_llm.py    (CORE #2 – Token Hook)
│   │   ├── access/access.py    (CORE #3 – Access Control Hook)
│   │   ├── chat/prompt_utils.py (CORE #7 – Prompt Hook)
│   │   ├── db/models.py        (READ-ONLY)
│   │   └── server/             (READ-ONLY)
│   │
│   ├── ext/                     (NEW – VÖB Extension Code)
│   │   ├── __init__.py
│   │   ├── config.py            (Feature Flags)
│   │   ├── routers/
│   │   │   ├── __init__.py      (register_ext_routers)
│   │   │   └── health.py       (GET /api/ext/health)
│   │   ├── models/              (SQLAlchemy, ext_-Prefix)
│   │   ├── schemas/             (Pydantic Schemas)
│   │   ├── services/            (Business Logic)
│   │   ├── migrations/          (Alembic, eigener Branch)
│   │   ├── _core_originals/     (Backups vor Core-Änderungen)
│   │   └── tests/               (pytest)
│   │
│   ├── alembic/                 (Core Migrations – READ-ONLY)
│   └── requirements/            (Core Dependencies – READ-ONLY)
│
├── web/
│   ├── src/
│   │   ├── app/layout.tsx       (CORE #4 – Nav Items)
│   │   ├── components/header/   (CORE #5 – Branding)
│   │   ├── lib/constants.ts     (CORE #6 – CSS Variables)
│   │   └── ext/                 (NEW – Frontend Extensions)
│   │       ├── components/
│   │       ├── pages/
│   │       ├── hooks/
│   │       └── lib/api.ts
│   └── package.json             (READ-ONLY)
│
├── deployment/
│   ├── terraform/               (StackIT IaC)
│   ├── helm/values/             (Helm Value-Overlays)
│   └── docker_compose/          (.env mit EXT_-Flags)
│
├── docs/                        (Enterprise-Dokumentation)
│   ├── runbooks/                (Verifizierte Anleitungen)
│   ├── referenz/                (Implementierungsplan, Infrastruktur)
│   ├── adr/                     (Architecture Decision Records)
│   └── abnahme/                 (Meilenstein-Protokolle)
│
└── .github/workflows/
    ├── stackit-deploy.yml       (CI/CD → StackIT)
    └── upstream-check.yml       (Wöchentlicher Merge-Check)
```

### Naming Conventions

**Backend (Python)**:
- Packages: `backend/ext/<modul_name>/` (snake_case)
- Klassen: `ClassName` (PascalCase)
- Funktionen/Variablen: `function_name` (snake_case)
- Dateien: `file_name.py` (snake_case)

**Frontend (TypeScript)**:
- Ordner: `web/src/ext/<modul-name>/` (kebab-case)
- Komponenten: `ComponentName` (PascalCase)
- Hooks/Utilities: `camelCase`
- Dateien: `file-name.ts` / `ComponentName.tsx`

**Database**:
- Tables: `ext_<modul>_<entity>` (snake_case)
- Columns: `snake_case`
- Indexes: `idx_<table>_<column>`

**API**:
- Routes: `/api/ext/<modul>/<resource>` (kebab-case)
- Response: JSON mit `status`, `data`, `error`

---

## Related ADRs

- **ADR-001**: Onyx FOSS als Basis
  - Warum Onyx und nicht Custom-Build
- **ADR-003**: StackIT als Cloud Provider
  - Wie Extensions auf StackIT deployed werden

---

## Approval & Sign-off

| Rolle | Name | Datum | Signatur |
|-------|------|-------|----------|
| Architektur Lead (CCJ) | Nikolaj Ivanov | 2026-02-12 | __ |
| Projektleiter (CCJ) | [TBD] | [TBD] | __ |
| Auftraggeber (VÖB) | [TBD] | [TBD] | __ |

---

**ADR Status**: Akzeptiert
**Letzte Aktualisierung**: 2026-02-12
**Version**: 1.1 (Implementierungsdetails nach Phase 4a an tatsächliche Architektur angepasst)
