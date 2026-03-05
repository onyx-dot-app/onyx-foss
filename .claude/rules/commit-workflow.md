# Commit- und PR-Workflow

## WICHTIG: Du commitst NICHT selbstständig.
1. Implementieren + Selbst-Review
2. Niko Ergebnis präsentieren (Dateien, Tests, Core-Änderungen, offene Punkte)
3. Niko prüft lokal
4. Niko gibt Freigabe ("Ja, committen" / "Commit")
5. Erst dann: git add + commit + push

## Checkliste (vor Präsentation)
- [ ] Selbst-Review: Error Handling, Types, Feature Flag, keine Seiteneffekte
- [ ] Tests geschrieben + grün
- [ ] Lint + Types grün (ruff, mypy, tsc)
- [ ] Modulspez aktualisiert (falls Abweichung)
- [ ] docs/CHANGELOG.md aktualisiert
- [ ] docs/testkonzept.md → Testergebnisse
- [ ] Feature Flag in .env.template dokumentiert
- [ ] "Aktueller Status" in CLAUDE.md aktualisiert

## Nach Freigabe
```bash
git add <spezifische Dateien>  # NICHT git add .
git commit -m "<type>(<scope>): <description>"
git push origin feature/{modulname}
# PR gegen main erstellen
```

## Commit-Format

```
<type>(<scope>): <kurze Beschreibung>

- Konkrete Änderung 1
- Konkrete Änderung 2
- ...
```

### Regeln
- **Titel**: Max. 72 Zeichen, Imperativ ("Add", nicht "Added"), kleingeschrieben nach Scope
- **Body**: Bullet-Liste mit konkreten Änderungen (was + warum)
- **Leerzeile** zwischen Titel und Body
- **Sprache**: Deutsch oder Englisch, aber konsistent innerhalb eines Commits

### Types
| Type | Verwendung |
|------|------------|
| `feat` | Neues Feature / neue Funktionalität |
| `fix` | Bugfix |
| `docs` | Nur Dokumentation |
| `refactor` | Code-Umbau ohne Funktionsänderung |
| `test` | Tests hinzufügen/ändern |
| `chore` | Build, CI, Dependencies, Tooling |
| `spec` | Modulspezifikation |

### Scopes
| Scope | Bereich |
|-------|---------|
| `ext-framework` | Extension Framework Basis |
| `ext-token` | Token Limits Modul |
| `ext-rbac` | RBAC Modul |
| `ext-analytics` | Analytics Modul |
| `ext-branding` | Branding Modul |
| `ext-prompts` | Custom Prompts Modul |
| `ext-access` | Access Control Modul |
| `stackit-infra` | Terraform, StackIT Ressourcen |
| `helm` | Helm Charts, Values |
| `ci` | GitHub Actions, CI/CD Pipelines |
| `docs` | Dokumentation allgemein |

### Beispiel
```
docs(stackit-infra): Doku an tatsächlichen DEV-Stand anpassen

- Terraform apply + SA-Rolle als erledigt markiert (2026-02-22)
- Kubeconfig-Anleitung: stackit CLI statt terraform output
- K8s-Version auf v1.32 korrigiert
- Phasen-Status-Marker im Implementierungsplan ergänzt
```
