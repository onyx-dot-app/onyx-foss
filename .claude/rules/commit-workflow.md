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
# PR gegen develop erstellen
```

## Commit-Format
```
<type>(<scope>): <description>
Types: feat, fix, docs, refactor, test, chore, spec
Scopes: ext-token, ext-rbac, ext-analytics, ext-branding, ext-prompts, ext-access, ext-framework, docs, ci
```
