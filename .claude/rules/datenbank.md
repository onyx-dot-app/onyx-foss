---
paths:
  - "backend/ext/models/**"
  - "backend/ext/migrations/**"
---

# Datenbank-Design-Regeln

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

## Alembic (eigene Config, getrennt von Onyx)
```bash
cd backend
alembic -c ext/alembic.ini revision --autogenerate -m "add ext_table" --branch-label ext
alembic -c ext/alembic.ini upgrade head
alembic -c ext/alembic.ini downgrade -1
```
Eigenes alembic.ini + eigenes versions/-Verzeichnis. Unabhängig von Onyx-Migrationen.
