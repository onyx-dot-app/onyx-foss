# Extension-Entwicklungsplan — VoeB Chatbot

**Stand**: Maerz 2026
**Erstellt von**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Bezug**: [EE/FOSS-Abgrenzung](ee-foss-abgrenzung.md) | [Extension Framework](../technisches-feinkonzept/ext-framework.md) | [Projektstatus](../../.claude/rules/voeb-projekt-status.md)

---

## Uebersicht

Alle Enterprise-Features werden custom in `backend/ext/` + `web/src/ext/` entwickelt, da wir Onyx FOSS (MIT) ohne Enterprise-Lizenz nutzen. Siehe [EE/FOSS-Abgrenzung](ee-foss-abgrenzung.md) fuer Details.

### Moduluebersicht

```
Phase 4a: ✅ Extension Framework Basis (erledigt)
          │
          ├── Phase 4b: ext-branding ← JETZT STARTBAR
          │     Whitelabel: Logo, App-Name, Farben, Favicon
          │
          ├── Phase 4c: ext-token ← JETZT STARTBAR
          │     LLM-Nutzung tracken, Limits pro User/Gruppe
          │
          ├── Phase 4d: ext-prompts ← JETZT STARTBAR
          │     Custom System Prompts pro Gruppe/Persona
          │
          ├── Phase 4e: ext-analytics ← JETZT STARTBAR
          │     Nutzungsstatistiken, Admin-Dashboard
          │
          ├── Phase 4f: ext-rbac ← BLOCKIERT (Entra ID)
          │     Rollen, Gruppen, Zugriffssteuerung
          │
          └── Phase 4g: ext-access ← BLOCKIERT (RBAC)
                Document Access Control pro Gruppe
```

---

## Abhaengigkeitsgraph

```
                    ┌─────────────────┐
                    │ Phase 4a:       │
                    │ ext-framework   │
                    │ ✅ ERLEDIGT     │
                    └────────┬────────┘
                             │
         ┌───────────┬───────┴───────┬────────────┐
         ▼           ▼               ▼            ▼
   ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐
   │ext-branding│ │ext-token │ │ext-prompts│ │ext-analytics│
   │ Phase 4b  │ │ Phase 4c │ │ Phase 4d  │ │ Phase 4e  │
   │ STARTBAR  │ │ STARTBAR │ │ STARTBAR  │ │ STARTBAR  │
   └───────────┘ └─────┬────┘ └───────────┘ └─────┬─────┘
                        │                           │
                        │      ┌──────────┐         │
                        └─────►│ext-rbac  │◄────────┘
                               │ Phase 4f │
                               │ BLOCKIERT│
                               │(Entra ID)│
                               └─────┬────┘
                                     │
                               ┌─────▼─────┐
                               │ext-access  │
                               │ Phase 4g   │
                               │ BLOCKIERT  │
                               │(braucht    │
                               │ RBAC)      │
                               └────────────┘
```

---

## Blocker-Analyse

| Modul | Blocker | Wartet auf | Workaround |
|-------|---------|-----------|------------|
| ext-branding | **Keiner** | — | — |
| ext-token | **Keiner** | — | — |
| ext-prompts | **Keiner** | — | — |
| ext-analytics | **Keiner** | — | — |
| ext-rbac | **Entra ID Zugangsdaten** | VoeB IT | Kein sinnvoller Workaround — Auth ist Voraussetzung |
| ext-access | **ext-rbac** | ext-rbac muss fertig sein | — |

---

## Empfohlene Reihenfolge

### Prioritaet 1: ext-branding (Phase 4b)

**Warum zuerst**: Sofort sichtbarer Mehrwert fuer VoeB. Kunde will komplettes Whitelabel — kein Onyx-Branding mehr sichtbar.

| Aspekt | Detail |
|--------|--------|
| **Scope** | App-Name, Logo, Favicon, Sidebar-Branding, Login-Seite, Browser-Tab |
| **Core-Aenderungen** | CORE #4 (layout.tsx): Favicon + Title | CORE #5 (header): Logo-Injection | CORE #6 (constants.ts): ext_-Konstanten |
| **Backend** | `backend/ext/routers/branding.py` — GET/PUT Branding Config |
| | `backend/ext/models/branding.py` — `ext_branding_config` Tabelle |
| | `backend/ext/services/branding.py` — Business Logic, Logo-Storage |
| **Frontend** | `web/src/ext/components/BrandingProvider.tsx` — Settings-Injection |
| **DB** | 1 Tabelle: `ext_branding_config` |
| **Feature Flag** | `EXT_BRANDING_ENABLED` (existiert bereits in config.py) |
| **Aufwand** | Mittel — Backend-Store + 3 Core-Patches + Frontend-Integration |
| **Abhaengigkeit** | Keine |

**Technischer Ansatz**: Die FOSS-Frontend-Komponenten (`Logo.tsx`, `SidebarWrapper.tsx`, `layout.tsx`) lesen bereits aus `EnterpriseSettings`. Wir bauen einen Backend-Store der dieselben Felder ueber unseren eigenen Endpoint befuellt (`/api/ext/branding/config`), und injizieren die Werte in den bestehenden `SettingsProvider`. So nutzen wir die vorhandene Rendering-Logik ohne sie zu duplizieren.

**Alternative**: Komplett eigene Komponenten in `web/src/ext/`. Vorteil: Null Abhaengigkeit von Onyx-Frontend. Nachteil: Doppelte Arbeit, Onyx-Logo-Reste koennten durchscheinen.

### Prioritaet 2: ext-token (Phase 4c)

**Warum als zweites**: Wichtig fuer Kostenkontrolle und Nutzungstransparenz. Banken brauchen Nachvollziehbarkeit.

| Aspekt | Detail |
|--------|--------|
| **Scope** | LLM-Aufrufe loggen (Tokens, Modell, User, Timestamp), Usage-API, spaeter: Limits |
| **Core-Aenderungen** | CORE #2 (multi_llm.py): Hook nach LLM-Response fuer Token-Logging |
| **Backend** | `backend/ext/routers/token.py` — GET Usage Stats |
| | `backend/ext/models/token.py` — `ext_token_usage` Tabelle |
| | `backend/ext/services/token_counter.py` — Zaehler + Aggregation |
| **Frontend** | `web/src/ext/pages/admin/token-usage.tsx` — Admin-Dashboard (spaeter) |
| **DB** | 1 Tabelle: `ext_token_usage` (user_id, model, prompt_tokens, completion_tokens, timestamp) |
| **Feature Flag** | `EXT_TOKEN_LIMITS_ENABLED` (existiert bereits in config.py) |
| **Aufwand** | Mittel — 1 Core-Patch + DB-Tabelle + Aggregations-Logik |
| **Abhaengigkeit** | Keine (User-Zuordnung funktioniert auch mit Basic Auth in DEV) |

### Prioritaet 3: ext-prompts (Phase 4d)

**Warum als drittes**: Ermoeglicht VoeB-spezifische Anweisungen an die LLMs (Tonalitaet, Compliance-Hinweise, Abteilungs-Kontext).

| Aspekt | Detail |
|--------|--------|
| **Scope** | System Prompt Injection (prepend, nicht replace), Admin-UI zum Verwalten |
| **Core-Aenderungen** | CORE #7 (prompt_utils.py): Hook fuer Custom Prompt Injection |
| **Backend** | `backend/ext/routers/prompts.py` — CRUD Prompt Templates |
| | `backend/ext/models/prompts.py` — `ext_prompt_templates` Tabelle |
| | `backend/ext/services/prompt_injection.py` — Injection-Logik |
| **Frontend** | `web/src/ext/pages/admin/prompt-templates.tsx` — Admin-UI |
| **DB** | 1 Tabelle: `ext_prompt_templates` (name, content, scope, is_active) |
| **Feature Flag** | `EXT_CUSTOM_PROMPTS_ENABLED` (existiert bereits in config.py) |
| **Aufwand** | Mittel — 1 Core-Patch + CRUD + Injection-Logik |
| **Abhaengigkeit** | Keine |

### Prioritaet 4: ext-analytics (Phase 4e)

**Warum als viertes**: Baut auf Token-Daten auf, liefert Management-relevante Insights.

| Aspekt | Detail |
|--------|--------|
| **Scope** | Nutzungsstatistiken aggregieren, Admin-Dashboard, CSV-Export |
| **Core-Aenderungen** | Keine — liest aus bestehenden ext_-Tabellen |
| **Backend** | `backend/ext/routers/analytics.py` — GET Statistiken, Export |
| | `backend/ext/services/analytics.py` — Aggregation, Reporting |
| **Frontend** | `web/src/ext/pages/admin/analytics.tsx` — Dashboard mit Charts |
| **DB** | Keine eigene Tabelle — liest aus ext_token_usage + ggf. ext_chat_logs |
| **Feature Flag** | `EXT_ANALYTICS_ENABLED` (existiert bereits in config.py) |
| **Aufwand** | Mittel — Aggregation + Frontend-Dashboard |
| **Abhaengigkeit** | Profitiert von ext-token (Token-Daten), funktioniert aber auch standalone |

### Prioritaet 5: ext-rbac (Phase 4f) — BLOCKIERT

**Blockiert durch**: Entra ID Zugangsdaten von VoeB IT

| Aspekt | Detail |
|--------|--------|
| **Scope** | 4 Rollen (System-Admin, Gruppen-Admin, Power-User, Standard-User), Gruppen = Abteilungen |
| **Core-Aenderungen** | CORE #3 (access.py): Additiver Permission-Check nach bestehenden Checks |
| **Backend** | `backend/ext/models/rbac.py` — `ext_user_groups`, `ext_user_roles`, `ext_group_permissions` |
| | `backend/ext/services/rbac.py` — Rollen-Mapping, Gruppen-Sync |
| | `backend/ext/services/entra_sync.py` — Entra ID Gruppen-Sync |
| **Frontend** | `web/src/ext/pages/admin/groups.tsx` — Gruppen-Verwaltung |
| **DB** | 3+ Tabellen |
| **Feature Flag** | `EXT_RBAC_ENABLED` (existiert bereits in config.py) |
| **Aufwand** | Hoch — Entra ID Integration + Rollen-System + Gruppen-Sync |
| **Abhaengigkeit** | Phase 3 (Entra ID Auth) muss abgeschlossen sein |
| **Vorarbeit** | Rollenmodell-Entwurf existiert (docs/referenz/rbac-rollenmodell.md), 10 Fragen an VoeB offen |

### Prioritaet 6: ext-access (Phase 4g) — BLOCKIERT

**Blockiert durch**: ext-rbac muss fertig sein

| Aspekt | Detail |
|--------|--------|
| **Scope** | Document Access Control: Welche Gruppe sieht welche Dokumente/Agenten/Modelle |
| **Core-Aenderungen** | CORE #3 (access.py): Gruppen-basierte Dokumentfilterung |
| **Abhaengigkeit** | ext-rbac (Gruppen muessen existieren) |

---

## Entwicklungs-Workflow pro Modul

Jedes Modul durchlaeuft denselben Prozess:

```
1. /modulspec erstellen
   └── docs/technisches-feinkonzept/ext-{modul}.md

2. Freigabe durch Niko
   └── Dokumentstatus: Freigegeben

3. /ext-framework aufrufen (6-Schritte-Pflicht)
   └── Analyse → Plan → Spec → Review → Implement → Test

4. Feature-Branch erstellen
   └── git checkout -b feature/ext-{modul}

5. Implementierung
   ├── Backend: ext/models/ → ext/services/ → ext/routers/
   ├── Core-Patches: _core_originals/ sichern → Hook einfuegen
   ├── Frontend: web/src/ext/
   └── Tests: ext/tests/

6. Selbst-Review (Sicherheits-Checkliste)
   └── .claude/rules/sicherheit.md

7. Praesentation an Niko
   └── Dateien, Tests, Core-Aenderungen, offene Punkte

8. Freigabe → Commit → PR → Merge → Deploy
```

---

## DB-Migrations-Strategie

Alle ext_-Tabellen nutzen **Onyx Alembic** (kein eigener Alembic-Branch):

```bash
# Migration erstellen
alembic revision -m "ext_branding: Create ext_branding_config table"

# Migration ausfuehren
alembic upgrade head
```

**Konventionen**:
- Tabellen-Prefix: `ext_` (z.B. `ext_branding_config`, `ext_token_usage`)
- Migrations-Prefix im Kommentar: `ext_{modul}:`
- Keine ALTER TABLE auf bestehende Onyx-Tabellen
- Foreign Keys auf Onyx-Tabellen (z.B. `user_.id`) sind erlaubt (READ-ONLY Referenz)

---

## Core-Datei-Aenderungen: Gesamtuebersicht

| Core | Datei | ext-branding | ext-token | ext-prompts | ext-rbac | ext-access |
|------|-------|:---:|:---:|:---:|:---:|:---:|
| #1 | `main.py` | — | — | — | — | — |
| #2 | `multi_llm.py` | — | ✅ | — | — | — |
| #3 | `access.py` | — | — | — | ✅ | ✅ |
| #4 | `layout.tsx` | ✅ | — | — | — | — |
| #5 | `header/` | ✅ | — | — | — | — |
| #6 | `constants.ts` | ✅ | — | — | — | — |
| #7 | `prompt_utils.py` | — | — | ✅ | — | — |

> CORE #1 (`main.py`) ist bereits gepatcht (Extension Framework Hook, Phase 4a).
> Alle Patches folgen dem try/except-Pattern aus `.claude/rules/core-dateien.md`.

---

## Feature-Flag-Uebersicht

Alle Flags existieren bereits in `backend/ext/config.py`:

| Flag | Modul | Default |
|------|-------|---------|
| `EXT_ENABLED` | Master-Switch | `false` |
| `EXT_BRANDING_ENABLED` | ext-branding | `false` |
| `EXT_TOKEN_LIMITS_ENABLED` | ext-token | `false` |
| `EXT_CUSTOM_PROMPTS_ENABLED` | ext-prompts | `false` |
| `EXT_ANALYTICS_ENABLED` | ext-analytics | `false` |
| `EXT_RBAC_ENABLED` | ext-rbac | `false` |
| `EXT_DOC_ACCESS_ENABLED` | ext-access | `false` |

Aktivierung in `deployment/docker_compose/.env` oder `deployment/helm/values/values-{env}.yaml`.

---

## Referenzen

- [EE/FOSS-Abgrenzung](ee-foss-abgrenzung.md) — Lizenz-Details
- [Extension Framework Spec](../technisches-feinkonzept/ext-framework.md) — Basis-Architektur
- [RBAC Rollenmodell](rbac-rollenmodell.md) — Rollen-Entwurf (Phase 4f)
- [Core-Dateien Regeln](../../.claude/rules/core-dateien.md) — Erlaubte Aenderungen
- [Sicherheits-Checkliste](../../.claude/rules/sicherheit.md) — Pruefung pro Modul
- [Commit-Workflow](../../.claude/rules/commit-workflow.md) — Branch + PR Prozess
