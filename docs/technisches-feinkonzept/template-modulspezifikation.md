# Modulspezifikation Template

**Dokumentstatus**: Entwurf
**Vorlage-Version**: 1.0

---

*Dieses Template dient als Grundlage für alle Modulspezifikationen. Ersetzen Sie alle `[PLACEHOLDER]` Texte mit Ihren spezifischen Inhalten.*

---

## Modulübersicht

| Feld | Wert |
|------|------|
| **Modulname** | [PLACEHOLDER: z. B. "Token Limits Management"] |
| **Modul-ID** | `ext_[PLACEHOLDER]` (z. B. `ext_limits`) |
| **Version** | [PLACEHOLDER: z. B. "1.0.0"] |
| **Autor** | [PLACEHOLDER: z. B. "CCJ / Coffee Studios"] |
| **Datum** | [PLACEHOLDER: Erstellungsdatum] |
| **Status** | [ ] Entwurf | [ ] Review | [ ] Freigegeben |
| **Priorität** | [ ] Kritisch | [ ] Hoch | [ ] Normal | [ ] Niedrig |

---

## Zweck und Umfang

### Zweck
[PLACEHOLDER: Beschreiben Sie in 2-3 Sätzen, welches Geschäftsproblem dieses Modul löst.]

**Beispiel**:
> Das Token Limits Management-Modul verwaltet die API-Token-Kontingente pro Benutzer und Organisation. Es gewährleistet, dass die Nutzung von LLM-APIs innerhalb vereinbarter Kostenschranken bleibt und bietet Echtzeitwarnungen bei Überschreitung.

### Im Umfang enthalten
- [PLACEHOLDER: Feature/Capability 1]
- [PLACEHOLDER: Feature/Capability 2]
- [PLACEHOLDER: Feature/Capability 3]

### Nicht im Umfang
- [PLACEHOLDER: Feature/Capability, die bewusst ausgeschlossen ist]
- [PLACEHOLDER: Future Enhancement]

### Abhängige Module / Prerequisites
- [ ] [PLACEHOLDER: z. B. Authentifizierung & Authorization]
- [ ] [PLACEHOLDER: z. B. Basisinfrastruktur]

---

## Architektur

### Komponenten-Übersicht

Diagramm Placeholder:
```
[PLACEHOLDER: ASCII-Diagramm oder Verweis auf externe Visualisierung]

Beispiel für Token Limits:
┌─────────────────────────────────────────────────┐
│         Onyx Chat Interface                      │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  Token Limits Middleware / Interceptor           │
│  - Request Validation                           │
│  - Quota Check                                  │
│  - Token Count Estimation                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  Token Limits API                               │
│  - GET /api/ext/limits/quota                    │
│  - POST /api/ext/limits/reset                   │
│  - GET /api/ext/limits/usage                    │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│  PostgreSQL (ext_limits_* tables)               │
│  - ext_limits_quota                             │
│  - ext_limits_usage_log                         │
│  - ext_limits_alerts                            │
└─────────────────────────────────────────────────┘
```

### Datenfluss

[PLACEHOLDER: Beschreiben Sie den typischen Request-Response-Fluss.]

**Beispiel für Token Limits**:
1. Benutzer sendet Chat-Message über UI
2. Middleware fängt Request ab
3. Token Limits Modul schätzt Token-Verbrauch
4. Vergleich mit Quota in `ext_limits_quota`
5. Falls unter Limit: Request fortgeleitet zu LLM
6. Falls über Limit: Error 429 + Alert erstellt in `ext_limits_alerts`
7. Analytics-Log in `ext_limits_usage_log`

---

## Datenbankschema

### Tabellen

#### Tabelle 1: `[PLACEHOLDER: ext_<modul>_<entität>]`

[PLACEHOLDER: Ersetzen Sie mit tatsächlichem Tabellennamen. Beispiel: `ext_limits_quota`]

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Eindeutige ID |
| `[PLACEHOLDER: spalte2]` | VARCHAR(255) | NOT NULL | [Beschreibung] |
| `[PLACEHOLDER: spalte3]` | INTEGER | DEFAULT 0 | [Beschreibung] |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Erstellungszeitpunkt |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Letzte Änderung |

**Beispiel für `ext_limits_quota`**:

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Eindeutige Quota-ID |
| `user_id` | UUID | NOT NULL, FK user.id | Zugehöriger Benutzer |
| `organization_id` | UUID | NOT NULL, FK organization.id | Zugehörige Organisation |
| `monthly_limit_tokens` | INTEGER | NOT NULL | Monatliches Token-Limit |
| `current_month_tokens` | INTEGER | DEFAULT 0 | Tokens im laufenden Monat |
| `reset_date` | DATE | NOT NULL | Datum des Quota-Resets |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Erstellt am |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Aktualisiert am |

#### Tabelle 2: `[PLACEHOLDER: ext_<modul>_<entität2>]`

[PLACEHOLDER: Weitere Tabellen analog]

### Relationen

[PLACEHOLDER: Beschreiben Sie Foreign Keys und deren Bedeutung.]

**Beispiel**:
```
ext_limits_quota (many) ──FK──> user (one)
ext_limits_quota (many) ──FK──> organization (one)
ext_limits_usage_log (many) ──FK──> ext_limits_quota (one)
```

### Indizes

[PLACEHOLDER: Liste der Indexe für Performance-Optimierung]

```sql
-- Schnelle Lookups nach user_id
CREATE INDEX idx_ext_limits_quota_user_id ON ext_limits_quota(user_id);

-- Schnelle Lookups nach organization_id
CREATE INDEX idx_ext_limits_quota_organization_id ON ext_limits_quota(organization_id);

-- Composite Index für Audit Trail
CREATE INDEX idx_ext_limits_usage_log_user_created
  ON ext_limits_usage_log(user_id, created_at DESC);
```

### Migrations

[PLACEHOLDER: Versioniertes Migrations-Script mit Datum]

**Beispiel Struktur**:
- `migrations/20240101_001_create_ext_limits_schema.sql`
- `migrations/20240115_002_add_alerts_table.sql`

---

## API-Spezifikation

### Endpoints

#### Endpoint 1: `[PLACEHOLDER: HTTP Method + Path]`

[PLACEHOLDER: Ersetzen Sie mit tatsächlichem Endpoint. Beispiel: `GET /api/ext/limits/quota`]

**Beschreibung**: [PLACEHOLDER: Was macht dieser Endpoint?]

**HTTP-Methode**: `[GET | POST | PUT | DELETE | PATCH]`

**Authentifizierung**: [PLACEHOLDER: z. B. "Bearer Token (JWT)", "API Key"]

**Request**:

```http
[PLACEHOLDER: Beispiel-Request]

Beispiel:
GET /api/ext/limits/quota?user_id=550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: dev.chatbot.voeb-service.de
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Query Parameter**:

| Parameter | Typ | Erforderlich | Beschreibung |
|-----------|-----|-------------|-------------|
| `[PLACEHOLDER: param1]` | string | Ja/Nein | [Beschreibung] |
| `user_id` | UUID | Ja | Benutzer-ID |

**Request Body** (falls zutreffend):

```json
{
  "[PLACEHOLDER: field1]": "[PLACEHOLDER: value1]",
  "monthly_limit_tokens": 100000,
  "reset_date": "2024-02-01"
}
```

**Response (Success 200)**:

```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "monthly_limit_tokens": 100000,
    "current_month_tokens": 45230,
    "remaining_tokens": 54770,
    "reset_date": "2024-02-01",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

**Response (Error 4xx/5xx)**:

```json
{
  "status": "error",
  "code": "[PLACEHOLDER: z. B. 'QUOTA_NOT_FOUND' oder 'INSUFFICIENT_PERMISSIONS']",
  "message": "[PLACEHOLDER: Lesbare Fehlermeldung]",
  "details": {
    "[PLACEHOLDER: key]": "[PLACEHOLDER: value]"
  }
}
```

| HTTP-Status | Grund |
|---|---|
| `200` | Erfolgreiche Anfrage |
| `400` | Ungültige Parameter |
| `401` | Authentifizierung erforderlich |
| `403` | Insufficient Permissions |
| `404` | Ressource nicht gefunden |
| `429` | Rate Limit überschritten |
| `500` | Interner Server-Fehler |

---

#### Endpoint 2: `[PLACEHOLDER: Weiterer Endpoint]`

[PLACEHOLDER: Analog zu Endpoint 1 dokumentieren]

### Error Handling & Fehler-Codes

[PLACEHOLDER: Definieren Sie spezifische Fehler-Codes für dieses Modul]

| Fehler-Code | HTTP-Status | Beschreibung | Aktion |
|-------------|------------|-------------|--------|
| `MODULE_QUOTA_EXCEEDED` | 429 | Monatliches Token-Limit überschritten | Benachrichtige Benutzer, biete Quota-Upgrade |
| `MODULE_UNAUTHORIZED` | 403 | Benutzer hat keine Berechtigung für diese Ressource | Überprüfe RBAC-Konfiguration |
| `MODULE_INVALID_INPUT` | 400 | Ungültige Request-Parameter | Validierung fehlgeschlagen |
| `MODULE_DATABASE_ERROR` | 500 | Datenbankfehler | Kontaktiere Support, überprüfe Logs |

---

## Frontend-Komponenten

[PLACEHOLDER: Falls das Modul UI-Komponenten enthält, beschreiben Sie diese hier.]

### Komponente 1: `[PLACEHOLDER: ComponentName]`

**Technologie**: React (Next.js / TypeScript)

**Location**: `web/src/ext/[modul]/components/[ComponentName].tsx`

**Beschreibung**: [PLACEHOLDER: Was macht diese Komponente?]

**Props**:

```typescript
interface ComponentProps {
  [PLACEHOLDER: prop1]: string;
  [PLACEHOLDER: prop2]: number;
}
```

**State & Hooks**:

- `[PLACEHOLDER: useState/useEffect hooks]`

**Beispiel-Rendering**:

```jsx
<QuotaWidget
  userId={user.id}
  currentUsage={45230}
  monthlyLimit={100000}
/>
```

---

## Abhängigkeiten

### Abhängigkeiten zu anderen Modulen

[PLACEHOLDER: Listet auf, von welchen anderen Extension-Modulen dieses abhängig ist]

| Modul | Abhängigkeit | Grund |
|-------|-------------|-------|
| [PLACEHOLDER: auth-rbac] | [Erforderlich | Optional] | [Grund: z. B. "für Permission Checks"] |

**Beispiel für Token Limits**:

| Modul | Abhängigkeit | Grund |
|-------|-------------|-------|
| `auth-rbac` | Erforderlich | Bestimmt, welche Benutzer welche Quotas bearbeiten dürfen |
| `analytics` | Optional | Für erweiterte Reporting-Features |

### Abhängigkeiten zu externen Services

[PLACEHOLDER: Externe APIs, Services, Bibliotheken]

| Service | Zweck | API/Library | Version |
|---------|-------|-----------|---------|
| [PLACEHOLDER: OpenAI API] | [Token-Zählung] | openai | >=1.0.0 |

### Python Dependencies

```txt
# backend/ext/requirements.txt
[PLACEHOLDER: package1]>=1.0.0
[PLACEHOLDER: package2]>=2.5.0,<3.0.0
```

---

## Konfiguration

### Environment Variables

[PLACEHOLDER: Alle konfigurierbaren Einstellungen für dieses Modul]

| Variable | Wert-Typ | Pflichtfeld | Standard | Beschreibung |
|----------|----------|-----------|---------|-------------|
| `EXT_[MODUL]_ENABLED` | boolean | Nein | `true` | Feature-Flag zum Aktivieren/Deaktivieren |
| `[PLACEHOLDER: VAR2]` | [type] | Ja/Nein | [default] | [Beschreibung] |

**Beispiel für Token Limits**:

| Variable | Wert-Typ | Pflichtfeld | Standard | Beschreibung |
|----------|----------|-----------|---------|-------------|
| `EXT_LIMITS_ENABLED` | boolean | Nein | `true` | Token Limits aktivieren |
| `EXT_LIMITS_DEFAULT_MONTHLY_TOKENS` | integer | Ja | `100000` | Standard monatliche Token pro Benutzer |
| `EXT_LIMITS_ALERT_THRESHOLD_PERCENT` | integer | Nein | `80` | Schwelle (%) für Warnungen |
| `EXT_LIMITS_LLM_TOKEN_MULTIPLIER` | float | Nein | `1.0` | Multiplikator für Token-Schätzung |

### Feature Flags

[PLACEHOLDER: Beschreiben Sie dynamische Feature Flags für A/B Testing, Rollouts]

```python
# Beispiel: Neues Quota-Reset-Verfahren
from ext.config import EXT_LIMITS_NEW_RESET_LOGIC

if EXT_LIMITS_NEW_RESET_LOGIC:
    # Neue Reset-Logik verwenden
    ...
```

---

## Fehlerbehandlung und Logging

### Fehlerbehandlungs-Strategie

[PLACEHOLDER: Wie werden Fehler in diesem Modul behandelt?]

1. **Validierungsfehler**: Client-seitig validieren, dann Server-Seite nochmals validieren
2. **Datenbankfehler**: Retry-Logik mit exponential backoff
3. **Externer Service-Fehler**: Graceful Degradation + Fallback-Behavior
4. **Unerwartete Fehler**: Error Tracking (z. B. Sentry), Alert an Ops

### Logging-Strategie

[PLACEHOLDER: Welche Events werden geloggt und auf welchem Log-Level?]

**Log Levels**:

| Level | Beispiel | Aktion |
|-------|----------|--------|
| `DEBUG` | Token-Zählung beginnen | Entwicklungs-Debugging |
| `INFO` | Quota erfolgreich aktualisiert | Wichtige Geschäftsereignisse |
| `WARN` | Benutzer nähert sich Quota-Limit | Aufmerksamkeit erforderlich |
| `ERROR` | Datenbankfehler bei Quota-Update | Fehlerbehandlung, Alert |

**Beispiel Logging**:

```python
import logging

logger = logging.getLogger("ext.limits")

logger.info(
    "Token quota check",
    extra={
        "user_id": user.id,
        "current_tokens": 45230,
        "limit_tokens": 100000,
        "percent_used": 45.23,
    },
)

logger.warning(
    "Token limit approaching",
    extra={
        "user_id": user.id,
        "percent_used": 85,
        "days_until_reset": 16,
    },
)

logger.error(
    "Quota update failed",
    extra={
        "user_id": user.id,
        "error": str(e),
    },
    exc_info=True,
)
```

### Structured Logging

[PLACEHOLDER: JSON-Format für Log-Aggregation]

```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "level": "INFO",
  "service": "ext_limits",
  "event": "quota_check",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "quota_id": "550e8400-e29b-41d4-a716-446655440002",
  "current_tokens": 45230,
  "monthly_limit": 100000,
  "status": "success"
}
```

---

## Performance-Anforderungen

### Non-Functional Requirements (NFR)

[PLACEHOLDER: Definieren Sie Performance-Ziele für dieses Modul]

| Anforderung | Zielwert | Priorität |
|------------|---------|-----------|
| Quota-Abfrage (GET /api/ext/limits/quota) | < 100 ms | Kritisch |
| Quota-Update | < 500 ms | Kritisch |
| Token-Zählung pro Request | < 50 ms | Hoch |
| Verfügbarkeit (Uptime) | 99.9% | Kritisch |

### Optimierungen

[PLACEHOLDER: Spezifische Optimierungsmaßnahmen]

- **Caching**: Redis-Cache für häufig abgerufene Quotas (TTL: 5 Min)
- **Datenbank**: Indizes auf `user_id`, `organization_id`
- **Async**: Asynchrones Logging und Alerts
- **Batching**: Batch-Update von Usage-Logs

### Last-Tests

[PLACEHOLDER: Geplante Last-Tests]

- [ ] 1000 gleichzeitige Benutzer, Quota-Abfragen
- [ ] 100 Requests/Sekunde, Token-Zähl-Operationen
- [ ] Datenbankpool unter Last (Connection Pooling)

---

## Offene Punkte

[PLACEHOLDER: Fragen oder Entscheidungen, die noch geklärt werden müssen]

- [ ] **[OPEN-1]** [Frage oder Entscheidung zu klären]
  - **Verantwortlicher**: [Name]
  - **Fälligkeitsdatum**: [Datum]
  - **Kontext**: [Warum ist das wichtig?]

- [ ] **[OPEN-2]** [Weitere offene Punkte]

**Beispiel für Token Limits**:

- [ ] **[OPEN-1]** Wie wird Token-Zählung für Streaming-Responses gehandhabt?
  - **Verantwortlicher**: CCJ Technical Lead
  - **Fälligkeitsdatum**: 2024-01-31
  - **Kontext**: Streaming-Responses verbrauchen Tokens incrementell, müssen aber vor Abschluss bekannt sein.

- [ ] **[OPEN-2]** Soll es separate Quotas für verschiedene LLM-Modelle geben?
  - **Verantwortlicher**: CCJ Project Manager & VÖB
  - **Fälligkeitsdatum**: 2024-02-07
  - **Kontext**: Verschiedene Modelle haben unterschiedliche Kosten.

---

## Approvals

[PLACEHOLDER: Unterschriftsbereiche für Freigaben]

| Rolle | Name | Datum | Unterschrift |
|------|------|-------|-------------|
| Technical Lead | [PLACEHOLDER] | [TBD] | __ |
| Architect | [PLACEHOLDER] | [TBD] | __ |
| Security Lead | [PLACEHOLDER] | [TBD] | __ |
| Project Manager | [PLACEHOLDER] | [TBD] | __ |

---

## Revisions-Historie

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|-----------|
| 0.1 | [Datum] | [Autor] | Initialer Entwurf |
| [später] | [später] | [später] | [später] |

---

**Dokumentstatus**: Entwurf
**Letzte Aktualisierung**: [Datum TBD]
**Version**: [x.x.x]
