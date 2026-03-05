# Commit- und PR-Workflow

## PFLICHT: Feature-Branch für JEDE Arbeit

**NIEMALS direkt auf `main` committen.** Jede Session beginnt so:

```bash
# 1. Sicherstellen dass main aktuell ist
git checkout main
git pull origin main

# 2. Feature-Branch erstellen
git checkout -b feature/<thema>
# Beispiele: feature/tls-setup, feature/doku-audit, feature/ext-token-limits
```

### Wann wird der Branch gemergt?
- Feature-Branch lebt bis das Thema FERTIG ist (kann über mehrere Sessions gehen)
- Wenn ein Branch bereits existiert: `git checkout feature/<thema>` (NICHT neu erstellen)
- Am Ende: PR gegen `main` → Review → Merge → auto-deploy DEV

### Session-Start Checkliste
1. `git status` — Bin ich auf einem Feature-Branch? Wenn ja, weiterarbeiten.
2. Kein Feature-Branch? → `git checkout -b feature/<thema>` von `main`
3. NIEMALS `main` als Arbeitsbranch nutzen

---

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
git push origin feature/{thema}
# PR gegen main erstellen (gh pr create)
```

## PR-Workflow
```bash
# PR erstellen
gh pr create --base main --title "<type>(<scope>): <Beschreibung>" --body "..."

# Nach Nikos Freigabe: Merge
gh pr merge <PR-NR> --squash --delete-branch
```

---

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
