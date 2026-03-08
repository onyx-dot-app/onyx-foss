# Modulspezifikation: ext-branding (Whitelabel/Branding)

**Dokumentstatus**: Implementiert
**Version**: 1.0
**Autor**: Nikolaj Ivanov (CCJ / Coffee Studios)
**Datum**: 2026-03-08
**Status**: [ ] Entwurf | [ ] Review | [x] Implementiert
**Prioritaet**: [x] Hoch | [ ] Kritisch | [ ] Normal | [ ] Niedrig

### Implementierungsstatus (2026-03-08)

| Komponente | Status | Anmerkung |
|------------|--------|-----------|
| Backend REST-API (5 Endpoints) | Implementiert | GET/PUT Config + Logo, public + admin |
| Datenbank ext_branding_config | Implementiert | Migration `ff7273065d0d`, Singleton-Pattern |
| Core-Patch CORE #6 (constants.ts) | Implementiert | 1 Zeile, Patch generiert |
| Core-Patch CORE #8 (LoginText.tsx) | Implementiert | Conditional Render, Patch generiert |
| Core-Patch CORE #9 (AuthFlowContainer.tsx) | Implementiert | Logo + Name Override, Patch generiert |
| Unit-Tests (21 Tests) | Bestanden | Schema, Magic Bytes, Defaults, Constraints |
| Docker-Integration | Verifiziert | Lokal getestet, alle Endpoints OK |
| Admin-UI (Browser-Seite) | Vorbereitet | Code existiert in `web/src/ext/`, Route fehlt (Next.js App Router) |
| Favicon | Offen | Nicht im Scope v1.0 (siehe "Nicht im Umfang") |
| Farben/Theme | Offen | Eigenes Modul, nicht Teil von ext-branding |

### Abweichungen von Spec v0.3

| Spec | Implementierung | Grund |
|------|-----------------|-------|
| Core-Patches CORE #4 + #5 (layout.tsx, header) | Nicht noetig | FOSS-Komponenten lesen automatisch von `/enterprise-settings` |
| Endpoint-Pfad `/api/ext/branding/config` | `/enterprise-settings` | Identischer Pfad wie EE — FOSS-Frontend braucht keine Aenderung |
| Public Endpoints mit Auth | Public ohne Auth | Login-Seite braucht Branding vor User-Login |
| Revision ID `a1b2c3d4e5f6` | `ff7273065d0d` | Kollision mit existierender Onyx-Migration gleicher ID |
| "Powered by Onyx" entfernen | Via Env-Variable | `NEXT_PUBLIC_DO_NOT_USE_TOGGLE_OFF_DANSWER_POWERED=true` (kein Code-Patch noetig) |
| Docker nicht erwähnt in Spec | 3 Docker-Aenderungen | `Dockerfile`: COPY ext/, `docker-compose.voeb.yml`: main.py Mount, `.env`: Feature Flags |
| Auth auf public Endpoints | Public ohne Auth + PUBLIC_ENDPOINT_SPECS | Runtime-Mutation der Onyx-Allowlist in `ext/routers/__init__.py` (keine Dateiänderung) |
| Hook protect-onyx-files.sh | 7 → 9 Core-Dateien | CORE #8 (LoginText.tsx) + CORE #9 (AuthFlowContainer.tsx) zur Allowlist |

---

## Moduluebersicht

| Feld | Wert |
|------|------|
| **Modulname** | Whitelabel Branding |
| **Modul-ID** | `ext_branding` |
| **Version** | 1.0.0 |
| **Phase** | 4b |
| **Feature Flag** | `EXT_BRANDING_ENABLED` (existiert in `backend/ext/config.py`) |
| **Abhaengigkeiten** | Phase 4a Extension Framework ✅ |

---

## Zweck und Umfang

### Zweck

Der VoeB-Kunde soll sein eigenes Branding sehen — kein Onyx-Logo, kein Onyx-Name. Das Modul ermoeglicht die vollstaendige Whitelabel-Konfiguration ueber eine Admin-Oberflaeche: App-Name, Logo, Favicon, Sidebar-Branding, Login-Seite, Willkommens-Popup und Chat-Header. Dies ist der erste sichtbare Mehrwert fuer den Kunden nach der Infrastruktur-Phase.

### Im Umfang enthalten

- Backend: REST-API fuer Branding-Konfiguration (CRUD) + Logo-Upload/Serving
- Datenbank: `ext_branding_config` Tabelle + Alembic-Migration
- Frontend: Admin-Seite zur Branding-Verwaltung unter `web/src/ext/`
- Core-Patches: CORE #6 (`constants.ts`) 1 Zeile + CORE #8 (`LoginText.tsx`) ~3 Zeilen + CORE #9 (`AuthFlowContainer.tsx`) ~5 Zeilen
- Feature-Flag-Gating: Alles hinter `EXT_BRANDING_ENABLED`

### Nicht im Umfang

- Custom CSS / Farbschema-Anpassung (eigenes Modul, spaeter)
- Custom Navigation Items (Feld wird gespeichert, Admin-UI dafuer kommt spaeter)
- Logotype-Upload (separates Bild neben Logo — Feld existiert, Upload kommt spaeter)
- Multi-Tenant-Branding (VoeB = Single-Tenant)

### Abhaengige Module / Prerequisites

- [x] Phase 4a: Extension Framework Basis (erledigt)
- [x] Onyx FOSS laufende Installation
- [ ] Keine weiteren Abhaengigkeiten

---

## Kritische Architekturentscheidung: EnterpriseSettings-Kompatibilitaet

### Erkenntnis aus Tiefenanalyse

Die FOSS-Frontend-Komponenten lesen bereits `EnterpriseSettings` aus dem React Context (`SettingsProvider`). Die Rendering-Logik fuer Branding existiert vollstaendig — sie bekommt nur keine Daten, weil der Backend-Endpoint fehlt.

**Betroffene FOSS-Komponenten (bereits vorhanden, benoetigen NULL Aenderungen):**

| Komponente | Pfad | Liest aus EnterpriseSettings |
|-----------|------|------------------------------|
| `Logo.tsx` | `web/src/refresh-components/Logo.tsx` | `use_custom_logo`, `application_name`, `logo_display_style` |
| `layout.tsx` | `web/src/app/layout.tsx` | `application_name` (HTML Title), `use_custom_logo` (Favicon) |
| `SidebarWrapper.tsx` | `web/src/sections/sidebar/SidebarWrapper.tsx` | `application_name`, `logo_display_style` |
| `LoginText.tsx` | `web/src/app/auth/login/LoginText.tsx` | `application_name` (Begruessung) |
| `AppPopup.tsx` | `web/src/app/app/components/AppPopup.tsx` | `show_first_visit_notice`, `custom_popup_header`, `custom_popup_content`, `enable_consent_screen`, `consent_screen_prompt`, `use_custom_logo`, `logo_display_style` |

### Fetching-Kette (IST-Zustand ohne ext-branding)

```
constants.ts: SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED = false
     │          (weil ENABLE_PAID_ENTERPRISE_EDITION_FEATURES=false
     │           UND LICENSE_ENFORCEMENT_ENABLED=false)
     ▼
lib.ts: fetchSettingsSS() → prueft Flag → UEBERSPRINGT /enterprise-settings Fetch
     │
     ▼
SettingsProvider: enterpriseSettings = null
     │
     ▼
Logo.tsx, layout.tsx, etc.: Zeigen Onyx-Defaults (Logo, Name "Onyx")
```

### Zwei moegliche Ansaetze

#### Ansatz A: Registrierung auf `/enterprise-settings` Pfad (EMPFOHLEN)

```
CORE #6 (constants.ts): EXT_BRANDING_ENABLED=true → Flag wird true
     │
     ▼
lib.ts (UNVERAENDERT): fetchSettingsSS() → Flag=true → FETCHT /enterprise-settings
     │
     ▼
Backend (NEU): ext-Router auf /enterprise-settings → liefert Branding-Config
     │
     ▼
SettingsProvider: enterpriseSettings = { application_name: "VoeB Chatbot", ... }
     │
     ▼
Logo.tsx, layout.tsx, etc.: Zeigen VoeB-Branding (AUTOMATISCH, null Aenderungen)
```

**Vorteile:**
- Nur 1 Core-Datei geaendert (CORE #6, 1 Zeile)
- CORE #4 (`layout.tsx`) und CORE #5 (`header/`) brauchen KEINE Aenderung
- Alle 5+ Frontend-Komponenten funktionieren automatisch
- `lib.ts` (`web/src/components/settings/lib.ts`) bleibt unveraendert (ist KEIN Core-File)
- Minimale Angriffflaeche fuer Upstream-Merge-Konflikte

**Risiken:**
- Pfad `/enterprise-settings` ist semantisch fuer EE gedacht — koennte bei Upstream-Merges zu Verwirrung fuehren
- Wenn Onyx zukuenftig FOSS-Endpoints unter diesem Pfad registriert, entsteht ein Routing-Konflikt

**Risikobewertung:** Gering. Der Pfad existiert nicht in FOSS (und hat es nie). `backend/ee/` ist in unserem Fork leer. Selbst wenn Upstream FOSS-Endpoints dort einfuehrt, wuerden wir das beim woechentlichen Upstream-Check (`upstream-check.yml`) sofort bemerken und reagieren koennen.

#### Ansatz B: Eigener Pfad `/api/ext/branding/config` + Frontend-Injection

```
Backend: Eigener Router /api/ext/branding/config
     │
     ▼
Frontend (NEU): web/src/ext/providers/BrandingProvider.tsx
     │         → Fetcht /api/ext/branding/config
     │         → Injiziert in SettingsProvider oder eigenen Context
     ▼
Problem: Bestehende Komponenten lesen aus SettingsProvider,
         nicht aus ext-BrandingProvider → muessten geaendert werden
         → Aber diese Dateien sind NICHT in den 7 Core-Files
```

**Vorteile:**
- Sauberer ext_-Namespace
- Kein "Borgen" von EE-Pfaden

**Nachteile:**
- Frontend-Rendering-Komponenten muessen modifiziert werden (Logo.tsx, SidebarWrapper.tsx, etc.)
- Diese Dateien sind NICHT in der erlaubten Core-Datei-Liste → Regel-Verletzung ODER Regel-Erweiterung noetig
- Deutlich mehr Code, mehr Merge-Konflikte
- Doppelte Arbeit: Rendering-Logik die Onyx FOSS bereits perfekt implementiert hat

### Empfehlung

**Ansatz A** ist die Best-Practice-Loesung. Er nutzt die existierende Frontend-Infrastruktur exakt so wie sie entworfen wurde. Die einzige Aenderung ist semantisch korrekt: Wir HABEN Enterprise-Settings (unsere eigenen), also soll das Frontend sie auch laden.

### Abweichung vom Entwicklungsplan

Der Extension-Entwicklungsplan (`docs/referenz/ext-entwicklungsplan.md`) listet 3 Core-Aenderungen:

| Geplant | Tatsaechlich noetig | Grund |
|---------|-------------------|-------|
| CORE #4 (`layout.tsx`): Favicon + Title | **Nicht noetig** | `layout.tsx` prueft bereits `SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED` und fetcht automatisch |
| CORE #5 (`header/`): Logo-Injection | **Nicht noetig** | `Logo.tsx` liest bereits aus `enterpriseSettings` Context |
| CORE #6 (`constants.ts`): ext_-Konstanten | **Ja, 1 Zeile** | Flag-Bedingung erweitern |

**Fazit:** Statt 3 Core-Patches brauchen wir nur 1. Das reduziert die Merge-Konflikt-Flaeche um 66%.

---

## EnterpriseSettings Interface (Frontend-Vertrag)

Das Backend MUSS exakt dieses Interface bedienen (`web/src/interfaces/settings.ts:98-117`):

```typescript
export interface EnterpriseSettings {
  application_name: string | null;          // App-Name (z.B. "VoeB Chatbot")
  use_custom_logo: boolean;                  // Ob Custom Logo aktiv ist
  use_custom_logotype: boolean;              // Ob Custom Logotype aktiv ist
  logo_display_style:                        // Wie Logo angezeigt wird
    | "logo_and_name"                        //   Logo + Name nebeneinander
    | "logo_only"                            //   Nur Logo
    | "name_only"                            //   Nur Name
    | null;
  custom_nav_items: NavigationItem[];        // Custom Navigation (Array)
  custom_lower_disclaimer_content: string | null;  // Disclaimer unter Chat
  custom_header_content: string | null;      // Custom Chat-Header Text
  two_lines_for_chat_header: boolean | null; // Zweizeiliger Chat-Header
  custom_popup_header: string | null;        // Willkommens-Popup Titel
  custom_popup_content: string | null;       // Willkommens-Popup Body (Markdown)
  enable_consent_screen: boolean | null;     // Consent-Checkbox im Popup
  consent_screen_prompt: string | null;      // Text fuer Consent
  show_first_visit_notice: boolean | null;   // Popup beim ersten Besuch
  custom_greeting_message: string | null;    // Begruessung im Chat
}

export interface NavigationItem {
  link: string;
  icon?: string;
  svg_logo?: string;
  title: string;
}
```

---

## API-Spezifikation

### Uebersicht der Endpoints

| # | Pfad | Methode | Auth | Beschreibung |
|---|------|---------|------|-------------|
| 1 | `/enterprise-settings` | GET | `current_user` | Branding-Config lesen |
| 2 | `/enterprise-settings/logo` | GET | `current_user` | Logo-Bild abrufen |
| 3 | `/admin/enterprise-settings` | GET | `current_admin_user` | Admin: Config lesen |
| 4 | `/admin/enterprise-settings` | PUT | `current_admin_user` | Admin: Config aendern |
| 5 | `/admin/enterprise-settings/logo` | PUT | `current_admin_user` | Admin: Logo hochladen |

> **Hinweis**: Die Pfade werden ueber `include_router_with_global_prefix_prepended()` mit `/api` Prefix registriert. Frontend-Aufrufe gehen an `/api/enterprise-settings` (Browser) bzw. `{INTERNAL_URL}/enterprise-settings` (SSR).

---

### Endpoint 1: GET `/enterprise-settings`

**Zweck:** Frontend-Komponenten laden Branding-Konfiguration beim Seitenaufbau (SSR + CSR).

**Auth:** `current_user` (authentifizierter User, jede Rolle)

**Response (200 OK):**

```json
{
  "application_name": "VoeB Chatbot",
  "use_custom_logo": true,
  "use_custom_logotype": false,
  "logo_display_style": "logo_and_name",
  "custom_nav_items": [],
  "custom_lower_disclaimer_content": null,
  "custom_header_content": "Bundesverband Oeffentlicher Banken",
  "two_lines_for_chat_header": false,
  "custom_popup_header": "Willkommen beim VoeB Chatbot",
  "custom_popup_content": "Dieser Chatbot unterstuetzt Sie bei der taeglichen Arbeit.",
  "enable_consent_screen": false,
  "consent_screen_prompt": null,
  "show_first_visit_notice": true,
  "custom_greeting_message": "Wie kann ich Ihnen helfen?"
}
```

**Fehlerfaelle:**

| HTTP | Wann | Response |
|------|------|----------|
| 200 | Config existiert | EnterpriseSettings JSON |
| 200 | Config existiert nicht | Default-Werte (Onyx-Defaults) |
| 401 | Nicht authentifiziert | `{"detail": "Not authenticated"}` |

> **Design-Entscheidung:** Kein 404, sondern immer 200 mit Defaults. Das Frontend erwartet eine gueltige Response — 4xx wuerde als Fehler geloggt (siehe `lib.ts:84-91`).

---

### Endpoint 2: GET `/enterprise-settings/logo`

**Zweck:** Logo-Bild fuer Favicon, Sidebar, Login-Seite.

**Auth:** `current_user`

**Response (200 OK):** Binaere Bilddaten mit korrektem Content-Type.

```
Content-Type: image/png  (oder image/jpeg, image/svg+xml)
Content-Disposition: inline; filename="logo.png"
Body: <binaere Bilddaten>
```

**Fehlerfaelle:**

| HTTP | Wann | Response |
|------|------|----------|
| 200 | Logo vorhanden | Bilddaten |
| 404 | Kein Logo hochgeladen | `{"detail": "No custom logo configured"}` |
| 401 | Nicht authentifiziert | `{"detail": "Not authenticated"}` |

---

### Endpoint 3: GET `/admin/enterprise-settings`

**Zweck:** Admin-UI laedt aktuelle Config zur Bearbeitung.

**Auth:** `current_admin_user` (nur Admins)

**Response:** Identisch zu Endpoint 1.

**Fehlerfaelle:** Wie Endpoint 1, plus 403 bei fehlender Admin-Rolle.

---

### Endpoint 4: PUT `/admin/enterprise-settings`

**Zweck:** Admin aendert Branding-Konfiguration.

**Auth:** `current_admin_user`

**Request Body:**

```json
{
  "application_name": "VoeB Chatbot",
  "use_custom_logo": true,
  "use_custom_logotype": false,
  "logo_display_style": "logo_and_name",
  "custom_nav_items": [],
  "custom_lower_disclaimer_content": null,
  "custom_header_content": "Bundesverband Oeffentlicher Banken",
  "two_lines_for_chat_header": false,
  "custom_popup_header": "Willkommen beim VoeB Chatbot",
  "custom_popup_content": "Dieser Chatbot unterstuetzt Sie bei der taeglichen Arbeit.",
  "enable_consent_screen": false,
  "consent_screen_prompt": null,
  "show_first_visit_notice": true,
  "custom_greeting_message": "Wie kann ich Ihnen helfen?"
}
```

**Validierungsregeln (Pydantic):**

| Feld | Typ | Max-Laenge | Constraint |
|------|-----|-----------|-----------|
| `application_name` | `str \| None` | 50 | — |
| `use_custom_logo` | `bool` | — | — |
| `use_custom_logotype` | `bool` | — | — |
| `logo_display_style` | `Literal[...] \| None` | — | Enum: `logo_and_name`, `logo_only`, `name_only` |
| `custom_nav_items` | `list[NavigationItem]` | — | Max 10 Items |
| `custom_lower_disclaimer_content` | `str \| None` | 200 | — |
| `custom_header_content` | `str \| None` | 100 | — |
| `two_lines_for_chat_header` | `bool \| None` | — | — |
| `custom_popup_header` | `str \| None` | 100 | Pflicht wenn `show_first_visit_notice=true` |
| `custom_popup_content` | `str \| None` | 500 | Pflicht wenn `show_first_visit_notice=true` |
| `enable_consent_screen` | `bool \| None` | — | — |
| `consent_screen_prompt` | `str \| None` | 200 | Pflicht wenn `enable_consent_screen=true` |
| `show_first_visit_notice` | `bool \| None` | — | — |
| `custom_greeting_message` | `str \| None` | 50 | — |

> **Max-Laengen**: Uebernommen aus dem EE Admin Theme UI (`web/src/app/ee/admin/theme/page.tsx`), das diese Limits client-seitig erzwingt.

**Response (200 OK):** Kein Body (oder leerer Body).

**Fehlerfaelle:**

| HTTP | Wann | Response |
|------|------|----------|
| 200 | Erfolgreich gespeichert | — |
| 400 | Validierungsfehler | `{"detail": "application_name: max 50 characters"}` |
| 401 | Nicht authentifiziert | `{"detail": "Not authenticated"}` |
| 403 | Kein Admin | `{"detail": "Not an admin"}` |
| 500 | DB-Fehler | `{"detail": "Internal server error"}` (kein DB-Detail!) |

---

### Endpoint 5: PUT `/admin/enterprise-settings/logo`

**Zweck:** Admin laedt Logo-Bild hoch.

**Auth:** `current_admin_user`

**Request:** `multipart/form-data`

```
Content-Type: multipart/form-data
Body: file=<binaere Bilddaten>
```

**Validierung:**

| Regel | Wert | Grund |
|-------|------|-------|
| Max Dateigroesse | 2 MB | Performance, DB-Speicher |
| Erlaubte Formate | PNG, JPEG | Browser-Kompatibilitaet |
| Erlaubte MIME-Types | `image/png`, `image/jpeg` | Sicherheit |

> **Sicherheit:** MIME-Type wird serverseitig anhand von Magic Bytes validiert, NICHT nur anhand der File-Extension. Verhindert Upload von als Bild getarnten Dateien. SVG ist bewusst ausgeschlossen (XSS-Risiko im Bankenumfeld, siehe OPEN-9).

**Response (200 OK):** Kein Body (oder leerer Body).

**Fehlerfaelle:**

| HTTP | Wann | Response |
|------|------|----------|
| 200 | Upload erfolgreich | — |
| 400 | Datei zu gross / falsches Format | `{"detail": "Logo must be PNG or JPEG and under 2MB"}` |
| 401 | Nicht authentifiziert | `{"detail": "Not authenticated"}` |
| 403 | Kein Admin | `{"detail": "Not an admin"}` |

---

## Datenbankschema

### Tabelle: `ext_branding_config`

**Design:** Single-Row-Tabelle (Singleton-Pattern). Es gibt genau eine Branding-Konfiguration pro Instanz (VoeB = Single-Tenant). Die Row wird bei erstem PUT erstellt (Upsert).

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|-------------|
| `id` | `Integer` | `PRIMARY KEY` | Immer 1 (Singleton) |
| `application_name` | `String(50)` | `NULLABLE` | App-Name ("VoeB Chatbot") |
| `use_custom_logo` | `Boolean` | `NOT NULL, DEFAULT false` | Custom Logo aktiviert? |
| `use_custom_logotype` | `Boolean` | `NOT NULL, DEFAULT false` | Custom Logotype aktiviert? |
| `logo_display_style` | `String(20)` | `NULLABLE` | "logo_and_name", "logo_only", "name_only" |
| `custom_nav_items_json` | `Text` | `NULLABLE` | JSON-Array von NavigationItem |
| `custom_lower_disclaimer_content` | `String(200)` | `NULLABLE` | Disclaimer-Text |
| `custom_header_content` | `String(100)` | `NULLABLE` | Chat-Header-Text |
| `two_lines_for_chat_header` | `Boolean` | `NULLABLE` | Zweizeiliger Header? |
| `custom_popup_header` | `String(100)` | `NULLABLE` | Popup-Titel |
| `custom_popup_content` | `String(500)` | `NULLABLE` | Popup-Body (Markdown) |
| `enable_consent_screen` | `Boolean` | `NULLABLE` | Consent-Screen? |
| `consent_screen_prompt` | `String(200)` | `NULLABLE` | Consent-Text |
| `show_first_visit_notice` | `Boolean` | `NULLABLE` | Erster-Besuch-Popup? |
| `custom_greeting_message` | `String(50)` | `NULLABLE` | Chat-Begruessung |
| `logo_data` | `LargeBinary` | `NULLABLE` | Logo als Binaerdaten (max 2MB) |
| `logo_content_type` | `String(50)` | `NULLABLE` | MIME-Type des Logos |
| `logo_filename` | `String(255)` | `NULLABLE` | Original-Dateiname |
| `created_at` | `DateTime` | `NOT NULL, DEFAULT now()` | Erstellt am |
| `updated_at` | `DateTime` | `NOT NULL, DEFAULT now()` | Letzte Aenderung |

### Warum Logo in der Datenbank?

| Option | Pro | Contra |
|--------|-----|--------|
| **DB (BLOB)** ✅ | Einfach, funktioniert ueber Pod-Restarts, keine extra Infrastruktur | Groessere DB, nicht ideal fuer grosse Dateien |
| Filesystem | Einfach | Ephemeral Pods → Datenverlust nach Restart |
| Object Storage (S3) | Skalierbar | Extra Komplexitaet, StackIT S3 Credentials noetig |

**Entscheidung:** DB-BLOB fuer MVP. Logo ist max 2MB, wird selten geschrieben, haeufig gelesen. Bei Bedarf kann spaeter ein Cache (Redis) vorgeschaltet werden. Fuer VoeB (Single-Tenant, <200 User) absolut ausreichend.

### Migration

```bash
# Im Standard-Onyx-Alembic (kein separater Branch)
alembic revision -m "ext_branding: Create ext_branding_config table"
```

Migration-Script erstellt die Tabelle. Keine Aenderung an bestehenden Onyx-Tabellen.

### Indizes

Keine zusaetzlichen Indizes noetig — Single-Row-Tabelle, Primary Key reicht.

---

## Betroffene Core-Dateien

### CORE #6: `web/src/lib/constants.ts` — EINZIGE Aenderung

**Was wird geaendert:**

Zeile 48-51 (aktuelle Version):
```typescript
export const SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED =
  process.env.ENABLE_PAID_ENTERPRISE_EDITION_FEATURES?.toLowerCase() ===
    "true" ||
  process.env.LICENSE_ENFORCEMENT_ENABLED?.toLowerCase() !== "false";
```

Wird zu:
```typescript
export const SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED =
  process.env.ENABLE_PAID_ENTERPRISE_EDITION_FEATURES?.toLowerCase() ===
    "true" ||
  process.env.LICENSE_ENFORCEMENT_ENABLED?.toLowerCase() !== "false" ||
  process.env.EXT_BRANDING_ENABLED?.toLowerCase() === "true";
```

**Warum:**
- Dieses Flag steuert, ob `fetchSettingsSS()` die `/enterprise-settings` Daten laedt
- Wird in `layout.tsx` und `lib.ts` server-seitig geprueft
- Wenn `EXT_BRANDING_ENABLED=true`, soll das Frontend unsere Branding-Daten laden
- KEIN EE-Code wird aktiviert — die Variable steuert nur das Fetching

**Seiteneffekte der CORE #6 Aenderung:**

Die Variable `SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED` wird an 7 Stellen im Frontend referenziert. Durch den Wechsel auf `true` ergeben sich folgende Effekte:

| Datei | Was passiert | Risiko |
|-------|-------------|--------|
| `lib.ts:34` | `fetchEnterpriseSettingsSS()` wird aufgerufen → laedt Branding-Config | ✅ Gewuenscht |
| `layout.tsx:50` | `generateMetadata()` fetcht Enterprise-Settings fuer Titel/Favicon | ✅ Gewuenscht |
| `ee/layout.tsx:11` | Build-Time Guard wird bestanden (Check 1 von 2) — Check 2 (`ee_features_enabled=false`) blockiert weiterhin | ✅ Kein EE-Zugang |
| `proxy.ts:82-86` | EE-Routes (`/admin/groups`, `/admin/theme`, etc.) werden zu `/ee/...` rewritten | ⚠️ Harmlos — Routen nicht ueber UI erreichbar, Guard blockiert |
| `admin/Layout.tsx:26` | `enableEnterprise=true` an ClientLayout — aber `AdminSidebar.tsx:197` ueberschreibt mit Runtime-Hook (`usePaidEnterpriseFeaturesEnabled()` → `false`) | ✅ EE-Sidebar-Items BLEIBEN VERSTECKT |
| `getStandardAnswerCategoriesIfEE.tsx:22` | API-Call an `/manage/admin/standard-answer/category` wird versucht → 404 → silently caught | ⚠️ Harmlos — kein User-Impact, nur unnoetige Request |
| `lib.ts:36-38` | `CUSTOM_ANALYTICS_ENABLED` wird geprueft → nur wenn `CUSTOM_ANALYTICS_SECRET_KEY` gesetzt ist (ist es nicht) | ✅ Kein Seiteneffekt |

**Keine unerwuenschten Seiteneffekte:**
- `EE_ENABLED` (separate Variable, Zeile 56-57) wird NICHT veraendert
- Backend-seitig: `ENABLE_PAID_ENTERPRISE_EDITION_FEATURES` bleibt `false` → kein EE-Code im Backend aktiviert
- Admin-Sidebar: EE-Items (Groups, SCIM, Theme, etc.) bleiben VERSTECKT — kontrolliert durch Runtime-Hook, nicht Build-Time-Flag
- EE-Seiten (`/ee/admin/*`): Guard blockiert Zugriff (Runtime-Check `ee_features_enabled=false`)

> **Hinweis zu EE-Code:** Wir nutzen KEINE EE-Features und bauen alles custom in `ext/` nach. Der EE-Code in `web/src/app/ee/` und `web/src/ee/` bleibt unangetastet (Extend, don't modify). Er ist durch Runtime-Gates deaktiviert und wird bei Upstream-Merges nicht zu Konflikten fuehren.

**Backup (alle 3 Core-Patches):**
```bash
mkdir -p backend/ext/_core_originals/

# CORE #6: constants.ts
cp web/src/lib/constants.ts backend/ext/_core_originals/constants.ts.original
# Nach Aenderung:
diff -u backend/ext/_core_originals/constants.ts.original web/src/lib/constants.ts \
  > backend/ext/_core_originals/constants.ts.patch

# CORE #8: LoginText.tsx
cp web/src/app/auth/login/LoginText.tsx backend/ext/_core_originals/LoginText.tsx.original
# Nach Aenderung:
diff -u backend/ext/_core_originals/LoginText.tsx.original web/src/app/auth/login/LoginText.tsx \
  > backend/ext/_core_originals/LoginText.tsx.patch

# CORE #9: AuthFlowContainer.tsx
cp web/src/components/auth/AuthFlowContainer.tsx backend/ext/_core_originals/AuthFlowContainer.tsx.original
# Nach Aenderung:
diff -u backend/ext/_core_originals/AuthFlowContainer.tsx.original web/src/components/auth/AuthFlowContainer.tsx \
  > backend/ext/_core_originals/AuthFlowContainer.tsx.patch
```

> **Upstream-Merge:** Bei Konflikten in diesen 3 Dateien: Upstream-Version uebernehmen (`git checkout --theirs`), `.original` aktualisieren, Patch neu anwenden (`patch -p0 < *.patch`), `.patch` regenerieren. Details: `fork-management.md` Schritt 5.

### CORE #4 (`layout.tsx`) — NICHT noetig

`generateMetadata()` (Zeile 47-65) prueft bereits `SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED` und fetcht automatisch `/enterprise-settings`. Durch die CORE #6 Aenderung wird dieses Flag true → `layout.tsx` funktioniert ohne Aenderung.

### CORE #5 (`header/`) — NICHT noetig

`Logo.tsx` und `HeaderTitle.tsx` lesen aus dem `SettingsProvider` Context, der durch `fetchSettingsSS()` befuellt wird. Keine Aenderung noetig.

### Sicherheitsnachweis: Keine unbeabsichtigte EE-Aktivierung

Die CORE #6 Aenderung setzt `SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED = true`. EE-UI-Features werden NICHT aktiviert — verifiziert durch 3 unabhaengige Gates:

**Gate 1: `usePaidEnterpriseFeaturesEnabled()` Runtime-Hook**
(`web/src/components/settings/usePaidEnterpriseFeaturesEnabled.ts:17-29`)

```typescript
export function usePaidEnterpriseFeaturesEnabled(): boolean {
  const combinedSettings = useSettingsContext();
  if (combinedSettings.settings.ee_features_enabled !== undefined) {
    return combinedSettings.settings.ee_features_enabled;  // → false
  }
  return combinedSettings.enterpriseSettings !== null;  // Fallback
}
```

- Backend sendet `ee_features_enabled: false` (Pydantic Default in `Settings` Model, `backend/onyx/server/settings/models.py:68`)
- `false !== undefined` → erster Branch greift → gibt `false` zurueck
- Fallback auf `enterpriseSettings !== null` wird nicht erreicht solange Backend `ee_features_enabled` sendet
- Alle Frontend-Stellen die diesen Hook nutzen bekommen `false` → EE-UI bleibt deaktiviert ✅
- Admin-Sidebar (`AdminSidebar.tsx:197`) nutzt diesen Hook → EE-Items (Groups, SCIM, Theme, etc.) werden NICHT angezeigt ✅

> **Hinweis:** `ee_features_enabled` ist ein Backend-Setting das theoretisch per Admin-API (`PUT /admin/settings`) geaendert werden koennte. In der Praxis ist das kein Risiko: (1) Nur Admins haben Zugriff, (2) `backend/ee/` ist LEER — EE-Backend-Funktionalitaet existiert nicht, (3) EE-Admin-Seiten wuerden rendern aber Speichern schlaegt fehl (kein Backend). Dieses Risiko ist NICHT neu durch CORE #6 — es existiert in der FOSS-Codebase unabhaengig von unserer Aenderung.

**Gate 2: EE Layout Guard**
(`web/src/app/ee/layout.tsx:11-29`)

```typescript
// Check 1: Build-Time Flag (nach CORE #6 = true → Check wird BESTANDEN)
if (!SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED) {
    return <EEFeatureRedirect />;
}

// Check 2: Runtime Backend-Flag (ee_features_enabled = false → REDIRECT)
if (settings.ee_features_enabled === false) {
    return <EEFeatureRedirect />;  // ← Dieser Check greift!
}
```

- Nach CORE #6 wird Check 1 bestanden (Build-Time Flag = true)
- Check 2 blockiert weiterhin: `ee_features_enabled = false` → Redirect auf `/app` mit Toast-Meldung
- Selbst wenn jemand direkt `/ee/admin/theme` aufruft → Redirect ✅

**Gate 3: Backend EE-Logik** (unabhaengig von Frontend)
(`backend/onyx/utils/variable_functionality.py`)

- `ENTERPRISE_EDITION_ENABLED` bleibt `false` im Backend (gesteuert durch eigene Env-Var, NICHT durch Frontend-Flag)
- 272 `ee.onyx.*`-Referenzen fallen weiterhin auf FOSS-Defaults zurueck ✅
- `backend/ee/` ist LEER (nur `__init__.py`) — kein EE-Code vorhanden

**Ergebnis:** CORE #6 Aenderung aktiviert NUR das Fetching der Enterprise-Settings (Branding-Daten). EE-Features sind durch Runtime-Gates deaktiviert. Kein EE-Feature wird sichtbar oder nutzbar.

---

### Zusaetzliche Core-Aenderungen: Login-Seite (OPEN-8 — Niko entscheidet)

Fuer vollstaendiges Whitelabel auf der Login-Seite sind 2 weitere Dateien betroffen. Diese sind NICHT in der aktuellen Core-Liste und brauchen Nikos Freigabe:

**`web/src/app/auth/login/LoginText.tsx`** — Login Tagline

Zeile 15-17 (aktuell):
```tsx
<Text as="p" text03 mainUiMuted>
  Your open source AI platform for work
</Text>
```

Aenderung: Tagline aus `enterpriseSettings` lesen oder komplett entfernen:
```tsx
{settings?.enterpriseSettings?.custom_header_content && (
  <Text as="p" text03 mainUiMuted>
    {settings.enterpriseSettings.custom_header_content}
  </Text>
)}
```

> Nutzt das bestehende `custom_header_content` Feld aus EnterpriseSettings. Kein neues DB-Feld noetig. Wenn nicht gesetzt → keine Tagline angezeigt (sauberer als "open source AI platform").

**`web/src/components/auth/AuthFlowContainer.tsx`** — Login Icon + "New to Onyx?"

Zeile 16: `OnyxIcon` als Login-Icon → Custom Logo verwenden
Zeile 23: `New to Onyx?` → `application_name` nutzen oder generisch "New here?"

> Diese Datei braucht Zugriff auf den SettingsContext. Da AuthFlowContainer aktuell KEIN Client-Component mit SettingsContext ist, muesste es erweitert werden. Alternative: Text statisch aendern ("New here?" statt "New to Onyx?").

---

## Feature Flag Verhalten

### `EXT_BRANDING_ENABLED=false` (Default)

- Backend: Branding-Router wird NICHT registriert (Gate in `register_ext_routers()`)
- Frontend: `SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED` bleibt `false` (sofern nicht durch andere Flags aktiviert)
- Ergebnis: `enterpriseSettings = null`, alle Komponenten zeigen Onyx-Defaults
- **Seiteneffekte: Keine. Onyx laeuft exakt wie ohne ext-branding.**

### `EXT_BRANDING_ENABLED=true` (+ `EXT_ENABLED=true`)

- Backend: Branding-Router registriert auf `/enterprise-settings` + `/admin/enterprise-settings`
- Frontend: Flag wird true → `fetchSettingsSS()` fetcht `/enterprise-settings`
- Ergebnis: `enterpriseSettings` wird mit VoeB-Branding befuellt
- Wenn noch keine Config in DB: Default-Werte (application_name=null → Frontend zeigt "Onyx" bis Admin konfiguriert)

### Env-Variablen die gesetzt werden muessen

| Variable | Wo | Wert |
|----------|----|----|
| `EXT_ENABLED` | Backend (api_server) + Frontend (web_server) | `true` |
| `EXT_BRANDING_ENABLED` | Backend (api_server) + Frontend (web_server) | `true` |

> **Wichtig:** `EXT_BRANDING_ENABLED` muss BEIDEN Services zur Verfuegung stehen — dem Python-Backend (fuer Router-Registrierung) UND dem Next.js-Frontend (fuer das Flag in `constants.ts`).

---

## Neue Dateien

### Backend

```
backend/ext/
  ├── models/
  │   ├── __init__.py
  │   └── branding.py              ← SQLAlchemy Model: ExtBrandingConfig
  ├── schemas/
  │   ├── __init__.py
  │   └── branding.py              ← Pydantic Schemas: Request/Response
  ├── services/
  │   ├── __init__.py
  │   └── branding.py              ← Business Logic: CRUD, Logo-Handling
  ├── routers/
  │   └── branding.py              ← FastAPI Router: 5 Endpoints
  └── _core_originals/
      ├── main.py.original              ← Backup von CORE #1 (Phase 4a, existiert bereits)
      ├── main.py.patch                 ← Diff (Phase 4a, existiert bereits)
      ├── constants.ts.original         ← Backup von CORE #6
      ├── constants.ts.patch            ← Diff
      ├── LoginText.tsx.original        ← Backup von CORE #8
      ├── LoginText.tsx.patch           ← Diff
      ├── AuthFlowContainer.tsx.original ← Backup von CORE #9
      └── AuthFlowContainer.tsx.patch   ← Diff
```

### Frontend

```
web/src/ext/
  └── pages/
      └── admin/
          └── branding/
              └── page.tsx           ← Admin-UI fuer Branding-Verwaltung
```

> **Admin-UI Navigation:** Die Seite ist unter `/ext/admin/branding` erreichbar. Ein Link dorthin kann aus dem ext-Health-Dashboard oder der Admin-Sidebar verlinkt werden. Die Admin-Sidebar (Onyx-Core) wird in Phase 4b NICHT veraendert — Zugang erfolgt ueber direkte URL oder ext-Dashboard.

### Alembic Migration

```
backend/alembic/versions/
  └── xxxx_ext_branding_create_ext_branding_config.py
```

---

## Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Logo.tsx     │  │ layout.tsx   │  │ ext Admin Branding UI │  │
│  │ (FOSS, liest │  │ (FOSS, liest │  │ (NEU, in web/src/ext) │  │
│  │  aus Context) │  │  aus Context) │  │                       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘  │
│         │                  │                       │              │
│         └──────────┬───────┘                       │              │
│                    ▼                               │              │
│         ┌──────────────────┐                       │              │
│         │ SettingsProvider  │                       │              │
│         │ (enterpriseSettings)                     │              │
│         └──────────┬───────┘                       │              │
│                    │                               │              │
└────────────────────┼───────────────────────────────┼──────────────┘
                     │ SSR: fetchSS(                 │ PUT /api/admin/
                     │ "/enterprise-settings")       │ enterprise-settings
                     ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ext/routers/branding.py                                   │   │
│  │                                                            │   │
│  │  GET  /enterprise-settings          → branding_service     │   │
│  │  GET  /enterprise-settings/logo     → branding_service     │   │
│  │  GET  /admin/enterprise-settings    → branding_service     │   │
│  │  PUT  /admin/enterprise-settings    → branding_service     │   │
│  │  PUT  /admin/enterprise-settings/logo → branding_service   │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ext/services/branding.py                                  │   │
│  │  - get_branding_config(db) → ExtBrandingConfig            │   │
│  │  - update_branding_config(db, data) → None                │   │
│  │  - get_logo(db) → bytes + content_type                    │   │
│  │  - update_logo(db, file) → None                           │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL: ext_branding_config (Singleton-Row)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fehlerbehandlung

| Fehlerfall | HTTP | Strategie |
|-----------|------|-----------|
| Feature Flag deaktiviert | 404 | Router nicht registriert, FastAPI gibt 404 |
| User nicht authentifiziert | 401 | Onyx Auth-Middleware |
| User nicht Admin (bei /admin/) | 403 | Onyx Auth-Middleware |
| DB-Config nicht vorhanden (GET) | 200 | Default-Werte zurueckgeben |
| DB-Fehler (GET/PUT) | 500 | Loggen, generische Fehlermeldung |
| Logo zu gross (>2MB) | 400 | Vor DB-Schreiben validieren |
| Logo falsches Format | 400 | MIME-Type + Magic-Byte Validierung |
| Ungueltige JSON-Felder (PUT) | 422 | Pydantic Validierungsfehler |
| `show_first_visit_notice=true` aber kein `custom_popup_header` | 400 | Geschaeftsregel-Validierung |

### Logging

| Level | Event | Logger |
|-------|-------|--------|
| `INFO` | Branding-Config aktualisiert | `ext.branding` |
| `INFO` | Logo hochgeladen (Groesse, Format) | `ext.branding` |
| `WARNING` | Logo-Upload mit ungueltigem Format abgelehnt | `ext.branding` |
| `ERROR` | DB-Fehler bei Config-Operation | `ext.branding` |

> **DSGVO:** Keine personenbezogenen Daten in Logs. User-ID wird NICHT geloggt (Branding ist global, nicht user-spezifisch).

---

## Performance

| Operation | Erwartete Dauer | Anmerkung |
|-----------|----------------|-----------|
| GET /enterprise-settings | < 10ms | Single-Row DB-Read |
| GET /enterprise-settings/logo | < 50ms | BLOB-Read (max 2MB) |
| PUT /admin/enterprise-settings | < 50ms | Single-Row Upsert |
| PUT /admin/enterprise-settings/logo | < 200ms | BLOB-Write (max 2MB) |

**Caching-Ueberlegung:** GET `/enterprise-settings` wird bei JEDEM Seitenaufruf (SSR) aufgerufen. Bei 150 Usern (VoeB-Szenario) ist das ~150 Requests/Minute in Spitzenzeiten. Ein In-Memory-Cache (TTL 60s) in Python waere sinnvoll, ist aber fuer MVP nicht noetig. Die DB-Query auf eine einzelne Row ist ausreichend performant.

---

## Tests

### Unit Tests (`backend/ext/tests/test_branding.py`)

| Test | Beschreibung |
|------|-------------|
| `test_branding_config_defaults` | Wenn keine Config in DB, werden Default-Werte zurueckgegeben |
| `test_branding_config_roundtrip` | PUT Config → GET Config → gleiche Werte |
| `test_logo_validation_size` | Logo >2MB wird abgelehnt (400) |
| `test_logo_validation_format` | Nicht-Bild wird abgelehnt (400) |
| `test_logo_magic_bytes` | MIME-Type-Spoofing wird erkannt |
| `test_popup_requires_header` | `show_first_visit_notice=true` ohne `custom_popup_header` → 400 |
| `test_consent_requires_prompt` | `enable_consent_screen=true` ohne `consent_screen_prompt` → 400 |
| `test_application_name_max_length` | >50 Zeichen wird abgelehnt |
| `test_logo_display_style_enum` | Ungueltiger Wert wird abgelehnt |

### Feature Flag Tests (`backend/ext/tests/test_branding_flag.py`)

| Test | Beschreibung |
|------|-------------|
| `test_endpoints_not_registered_when_disabled` | `EXT_BRANDING_ENABLED=false` → 404 auf alle Endpoints |
| `test_endpoints_registered_when_enabled` | `EXT_BRANDING_ENABLED=true` → Endpoints antworten |

### Integration Tests (wenn Onyx laeuft)

| Test | Beschreibung |
|------|-------------|
| `test_full_branding_flow` | Login → PUT Config → GET Config → Verifiziere Werte |
| `test_logo_upload_and_serve` | Upload PNG → GET Logo → Verifiziere Content-Type + Groesse |
| `test_non_admin_cannot_modify` | Normal-User → PUT → 403 |

---

## Branding-Audit: Wo erscheint "Onyx" fuer den Endnutzer?

Vollstaendige Analyse aller Stellen im Frontend, an denen ein Nutzer "Onyx"-Branding sehen wuerde.

### Kategorie 1: Durch EnterpriseSettings KONTROLLIERT (funktioniert automatisch)

Diese Stellen werden automatisch ersetzt, sobald ext-branding aktiv ist und der Admin die Config setzt:

| # | Stelle | Datei | Feld | Verhalten |
|---|--------|-------|------|-----------|
| 1 | **Page Title** (Browser-Tab) | `layout.tsx:59` | `application_name` | Zeigt App-Name statt "Onyx" |
| 2 | **Favicon** | `layout.tsx:52-55` | `use_custom_logo` | Custom Logo als Favicon |
| 3 | **Sidebar Logo** | `Logo.tsx` | `use_custom_logo`, `logo_display_style` | Custom Logo + Name |
| 4 | **Login Begruessung** | `LoginText.tsx:12-13` | `application_name` | "Welcome to {Name}" |
| 5 | **Chat Begruessung** | `WelcomeMessage.tsx:31-32` | `custom_greeting_message` | Custom Greeting statt Random |
| 6 | **Chat Footer** | `app-layouts.tsx:460-464` | `custom_lower_disclaimer_content` | Custom Footer statt "Onyx - Open Source AI Platform" |
| 7 | **Willkommens-Popup Titel** | `AppPopup.tsx:79` | `custom_popup_header` | Custom Titel statt "Welcome to Onyx!" |
| 8 | **Willkommens-Popup Body** | `AppPopup.tsx:83` | `custom_popup_content` | Custom Inhalt (Markdown) |
| 9 | **Chat Header** | diverse | `custom_header_content` | Custom Header-Text |
| 10 | **Lade-Bildschirm** | `OnyxInitializingLoader.tsx:14` | `application_name` | "Initializing {Name}" |
| 11 | **Consent-Screen** | `AppPopup.tsx` | `enable_consent_screen`, `consent_screen_prompt` | Custom Consent-Text |

### Kategorie 2: NICHT kontrolliert — User-sichtbar (KRITISCH)

Diese Stellen zeigen "Onyx" und sind NICHT ueber EnterpriseSettings steuerbar:

| # | Stelle | Datei:Zeile | Text | Sichtbarkeit | Loesung |
|---|--------|------------|------|-------------|---------|
| A | **Login Tagline** | `LoginText.tsx:16` | "Your open source AI platform for work" | Jeder User bei Login | **→ OPEN-8: Core-Liste erweitern** |
| B | **Login Icon** | `AuthFlowContainer.tsx:16` | `OnyxIcon` als Login-Logo | Jeder User bei Login | **→ OPEN-8: Core-Liste erweitern** |
| C | **Login Footer** | `AuthFlowContainer.tsx:23` | "New to Onyx?" | Jeder User auf Login-Seite | **→ OPEN-8: Core-Liste erweitern** |
| D | **Account-Seite** | `create-account/page.tsx:17-22` | "To access Onyx...", "Onyx team" (3x) | Nur bei fehlendem Account | Edge Case (VoeB hat Entra ID) |
| E | **Auth Error E-Mail** | `auth/error/page.tsx:47-50` | "Onyx team at support@onyx.app" + E-Mail-Link | Nur bei Auth-Fehler | Edge Case |
| F | **Chat Placeholder** | `SharedAppInputBar.tsx:21` | "How can Onyx help you today" | Skelett-Zustand beim Laden | Gering (kurz sichtbar) |
| G | **Error Page Text** | `ErrorPage.tsx:17` | "problem loading your Onyx settings" | User bei Fehler | Edge Case |
| H | **Error Page Logo** | `ErrorPageLayout.tsx:11` | `OnyxLogoTypeIcon` | User bei Fehler | Edge Case |
| I | **Meta Description** | `layout.tsx:61` | "Question answering for your documents" | Browser-Tooltip, SEO | Gering (internes Tool) |
| J | **Health Banner** | `AppHealthBanner.tsx:223` | "you just updated your Onyx deployment" | Admins bei Backend-Problemen | Admin-only |
| K | **Onboarding "Name"** | `NameStep.tsx:50` | "What should Onyx call you?" | Erster Login, einmalig | Einmal sichtbar |
| K2 | **Onboarding "Name" (Non-Admin)** | `NonAdminStep.tsx:97` | "What should Onyx call you?" (Duplikat) | Erster Login, einmalig | Einmal sichtbar |
| L | **Cloud Error** | `CloudErrorPage.tsx:12` | "Onyx is currently in maintenance" | Nie (Cloud-Feature) | Irrelevant |
| M | **Agent Owner Fallback** | `AgentCard.tsx:203`, `AgentViewerModal.tsx:263` | `|| "Onyx"` als Fallback fuer ownerlosen Agent | User sieht "Onyx" bei Agents ohne Owner | Gering (selten) |

### Kategorie 3: NICHT kontrolliert — Admin-only (NIEDRIG)

| # | Stelle | Datei | Text |
|---|--------|-------|------|
| I | LLM Config | `LLMConfigurationPage.tsx:365,445` | "used by Onyx by default", "Onyx supports..." |
| J | Chat Preferences | `ChatPreferencesPage.tsx:364,696` | "how Onyx should behave", "how long Onyx should retain" |
| K | Connector Descriptions | `connectors.tsx:425-517` | "allow Onyx to index...", "Onyx skips files..." (6+ Stellen) |
| L | Settings Page | `SettingsPage.tsx:877-1471` | "Let Onyx reference/generate memories", "lose access to Onyx" |
| M | Memories | `Memories.tsx:27` | "memory that Onyx should remember" |
| N | Onboarding Forms | `AzureOnboardingForm.tsx:171`, `BedrockOnboardingForm.tsx:206` | "used by Onyx by default", "Onyx will use the IAM role..." |
| O | Announcement Banner | `AnnouncementBanner.tsx:83` | "continue using Onyx" |
| P | OnyxBot Slack | `bots/[bot-id]/channels/new/page.tsx:55` | "Configure OnyxBot for Slack Channel" |

### Kategorie 5: VoeB-IRRELEVANT (nicht im Scope)

Folgende Stellen enthalten "Onyx"-Branding, sind aber fuer VoeB komplett irrelevant (Features die nicht genutzt werden):

| # | Stelle | Datei | Grund |
|---|--------|-------|-------|
| NRF-1 | NRF Chrome Extension | `NRFPage.tsx:559,560,582` | "Turn off Onyx new tab page?", "Welcome to Onyx" — VoeB nutzt keine Chrome Extension |
| NRF-2 | NRF Footer | `NRFChrome.tsx:75` | "Onyx - Open Source AI Platform" — Chrome Extension |
| CRAFT-1 | Craft Module | `craft/v1/configure/page.tsx:375` | "Configure Onyx Craft" — VoeB nutzt kein Craft |
| CRAFT-2 | Craft E-Mail | `RequestConnectorModal.tsx:184,187` | `hello@onyx.app` — Craft-spezifisch |
| CLOUD-1 | Cloud Error | `CloudErrorPage.tsx:12` | "Onyx is currently in maintenance" — Cloud-Feature, nicht Self-Hosted |
| CLOUD-2 | Billing | `billing/page.tsx:43`, `PlansView.tsx:28` | `support@onyx.app`, Onyx Sales-URL — Cloud Billing |
| CLOUD-3 | Lizenz-Seite | `AccessRestrictedPage.tsx:170-171` | `support@onyx.app` — Lizenz/Billing-Fehler (LICENSE_ENFORCEMENT_ENABLED=false) |

> **Entscheidung:** Diese Stellen werden NICHT angepasst. VoeB nutzt weder NRF, Craft, noch Cloud-Billing. Die Dateien bleiben unangetastet (Extend, don't modify).

### Kategorie 4: Statische Assets

| Asset | Pfad | Status |
|-------|------|--------|
| `onyx.ico` | `web/public/onyx.ico` | Ersetzt durch Custom Logo wenn `use_custom_logo=true` |
| `logo.svg` | `web/public/logo.svg` | Nicht mehr sichtbar wenn Custom Logo aktiv |
| `logo.png` | `web/public/logo.png` | Nicht mehr sichtbar wenn Custom Logo aktiv |
| `logotype*.png` | `web/public/logotype*.png` | Fallback-Logotype |
| `logo-dark.png` | `web/public/logo-dark.png` | Dark-Mode Fallback |
| `SlabLogo.png` | `web/public/SlabLogo.png` | Connector-Icon (nicht Branding) |

### Bewertung und Empfehlung

**Kategorien 1 + 4 (automatisch kontrolliert):** 11 Stellen — alle abgedeckt durch ext-branding. ✅

**Kategorie 2 — Login-Seite (A-C):** KRITISCH — jeder User sieht das bei jedem Login.
- **Loesung:** `LoginText.tsx` + `AuthFlowContainer.tsx` zur Core-Liste hinzufuegen → **OPEN-8**
- Niko hat bestaetigt: "Komplett raus. Alles was mit Onyx, Open Source zu tun hat."

**Kategorie 2 — Rest (D-N):** GERING bis IRRELEVANT
- **D (Account-Seite):** VoeB nutzt Entra ID, nicht Self-Service-Registrierung. Seite wird nicht erreicht.
- **E, N (Auth Error / Billing E-Mail):** `support@onyx.app` in Fehlermeldungen. Edge Case — nur bei Server-Problemen sichtbar.
- **F (Chat Placeholder):** Nur im Skelett-Zustand waehrend Laden (~0.5s). Regulaere User sehen den echten AppInputBar.
- **G-H (Error Pages):** Nur bei Server-Problemen sichtbar. Edge Case.
- **I (Meta Description):** Internes Tool, kein SEO. Koennte in CORE #4 angepasst werden (niedrige Prioritaet).
- **J:** Admin-only (Health Banner bei Backend-Problemen).
- **K, K2 (Onboarding):** Einmalig beim allerersten Login. 2 Dateien mit identischem Text.
- **L:** Cloud-Feature, nicht Self-Hosted. Irrelevant.
- **M (Agent Owner Fallback):** `|| "Onyx"` als Fallback fuer ownerlosen Agent. Gering — selten, nur bei System-Agents.

**Kategorie 3 (Admin-only):** 8+ Stellen mit "Onyx" in Admin-Texten — nur Admins sehen das, generische englische Hilfetexte fuer LLM-Config, Connectors etc. Kein Handlungsbedarf.

**Kategorie 5 (VoeB-irrelevant):** NRF Chrome Extension, Craft Module, Cloud Billing — Features die VoeB nicht nutzt. Kein Handlungsbedarf.

### Priorisierung

| Prioritaet | Was | Umfang | Phase |
|-----------|-----|--------|-------|
| **P1** | EnterpriseSettings-Endpunkte + CORE #6 | 11 Stellen automatisch | 4b (jetzt) |
| **P1** | Login-Seite Whitelabel (OPEN-8) | 3 Stellen, 2 Dateien | 4b (jetzt) |
| **P3** | Error Pages, Meta Description, Agent Owner Fallback | 6 Stellen | Spaeter |
| **P4** | Admin-only Texte | 8+ Stellen | Nicht geplant |
| **—** | VoeB-irrelevante Features (NRF, Craft, Cloud) | 6 Stellen | Nicht im Scope |

---

## Geklärte Fragen

### ✅ OPEN-1: Env-Var Propagation an Next.js Web-Server — GEKLAERT

**Ergebnis:** Helm-Chart nutzt eine gemeinsame ConfigMap (`env-configmap`), die AUTOMATISCH in BEIDE Container injiziert wird (api_server UND web_server ueber `envFrom.configMapRef`).

**Beweis:**
- `deployment/helm/charts/onyx/templates/configmap.yaml` — Rendert `.Values.configMap` Dictionary
- `deployment/helm/charts/onyx/templates/api-deployment.yaml` — `envFrom: configMapRef: env-configmap`
- `deployment/helm/charts/onyx/templates/webserver-deployment.yaml` — Identisches Pattern

**Aktion:** `EXT_BRANDING_ENABLED: "true"` in `values-dev.yaml` unter `configMap:` eintragen. Beide Container erhalten die Variable automatisch. Kein separater Eintrag noetig.

**Wichtig:** `EXT_BRANDING_ENABLED` ist KEIN `NEXT_PUBLIC_`-Prefix noetig. `constants.ts` liest die Variable server-seitig (`SERVER_SIDE_ONLY__...`). Server-seitige Next.js-Variablen sind ueber ConfigMap Runtime-Env erreichbar.

---

### ✅ OPEN-2: Nur 1 statt 3 Core-Patches — GEKLAERT

**Status:** Technisch verifiziert und durch Audit bestaetigt (v0.3). CORE #4 und #5 brauchen keine Aenderung. Entwicklungsplan wird bei Implementierung aktualisiert.

---

### ✅ OPEN-3: Admin-UI Navigation — GEKLAERT

**Entscheidung:** Direkte URL fuer MVP (`/ext/admin/branding`). Admin-Sidebar-Integration spaeter wenn mehrere ext-Module Admin-UIs haben. EE-Sidebar-Items werden NICHT modifiziert — sie sind durch den Runtime-Hook (`usePaidEnterpriseFeaturesEnabled()` → `false`) bereits versteckt.

---

### ✅ OPEN-4: Logo-Cache — Implementierungs-Entscheidung

**Entscheidung:** `Cache-Control: public, max-age=3600` implementieren. Kein Blocker.

---

### ✅ OPEN-5: Favicon vs. Logo — Implementierungs-Entscheidung

**Entscheidung:** Ein Endpoint fuer beides (MVP). Browser skalieren automatisch.

---

### ✅ OPEN-6: INTERNAL_URL `/api`-Prefix — GEKLAERT

**Ergebnis:** KEIN Problem. Die Architektur funktioniert korrekt:

1. `INTERNAL_URL` = `http://onyx-dev-api-service:8080` (OHNE `/api`)
2. Backend `APP_API_PREFIX` = `""` (leer, KEIN `/api` Prefix auf Backend-Routen)
3. `fetchSS("/enterprise-settings")` → `http://api_server:8080/enterprise-settings` → Backend-Route `/enterprise-settings` ✅
4. NGINX (`nginx-conf.yaml:60-61`) stripped `/api` von Browser-Requests: `location ~ ^/(api|openapi\.json)(/.*)?$ { rewrite ^/api(/.*)$ $1 break; proxy_pass http://api_server; }`
5. Ergo: Backend-Routen haben KEINEN `/api`-Prefix. Browser-Requests an `/api/enterprise-settings` werden zu `/enterprise-settings` rewritten.

**Router-Registrierung:** `include_router_with_global_prefix_prepended()` nutzt `APP_API_PREFIX` = `""`. Unsere Route `prefix="/enterprise-settings"` wird OHNE Prefix registriert. ✅

---

### ✅ OPEN-7: EE-Backend-Aktivierung — GEKLAERT (kein Risiko)

Frontend-Aenderung (`constants.ts`) hat NULL Einfluss auf Backend. Getrennte Gates:
- Frontend: `SERVER_SIDE_ONLY__PAID_ENTERPRISE_FEATURES_ENABLED` (steuert Fetching)
- Backend: `ENTERPRISE_EDITION_ENABLED` (steuert EE-Imports) — bleibt `false`

---

## Verbleibende offene Fragen

### ✅ OPEN-8: Login-Seite Whitelabel — GEKLAERT

**Freigabe:** Niko (2026-03-08). "Alles von Onyx soll raus und komplett auf VoeB gebrandet werden."

**Aenderung:** `.claude/rules/core-dateien.md` um 2 Eintraege erweitert (7 → 9 Core-Dateien):

| # | Datei | Aenderung | Zeilen |
|---|-------|----------|--------|
| CORE #8 | `web/src/app/auth/login/LoginText.tsx` | Tagline ("Your open source AI platform for work") entfernen oder durch `custom_header_content` ersetzen | ~3 Zeilen |
| CORE #9 | `web/src/components/auth/AuthFlowContainer.tsx` | OnyxIcon durch Custom Logo ersetzen (Fallback auf OnyxIcon), "New to Onyx?" durch `application_name` ersetzen | ~5 Zeilen |

Patches folgen demselben Pattern und werden in `_core_originals/` gesichert.

---

### OPEN-9: SVG-Upload Sicherheit — Implementierungs-Entscheidung

**Problem:** SVG-Dateien koennen `<script>`-Tags und Event-Handler enthalten (XSS-Risiko). Bei Serving mit `Content-Type: image/svg+xml` fuehren Browser JavaScript in SVGs NICHT aus (nur wenn als `<object>` oder inline eingebettet). Das Logo wird als `<img src=...>` eingebettet (sicher).

**Optionen:**
- a) SVG erlauben (Browser-Sicherheit reicht fuer `<img>` Embedding)
- b) SVG ausschliessen (nur PNG + JPEG)
- c) SVG mit Sanitization erlauben (z.B. `bleach` oder eigener Parser)

**Empfehlung:** Option (b) fuer MVP — kein unnoeiges Risiko im Bankenumfeld. SVG-Support kann spaeter nachgeruestet werden.

**Verantwortlich:** Implementierungs-Entscheidung

---

## Sicherheits-Checkliste (vorab)

- [x] Alle Inputs via Pydantic Schemas validiert (Max-Laengen, Enums, Pflichtfelder)
- [x] Keine SQL-Strings aus User-Input (NUR SQLAlchemy ORM)
- [x] Logo-Upload: MIME-Type + Magic-Byte Validierung (kein Blind Trust auf Extension)
- [x] Logo-Upload: Max 2MB Limit (serverseitig enforced)
- [x] Logo-Upload: Nur PNG + JPEG erlaubt (kein SVG — XSS-Risiko im Bankenumfeld, siehe OPEN-9)
- [x] Alle Endpoints erfordern Auth (`current_user` / `current_admin_user`)
- [x] Admin-Endpoints nur fuer Admins (`current_admin_user`)
- [x] Keine personenbezogenen Daten in Logs (Branding ist global)
- [x] Keine Secrets/Tokens in Logs
- [x] HTTP-Statuscodes korrekt (400/401/403/404/422/500)
- [x] ext-Hook in Core-Datei: Feature-Flag-Gate, kein try/except noetig (reine Konstanten-Aenderung)
- [x] `custom_popup_content` erlaubt Markdown → Rendering erfolgt im Frontend mit sanitization (Onyx-Code, nicht unsere Verantwortung)
- [x] EE-Backend-Logik wird NICHT aktiviert (getrennte Gates, verifiziert → OPEN-7)
- [x] Logo-Cache: `Cache-Control: public, max-age=3600` verhindert unnoetige DB-Reads

---

## Audit-Protokoll (v0.3)

**Datum:** 2026-03-08
**Methode:** 7 parallele Tiefenanalyse-Agenten (Opus 4.6), unabhaengige Validierung jedes Aspekts

### Geprueft und bestaetigt

| Aspekt | Agent | Ergebnis |
|--------|-------|---------|
| CORE #6 Zeilen + Code exakt | #1 | ✅ 13 Referenzen in 7 Dateien geprueft |
| `EE_ENABLED` Unabhaengigkeit | #1 | ✅ Separate Env-Var, nicht betroffen |
| EE Safety Gates (3 Gates) | #2 | ✅ Mit praezisierter Formulierung (siehe Sicherheitsnachweis) |
| Fetching-Kette komplett | #3 | ✅ constants → lib.ts → SettingsProvider → Komponenten |
| Error Handling (403/401 → null) | #3 | ✅ Graceful Fallback, kein Crash |
| Backend-Routing (`APP_API_PREFIX` leer) | #4 | ✅ Kein `/api` Prefix auf Backend-Routen |
| NGINX Rewrite (`/api` → `/`) | #4 | ✅ `nginx-conf.yaml:60-61` bestaetigt |
| Kein bestehender `/enterprise-settings` Endpoint | #4 | ✅ Pfad ist frei (grep ueber gesamtes Backend) |
| EnterpriseSettings Interface (14 Felder) | #5 | ✅ Exakt Zeilen 98-117 in `settings.ts` |
| Logo-URL konsistent | #5 | ✅ `/api/enterprise-settings/logo` in 5 Komponenten |
| LoginText.tsx + AuthFlowContainer.tsx | #5 | ✅ Zeilen und Inhalte exakt bestaetigt |
| ConfigMap (api + web teilen sich `env-configmap`) | #7 | ✅ Beide nutzen `envFrom.configMapRef` |
| Extension Framework Hook (`main.py:514-524`) | #7 | ✅ Korrekt implementiert |
| `EXT_BRANDING_ENABLED` AND-Gating | #7 | ✅ `config.py:25-28` geprueft |

### Korrekturen durch Audit (v0.2 → v0.3)

| Was | Aenderung |
|-----|----------|
| Sicherheitsnachweis Gate 1+2 | Formulierung praezisiert: "wird nicht erreicht solange Backend `ee_features_enabled` sendet" statt "wird NIE erreicht". Hinweis auf theoretisches Admin-Risiko ergaenzt. |
| Seiteneffekte-Sektion | Komplett neu: 7 Referenz-Stellen einzeln dokumentiert mit Risikobewertung. `proxy.ts` und `admin/Layout.tsx` Effekte aufgenommen. |
| Branding-Audit | 5 neue Stellen ergaenzt: K2 (NonAdminStep Duplikat), M (Agent Owner Fallback), N (Billing E-Mail), E erweitert. Kategorie 5 (VoeB-irrelevant) hinzugefuegt mit NRF, Craft, Cloud. |
| OPEN-2, OPEN-3 | Status auf GEKLAERT aktualisiert |

### Keine Blocker gefunden

Das Audit hat keine architektonischen Fehler oder Security-Blocker identifiziert. Alle Behauptungen der Modulspec sind korrekt oder wurden korrigiert.

---

## Referenzen

| Dokument | Pfad |
|---------|------|
| Extension-Entwicklungsplan | `docs/referenz/ext-entwicklungsplan.md` |
| EE/FOSS-Abgrenzung | `docs/referenz/ee-foss-abgrenzung.md` |
| Extension Framework Spec | `docs/technisches-feinkonzept/ext-framework.md` |
| Core-Dateien Regeln | `.claude/rules/core-dateien.md` |
| Sicherheits-Checkliste | `.claude/rules/sicherheit.md` |
| EnterpriseSettings Interface | `web/src/interfaces/settings.ts:98-117` |
| Frontend Settings Fetching | `web/src/components/settings/lib.ts` |
| Logo Rendering (FOSS) | `web/src/refresh-components/Logo.tsx` |
| Layout Metadata (CORE #4) | `web/src/app/layout.tsx:47-65` |
| Constants (CORE #6) | `web/src/lib/constants.ts:48-51` |
| EE Theme Admin (Referenz) | `web/src/app/ee/admin/theme/page.tsx` |
| Backend Settings API (Referenz) | `backend/onyx/server/settings/api.py` |

---

## Approvals

| Rolle | Name | Datum | Status |
|------|------|-------|--------|
| Tech Lead | Nikolaj Ivanov | TBD | Ausstehend |

---

## Revisions-Historie

| Version | Datum | Autor | Aenderungen |
|---------|-------|-------|-----------|
| 0.1 | 2026-03-08 | Claude (Entwurf) | Initialer Entwurf nach Tiefenanalyse |
| 0.2 | 2026-03-08 | Claude (Entwurf) | OPEN-1/6/7 geklaert, Branding-Audit (alle "Onyx"-Stellen), OPEN-8/9 hinzugefuegt, SVG ausgeschlossen |
