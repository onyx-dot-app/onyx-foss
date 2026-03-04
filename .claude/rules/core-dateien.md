---
paths:
  - "backend/onyx/**"
  - "web/src/app/**"
  - "web/src/components/**"
  - "web/src/lib/**"
---

# Core-Dateien: Was darf geändert werden

**NUR DIESE 7 DATEIEN dürfen verändert werden. Keine Ausnahmen.**

## 1. `backend/onyx/main.py` — Router registrieren
- ERLAUBT: `from ext.config import EXT_ENABLED` + `register_ext_routers(app)` hinter Feature Flag + try/except ImportError
- VERBOTEN: Bestehende Router/Middleware/Startup-Events verändern
- MERGE: 7 Zeilen wieder einfügen (nach letztem Router, vor Auth-Block)
- HINWEIS: Funktion `get_application()` ab Zeile 419, Router-Registrierung Zeilen 447-509

## 2. `backend/onyx/llm/multi_llm.py` — Token Hook
- ERLAUBT: Nach LLM-Response Hook einfügen: `ext_token_counter.log_usage(...)` hinter Flag + Try/Except
- VERBOTEN: LLM-Call-Flow, Parameter, Return-Values verändern
- MERGE: Hook-Insertion-Point finden, Zeilen einfügen

## 3. `backend/onyx/access/access.py` — RBAC
- ERLAUBT: Additiver Permission-Check NACH bestehenden Checks
- VERBOTEN: Bestehende Checks verändern/entfernen
- MERGE: Additiv, einfach einfügen

## 4. `web/src/app/layout.tsx` — Navigation
- ERLAUBT: Nav-Items für ext/-Seiten, Conditional Rendering, Import ext/-Komponenten
- VERBOTEN: Bestehende Nav/Layout umbauen
- MERGE: Nav-Items einfügen

## 5. `web/src/components/header/` — Branding
- ERLAUBT: Logo/Titel durch Config-Werte ersetzen mit Fallback auf Original
- VERBOTEN: Header-Layout/Struktur verändern
- MERGE: Config-Injection anpassen

## 6. `web/src/lib/constants.ts` — CSS Variables
- ERLAUBT: Neue CSS Properties mit --ext- Prefix, neue Konstanten mit ext_-Prefix
- VERBOTEN: Bestehende Variablen umbenennen/ändern
- MERGE: Additiv, kein Konflikt

## 7. `backend/onyx/chat/prompt_utils.py` — System Prompts
- ERLAUBT: Hook für Custom Prompt Injection (prepend, nicht override) hinter Flag
- VERBOTEN: Bestehenden Prompt-Flow verändern
- MERGE: Injection-Point einfügen

## Absicherung
Vor JEDER Core-Datei-Änderung:
```bash
mkdir -p backend/ext/_core_originals/
cp <original> backend/ext/_core_originals/<name>.original
# Nach Änderung:
diff -u backend/ext/_core_originals/<name>.original <geändert> > backend/ext/_core_originals/<name>.patch
```

## Hook-Pattern für Core-Dateien
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
