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

## Konfiguration (Lokal / Docker)
```
deployment/docker_compose/
  .env                       ← Umgebungsvariablen + EXT_-Flags
  env.template               ← Template
  docker-compose.yml         ← Docker (READ-ONLY Struktur)
```

## StackIT Cloud-Infrastruktur (NEU)
```
deployment/terraform/
  modules/stackit/
    main.tf                  ← SKE Cluster, PostgreSQL Flex, Object Storage
    variables.tf             ← Alle Variablen mit DEV-Defaults
    outputs.tf               ← Kubeconfig, PG-Credentials, Bucket-URL
    versions.tf              ← Provider stackitcloud/stackit ~> 0.56
  environments/dev/
    main.tf                  ← DEV-Umgebung (ruft Modul auf)
    backend.tf               ← State-Backend (lokal, remote vorbereitet)
    terraform.tfvars         ← Projekt-spezifische Werte
```

## Helm Value-Overlays (NEU)
```
deployment/helm/
  charts/onyx/               ← Onyx Helm Chart (READ-ONLY, nicht verändern!)
  values/
    values-common.yaml       ← Gemeinsame Config (PG extern, MinIO aus, Vespa+Redis an)
    values-dev.yaml          ← DEV: 1 Replica, Lightweight, Auth disabled
```
Deployment: `helm upgrade --install -f values-common.yaml -f values-dev.yaml`

## CI/CD (NEU)
```
.github/workflows/
  stackit-deploy.yml         ← Build → StackIT Registry → Helm Deploy (DEV/TEST/PROD)
  upstream-check.yml         ← Wöchentlicher Upstream-Merge-Check
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
  referenz/
    stackit-implementierungsplan.md  ← DEV-Infrastruktur Step-by-Step
    stackit-infrastruktur.md         ← StackIT Specs + Architekturentscheidungen
```
