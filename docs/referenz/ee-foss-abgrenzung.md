# EE/FOSS-Abgrenzung — Onyx Lizenzierung

**Stand**: Maerz 2026
**Erstellt von**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Bezug**: [Extension Framework](../technisches-feinkonzept/ext-framework.md) | [Extension-Entwicklungsplan](ext-entwicklungsplan.md)

---

## Warum Onyx FOSS?

Der VoeB Chatbot basiert auf **Onyx FOSS** (MIT-Lizenz), nicht auf Onyx Enterprise Edition.

| Kriterium | Onyx FOSS (MIT) | Onyx Enterprise |
|-----------|-----------------|-----------------|
| **Lizenz** | MIT — frei nutzbar | Proprietaer — kostenpflichtige Subscription |
| **Kosten** | 0 EUR | Subscription-basiert |
| **Quellcode** | Vollstaendig offen | Teils proprietaer |
| **Modifikation** | Uneingeschraenkt | Lizenzabhaengig |
| **Distribution** | Frei | Nur mit gueltigem Vertrag |
| **Support** | Community | Kommerziell |

**Entscheidung**: VoeB benoetigt volle Kontrolle ueber den Code, Datensouveraenitaet (StackIT, Region DE) und keine laufenden Lizenzkosten. Fehlende Enterprise-Features werden custom in `backend/ext/` und `web/src/ext/` nachgebaut.

---

## Lizenz-Dateien im Repository

| Datei | Lizenz | Scope |
|-------|--------|-------|
| `/LICENSE` | **MIT** | Gesamtes Repository (Root) |
| `/web/src/ee/LICENSE` | **Onyx Enterprise License** (proprietaer) | Nur `web/src/ee/` |

> **Wichtig**: Der Ordner `web/src/ee/` enthaelt 6 Frontend-Dateien (Search UI), die durch Feature-Gating deaktiviert sind. Der Ordner `backend/ee/` ist **leer** (nur `__init__.py`). Wir nutzen keinen EE-Code.

---

## Technische Architektur: EE-Gating in Onyx

Onyx trennt FOSS und EE durch ein dynamisches Ladesystem:

### Backend (Python)

```python
# backend/onyx/utils/variable_functionality.py
ENTERPRISE_EDITION_ENABLED = os.environ.get(
    "ENABLE_PAID_ENTERPRISE_EDITION_FEATURES", ""
).lower() == "true"

# Dynamischer Import mit Fallback
def fetch_versioned_implementation(module, attribute):
    if is_ee:
        try:
            return import_from(f"ee.{module}", attribute)  # EE-Version
        except ImportError:
            pass
    return import_from(module, attribute)  # FOSS-Fallback
```

**272 Stellen** im Backend referenzieren `ee.onyx.*`. Da `backend/ee/` leer ist, fallen ALLE auf FOSS-Defaults zurueck. Das System laeuft stabil.

### Frontend (TypeScript)

```typescript
// web/src/lib/constants.ts
export const SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED = ...

// web/src/ce.tsx — eeGated() Wrapper
// Komponenten mit eeGated() rendern nur bei aktiviertem EE
```

### Unsere Konfiguration

```yaml
# deployment/helm/values/values-common.yaml
LICENSE_ENFORCEMENT_ENABLED: "false"   # Kein Lizenz-Check
ENABLE_PAID_ENTERPRISE_EDITION_FEATURES: "false"  # EE deaktiviert
```

---

## EE-Features: Was fehlt und was wird nachgebaut

### Features die wir nachbauen (in `backend/ext/` + `web/src/ext/`)

| # | EE-Feature | EE-Modul (nicht vorhanden) | Unser Modul | Phase | Blocker |
|---|-----------|---------------------------|-------------|-------|---------|
| 1 | **Branding / Whitelabel** | `ee.onyx.server.enterprise_settings.store` | `ext-branding` | 4b | Keiner |
| 2 | **Token Limits / Usage Tracking** | — (existiert auch in EE nicht als Modul) | `ext-token` | 4c | Keiner |
| 3 | **Custom System Prompts** | `ee.onyx.chat` (teilweise) | `ext-prompts` | 4d | Keiner |
| 4 | **Analytics / Monitoring** | `ee.onyx.server.monitoring` | `ext-analytics` | 4e | Keiner |
| 5 | **RBAC / User Groups** | `ee.onyx.db.user_group`, `ee.onyx.access` | `ext-rbac` | 4f | Entra ID |
| 6 | **Document Access Control** | `ee.onyx.external_permissions` | `ext-access` | 4g | RBAC |

### Features die wir NICHT nachbauen

| EE-Feature | Grund |
|-----------|-------|
| Multi-Tenant Support | VoeB = Single-Tenant |
| SCIM Provisioning | Entra ID Gruppen-Sync reicht |
| Billing API | Nicht relevant (internes Tool) |
| License Enforcement | Nicht relevant (eigener Fork) |

---

## Onyx FOSS: Was bereits funktioniert

Diese Features sind im FOSS-Code enthalten und funktionieren ohne EE:

| Feature | Status |
|---------|--------|
| Chat (LLM-Integration, Streaming) | Funktioniert |
| Document Connectors (50+) | Funktioniert |
| Vespa Search (Hybrid, Embedding) | Funktioniert |
| Admin-UI (Connectors, Modelle, Settings) | Funktioniert |
| OAuth2 / OIDC Auth (Basis) | Funktioniert |
| Celery Background Workers | Funktioniert (8 Worker) |
| Persona / Assistant Builder | Funktioniert |

### FOSS-Code der EE-Settings referenziert

Das Frontend (FOSS) enthaelt Komponenten die `EnterpriseSettings` lesen:

| Komponente | Liest aus EnterpriseSettings | Ohne EE |
|-----------|------------------------------|---------|
| `Logo.tsx` | `use_custom_logo`, `application_name`, `logo_display_style` | Zeigt Onyx-Logo |
| `layout.tsx` | `application_name` (HTML Title + Favicon) | Zeigt "Onyx" |
| `SidebarWrapper.tsx` | Logo-Rendering | Zeigt Onyx-Logo |
| `LoginText.tsx` | `application_name` | Zeigt "Onyx" |
| `AppPopup.tsx` | `application_name`, `custom_popup_*` | Zeigt Onyx-Defaults |

**Konsequenz fuer ext-branding**: Wir muessen einen Backend-Store bauen, der dieselben `EnterpriseSettings`-Felder befuellt. Die Frontend-Rendering-Logik existiert bereits — sie braucht nur Daten.

---

## Architekturprinzip: Extend, don't modify

```
Onyx FOSS (MIT, READ-ONLY)          Unsere Extensions (MIT, eigener Code)
┌─────────────────────────┐         ┌──────────────────────────┐
│ backend/onyx/           │ ──7──►  │ backend/ext/             │
│ web/src/app/            │ Patches │ web/src/ext/             │
│ web/src/components/     │         │                          │
│                         │         │ config.py (Feature Flags) │
│ 272× ee.onyx.* Imports  │         │ routers/ (API Endpoints)  │
│ → alle fallen auf       │         │ models/ (DB, ext_-Prefix) │
│   FOSS-Defaults zurueck │         │ services/ (Business Logic)│
└─────────────────────────┘         └──────────────────────────┘
```

- **7 Core-Dateien** duerfen minimal geaendert werden (Hook-Pattern mit try/except)
- **Patches** werden als `.original` + `.patch` in `backend/ext/_core_originals/` gesichert
- **Upstream-Merges** sind konfliktfrei fuer ext_-Code (Ordner existiert nicht in Upstream)
- **Feature Flags** steuern alles: `EXT_ENABLED` (Master) + `EXT_{MODUL}_ENABLED` (pro Modul)

---

## Referenzen

- [Extension Framework Spec](../technisches-feinkonzept/ext-framework.md)
- [Core-Dateien Regeln](../../.claude/rules/core-dateien.md)
- [Fork-Management](../../.claude/rules/fork-management.md)
- [Sicherheits-Checkliste](../../.claude/rules/sicherheit.md)
