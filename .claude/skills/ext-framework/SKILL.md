---
name: ext-framework
description: 6-Schritte-Pflicht-Workflow vor jeder Extension-Implementierung. Rufe diesen Skill auf BEVOR du Code schreibst.
---

# Extension Framework — Pflicht-Workflow

**Befolge diese 6 Schritte in exakter Reihenfolge. Keine Ausnahmen.**

## Schritt 1: Tiefenanalyse des bestehenden Codes

Lies und verstehe die betroffenen Onyx-Dateien VOLLSTÄNDIG:
- Öffne jede relevante Datei und lies sie komplett
- Analysiere: Imports, Typen, Klassenstruktur, Patterns, Abhängigkeiten
- Verstehe den Datenfluss: Woher kommen die Daten? Wohin gehen sie?
- Prüfe bestehende Tests: Welche Patterns? Was wird getestet?
- Schreibe KEINEN Code auf Basis von Annahmen

## Schritt 2: Selbst-Check (beantworte jede Frage)

- [ ] Verstehe ich den Code wirklich, oder rate ich?
- [ ] Passt mein Ansatz zu Onyx-Patterns? (SQLAlchemy, FastAPI, Alembic, Pydantic)
- [ ] Verändere ich NUR die 10 Core-Dateien auf erlaubte Weise?
- [ ] Neue Dateien NUR unter backend/ext/ und web/src/ext/?
- [ ] Alle Edge Cases bedacht? (leere DB, fehlende Config, Flag=false, Concurrent Access)
- [ ] Feature Flag vorhanden und abschaltbar?
- [ ] Onyx funktioniert normal wenn alle Flags false sind?

**Bei Unsicherheit: STOPP und nachfragen.**

## Schritt 3: Modulspezifikation schreiben

Erstelle unter `docs/technisches-feinkonzept/{modulname}.md`:
- API-Endpoints (Pfad, Methode, Request/Response, Fehlercodes)
- DB-Schema (ext_-Prefix, Spalten, Typen, FKs, Indizes)
- Fehlerbehandlung (jeder Fehlerfall + Strategie)
- Abhängigkeiten (welche Onyx-Module, welche Core-Dateien)
- Feature Flags (Name, Default, Verhalten wenn deaktiviert)
- Betroffene Core-Dateien (welche der 7, wie verändert)

Template: `docs/technisches-feinkonzept/template-modulspezifikation.md`

## Schritt 4: Spec vorlegen

Zeige Niko die Modulspezifikation. Erst nach EXPLIZITER Freigabe wird Code geschrieben.

## Schritt 5: Implementierung

Erst jetzt Code schreiben — strikt nach Spec:
- Feature-Branch: `feature/{modulname}` von main
- Backend: `backend/ext/`
- Frontend: `web/src/ext/`
- Tests: `backend/tests/ext/` + `web/src/ext/__tests__/`
- Core-Dateien: NUR wie in Spec + Backup erstellen

## Schritt 6: Selbst-Review

Lies deinen Code kritisch:
- [ ] Error Handling komplett?
- [ ] Type Safety? Keine unnötigen Any-Types?
- [ ] Feature Flag Test: Funktioniert alles mit Flag=false?
- [ ] Keine Seiteneffekte auf Onyx?
- [ ] Tests vorhanden und sinnvoll?
- [ ] Nur erlaubte Dateien verändert?

Dann: Niko das Ergebnis präsentieren (siehe @.claude/rules/commit-workflow.md).

---

## Entscheidungsbaum: Muss ich eine Core-Datei ändern?

```
Brauche ich Daten aus Onyx?
  → JA: Kann ich per DB-Query (read-only) oder internem API-Call zugreifen?
    → JA: KEINE Core-Datei-Änderung nötig. Mach es so. ✅
    → NEIN: Ist es eine der 7 erlaubten Stellen?
      → JA: Minimaler Hook/Import. Backup + Patch. In Spec dokumentieren.
      → NEIN: STOPP. Frage Niko. Es gibt wahrscheinlich einen anderen Weg.

Muss ich Onyx-Verhalten erweitern?
  → Ist es eine der 7 erlaubten Stellen?
    → JA: Minimaler Hook. Backup + Patch. In Spec dokumentieren.
    → NEIN: STOPP. Frage Niko. Ggf. neues ADR nötig.
```

---

## Referenz: Code-Patterns

### Pattern 1: Feature Flag Config
```python
# backend/ext/config.py
import os
EXT_ENABLED = os.getenv("EXT_ENABLED", "true").lower() == "true"
EXT_TOKEN_LIMITS_ENABLED = EXT_ENABLED and os.getenv("EXT_TOKEN_LIMITS_ENABLED", "false").lower() == "true"
EXT_RBAC_ENABLED = EXT_ENABLED and os.getenv("EXT_RBAC_ENABLED", "false").lower() == "true"
EXT_ANALYTICS_ENABLED = EXT_ENABLED and os.getenv("EXT_ANALYTICS_ENABLED", "false").lower() == "true"
EXT_BRANDING_ENABLED = EXT_ENABLED and os.getenv("EXT_BRANDING_ENABLED", "false").lower() == "true"
EXT_CUSTOM_PROMPTS_ENABLED = EXT_ENABLED and os.getenv("EXT_CUSTOM_PROMPTS_ENABLED", "false").lower() == "true"
EXT_DOC_ACCESS_ENABLED = EXT_ENABLED and os.getenv("EXT_DOC_ACCESS_ENABLED", "false").lower() == "true"
```

### Pattern 2: Router Registration (Core-Datei #1 app.py)
```python
# NUR diese Zeilen in backend/onyx/server/app.py hinzufügen:
try:
    from backend.ext.config import EXT_ENABLED
    if EXT_ENABLED:
        from backend.ext.routers import register_ext_routers
        register_ext_routers(app)
except ImportError:
    pass  # ext/ nicht vorhanden → Onyx läuft normal
```

### Pattern 3: Hook mit Error Handling (Core-Datei #2 llm_call.py)
```python
# NACH dem LLM-Response in backend/onyx/llm/llm_call.py:
try:
    from backend.ext.config import EXT_TOKEN_LIMITS_ENABLED
    if EXT_TOKEN_LIMITS_ENABLED:
        from backend.ext.services.token_counter import log_token_usage
        log_token_usage(user_id=user.id, model=model, tokens_used=response.usage)
except Exception:
    import logging
    logging.getLogger("ext").error("Token logging failed", exc_info=True)
    # NIEMALS Onyx-Funktionalität brechen
```

### Pattern 4: SQLAlchemy ext_-Model
```python
# backend/ext/models/token_models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from onyx.db.models import Base

class ExtTokenBudget(Base):
    __tablename__ = "ext_token_budgets"  # IMMER ext_-Prefix
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # FK auf Onyx
    monthly_limit = Column(Integer, nullable=False, default=100000)
    current_usage = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
```

### Pattern 5: Frontend Wrapper
```tsx
// web/src/ext/components/ExtHeader.tsx — NICHT Header.tsx editieren!
import { Header } from "@/components/header/Header";

export function ExtHeader() {
  const config = useExtBrandingConfig();
  if (!config) return <Header />;  // Fallback: Original Onyx
  return (
    <div className="ext-header-wrapper">
      <img src={config.logoUrl} className="ext-logo" />
      <span className="ext-title">{config.title}</span>
    </div>
  );
}
```

### Pattern 6: Onyx-Daten lesen (OHNE Dateien zu ändern)
```python
# backend/ext/services/analytics_service.py
from onyx.db.engine import get_session
from onyx.db.models import User, ChatMessage

def get_user_statistics(user_id: int):
    with get_session() as db:
        # ✅ SELECT auf Onyx-Tabellen (read-only)
        count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
        # ✅ Schreiben NUR in eigene ext_-Tabelle
        db.add(ExtUsageStats(user_id=user_id, total_messages=count))
        # ❌ NIEMALS Onyx-Tabellen verändern
```

### Pattern 7: .env Feature Flags
```env
# deployment/docker_compose/.env
EXT_ENABLED=true
EXT_TOKEN_LIMITS_ENABLED=true
EXT_RBAC_ENABLED=true
EXT_ANALYTICS_ENABLED=false
EXT_BRANDING_ENABLED=false
EXT_CUSTOM_PROMPTS_ENABLED=false
EXT_DOC_ACCESS_ENABLED=false
```

### Flag=false bedeutet konkret:
```
Wenn EXT_TOKEN_LIMITS_ENABLED=false:
  ✅ DB-Tabellen existieren (Migrationen laufen immer)
  ✅ Python-Code liegt im Dateisystem
  ❌ Router NICHT registriert → /api/ext/token/* gibt 404
  ❌ Hooks feuern NICHT
  ❌ Keine DB-Queries auf ext_token_*
  → Onyx verhält sich als gäbe es das Modul nicht
```
