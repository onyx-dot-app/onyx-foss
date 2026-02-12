# Codebase-Orientierung — Wo finde ich was?

## Onyx Backend
```
backend/onyx/
  main.py                    ← FastAPI App + Router-Registrierung (CORE #1)
  llm/multi_llm.py           ← LLM-Aufrufe (CORE #2)
  access/access.py           ← Permissions/Access Control (CORE #3)
  chat/prompt_utils.py       ← Prompts (CORE #7)
  db/models.py               ← SQLAlchemy Models (READ-ONLY)
  db/engine/sql_engine.py    ← DB Connection (READ-ONLY)
  configs/app_configs.py     ← Konfiguration (READ-ONLY)
  server/auth_check.py       ← Route-Auth-Prüfung (READ-ONLY, aber relevant für ext)
backend/tests/               ← Onyx-Tests (READ-ONLY)
backend/alembic/             ← Onyx-Migrationen (READ-ONLY)
backend/requirements/        ← Onyx-Dependencies (READ-ONLY)
```

## Onyx Frontend
```
web/src/
  app/layout.tsx             ← Root Layout (CORE #4)
  app/page.tsx               ← Startseite
  app/admin/                 ← Admin-Bereich
  app/chat/                  ← Chat-Interface
  components/header/         ← Header (CORE #5)
  lib/constants.ts           ← Konstanten (CORE #6)
web/package.json, tailwind.config.js
```

## Unser Extension-Code (HIER arbeiten wir)
```
backend/ext/                 ← Backend-Extensions
  config.py                  ← Feature Flags
  routers/                   ← FastAPI Router
  models/                    ← DB Models (ext_-Prefix)
  schemas/                   ← Pydantic Schemas
  services/                  ← Business Logic
  migrations/versions/       ← Alembic (eigener Branch)
  tests/                     ← Backend-Tests
  _core_originals/           ← Backups vor Core-Änderungen
web/src/ext/                 ← Frontend-Extensions
  components/                ← React-Komponenten
  pages/                     ← Eigene Seiten (/ext/...)
  hooks/                     ← React Hooks
  lib/api.ts                 ← API-Client
```

## Konfiguration
```
deployment/docker_compose/
  .env                       ← Umgebungsvariablen + EXT_-Flags
  env.template               ← Template
  docker-compose.yml         ← Docker (READ-ONLY Struktur)
```

## Enterprise-Docs
```
docs/
  README.md                  ← Index
  sicherheitskonzept.md      ← Security
  testkonzept.md             ← Testing
  betriebskonzept.md         ← Operations
  CHANGELOG.md               ← Versionshistorie
  technisches-feinkonzept/   ← Modulspezifikationen
  adr/                       ← Architecture Decisions
  abnahme/                   ← Abnahmeprotokolle
  referenz/                  ← Business-Dokumente
```
