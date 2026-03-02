---
paths:
  - "backend/ext/**"
---

# Sicherheits-Checkliste (Bankendienstleister)

Jedes neue ext_-Modul durchläuft diese Prüfung.

## Input Validation
- [ ] Alle Inputs via Pydantic Schemas validiert
- [ ] Keine SQL-Strings aus User-Input (NUR SQLAlchemy ORM)
- [ ] String-Maxlänge, numerische Min/Max definiert

## Auth & RBAC
- [ ] Alle ext/-Endpoints erfordern Auth (Entra ID)
- [ ] RBAC-Checks: Nur autorisierte Rollen haben Zugriff
- [ ] Keine Hardcoded Secrets (alles über .env)

## Logging (DSGVO)
- [ ] Keine personenbezogenen Daten in Logs
- [ ] Keine Tokens/Passwörter/API-Keys in Logs
- [ ] Format: `[EXT-{MODULNAME}] {message}`

## Error Handling
- [ ] Alle Exceptions gefangen (kein unhandled an Client)
- [ ] Keine internen Details in Fehlermeldungen
- [ ] HTTP-Statuscodes korrekt (400/401/403/500)
- [ ] ext_-Hooks in Core-Dateien: Try/Except, Onyx nie brechen
