---
paths:
  - "backend/ext/models/**"
  - "backend/ext/migrations/**"
---

# Datenbank-Design-Regeln

> **Hinweis zu CLAUDE.md**: Die Upstream-Regel "Put ALL db operations under backend/onyx/db"
> gilt fuer Onyx-Code. Unsere ext_-Models leben in `backend/ext/models/` — das ist kein
> Widerspruch, sondern die bewusste Trennung zwischen Onyx-Code (READ-ONLY) und Extensions.

## Namenskonvention
- Tabellen: `ext_{modulname}_{entity}` (z.B. ext_token_budgets)
- Foreign Keys: `fk_ext_{tabelle}_{referenz}`
- Indizes: `ix_ext_{tabelle}_{spalte}`

## Pflicht pro Tabelle
- ext_-Prefix, Primary Key (prüfe Onyx-Pattern: UUID oder Integer)
- created_at + updated_at Timestamps
- FK auf Onyx-Tabellen: NUR Referenz, KEIN CASCADE DELETE
- Indizes auf häufige Query-Spalten
- Soft-Delete wo Daten nicht verloren gehen dürfen

## Alembic (Onyx-Alembic mitnutzen)

ext_-Tabellen nutzen die **bestehende Onyx-Alembic-Konfiguration** (`backend/alembic.ini`).
Kein eigenes `alembic.ini` — das haelt den Migrations-Stack einfach und vermeidet Konflikte.

```bash
cd backend
# Migration erstellen
alembic revision -m "ext_branding: Create ext_branding_config table"

# Migration ausfuehren
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Konventionen:**
- Migrations-Kommentar immer mit `ext_{modul}:` prefixen
- Nur ext_-Tabellen erstellen (CREATE TABLE), niemals Onyx-Tabellen aendern (ALTER TABLE)
- Foreign Keys auf Onyx-Tabellen (z.B. `user_.id`) sind erlaubt (READ-ONLY Referenz)
- Downgrade-Funktion ist Pflicht (DROP TABLE fuer ext_-Tabellen)
