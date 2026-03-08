# EE/FOSS-Lizenzabgrenzung

## Onyx FOSS (MIT) — KEINE Enterprise-Lizenz

Wir nutzen **ausschliesslich Onyx FOSS** (MIT-Lizenz). Fuer Onyx Enterprise Edition existiert **keine gueltige Lizenz**. Das bedeutet:

### VERBOTEN
- ❌ Code aus `backend/ee/` nutzen, kopieren oder portieren
- ❌ Code aus `web/src/ee/` nutzen, kopieren oder portieren
- ❌ `ENABLE_PAID_ENTERPRISE_EDITION_FEATURES` auf `true` setzen
- ❌ EE-Module als Dependency importieren (`from ee.onyx.* import ...`)
- ❌ EE-Patterns oder EE-Interfaces als Vorlage fuer ext_-Code verwenden
- ❌ EE-Lizenz (`web/src/ee/LICENSE`) ignorieren oder umgehen

### Technischer Hintergrund
- `backend/ee/` ist **leer** (nur `__init__.py`) — EE-Backend-Code existiert nicht in unserem Fork
- `web/src/ee/` enthaelt 6 Frontend-Dateien unter proprietaerer Lizenz — deaktiviert durch Feature-Gating
- 272 Stellen im Backend referenzieren `ee.onyx.*` — alle fallen automatisch auf FOSS-Defaults zurueck
- Konfiguration: `LICENSE_ENFORCEMENT_ENABLED: "false"` + `ENABLE_PAID_ENTERPRISE_EDITION_FEATURES: "false"`

### Was stattdessen tun
**Alle Enterprise-Features werden custom nachgebaut** in `backend/ext/` + `web/src/ext/`:

| EE-Feature (nicht verfuegbar) | Unser Modul | Feature Flag |
|-------------------------------|-------------|-------------|
| Enterprise Settings / Branding | `ext-branding` | `EXT_BRANDING_ENABLED` |
| Token/Usage Tracking | `ext-token` | `EXT_TOKEN_LIMITS_ENABLED` |
| Custom Prompts | `ext-prompts` | `EXT_CUSTOM_PROMPTS_ENABLED` |
| Analytics/Monitoring | `ext-analytics` | `EXT_ANALYTICS_ENABLED` |
| User Groups / RBAC | `ext-rbac` | `EXT_RBAC_ENABLED` |
| Document Access Control | `ext-access` | `EXT_DOC_ACCESS_ENABLED` |

### Erlaubt
- ✅ FOSS-Code lesen und verstehen (Architektur-Analyse)
- ✅ FOSS-Interfaces und Patterns als Inspiration (z.B. wie `EnterpriseSettings` aufgebaut ist)
- ✅ FOSS-Komponenten die `EnterpriseSettings` lesen → eigenen Backend-Store bauen der diese befuellt
- ✅ Eigene Implementierung in `backend/ext/` die gleiche Funktionalitaet bietet

### Referenz
Detaillierte Dokumentation: `docs/referenz/ee-foss-abgrenzung.md`
Entwicklungsplan: `docs/referenz/ext-entwicklungsplan.md`
