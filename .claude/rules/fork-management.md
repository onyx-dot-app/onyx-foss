# Fork-Management & Upstream-Sync

## Remotes
- `origin` → unser Fork (CCJ-Development/voeb-chatbot)
- `upstream` → Onyx FOSS (onyx-dot-app/onyx-foss)

## Branch-Strategie (Simplified GitLab Flow)

**Kein `develop`-Branch.** `main` ist der einzige langlebige Branch.

- `main` ← Integrationsbranch, auto-deploy DEV, Upstream-Merges landen hier
- `feature/*` ← Feature-Branches von main, PR zurück nach main
- `release/*` ← Geschnitten von main wenn TEST/PROD-ready

### Promotion-Modell
```
feature/* → PR → main → auto-deploy DEV
                  │
                  └→ release/1.0 → workflow_dispatch → TEST
                          │
                          └→ tag v1.0.0 → workflow_dispatch → PROD
                          │
                          └→ merge back → main
```

### Release-Workflow
```bash
# 1. Release-Branch schneiden (wenn DEV stabil)
git checkout main
git checkout -b release/1.0

# 2. TEST deployen
gh workflow run stackit-deploy.yml -f environment=test --ref release/1.0

# 3. Bugfixes auf Release-Branch, cherry-pick zurück nach main
git cherry-pick <fix-commit> # auf main

# 4. Wenn TEST approved: Tag setzen + PROD deployen
git tag -a v1.0.0 -m "Release v1.0.0 — M1 Infrastruktur"
git push origin v1.0.0
gh workflow run stackit-deploy.yml -f environment=prod --ref release/1.0

# 5. Release-Branch zurück nach main mergen
git checkout main
git merge release/1.0
```

## Upstream-Sync — Schritt für Schritt

### 1. Vorbereitung
```bash
git fetch upstream
git log --oneline HEAD..upstream/main | wc -l   # Anzahl neuer Commits
```

### 2. Test-Merge (Dry-Run in Worktree)
```bash
mkdir -p .claude/worktrees
git worktree add .claude/worktrees/upstream-test upstream/main
cd .claude/worktrees/upstream-test
git merge main --no-commit --no-ff
# Konflikte prüfen:
git diff --name-only --diff-filter=U
# Aufräumen:
git merge --abort
cd -
git worktree remove .claude/worktrees/upstream-test
```

### 3. Merge durchführen
```bash
git merge upstream/main --no-commit --no-ff
```

### 4. Konflikte lösen

**Erwartete Konflikte (harmlos):**
- `AGENTS.md`, `.claude/skills` → Unsere Version behalten (`git checkout --ours`)
- `Chart.yaml`, `Chart.lock` → Upstream übernehmen (`git checkout --theirs`)
- 7 Core-Dateien → Upstream übernehmen, Patches neu anwenden (siehe unten)

**Unerwartete Konflikte:**
- Dateien in `backend/onyx/`, `web/src/` (außer Core) = Regeln gebrochen
- Ursache analysieren, ext_-Code anpassen (NICHT Onyx-Code)

### 5. Core-Datei-Patches aktualisieren
```bash
# Upstream-Version als neues Original speichern:
git show upstream/main:backend/onyx/main.py > backend/ext/_core_originals/main.py.original

# Patch gegen aktuellen Stand regenerieren:
diff -u backend/ext/_core_originals/main.py.original backend/onyx/main.py \
  > backend/ext/_core_originals/main.py.patch
```

Falls Core-Datei-Konflikte auftreten (auto-merge fehlschlägt):
```bash
# Upstream übernehmen:
git checkout --theirs backend/onyx/main.py
# Patch anwenden:
patch -p0 < backend/ext/_core_originals/main.py.patch
# Prüfen ob Patch sauber angewendet wurde, ggf. manuell nachbessern
```

### 6. Helm-Dependencies prüfen
```bash
# Neue Sub-Charts in Chart.yaml?
grep "repository:" deployment/helm/charts/onyx/Chart.yaml
# Vergleichen mit helm repo add in .github/workflows/stackit-deploy.yml
# Fehlende Repos in ALLEN 3 Deploy-Jobs (dev, test, prod) ergänzen
```

### 7. CI/CD verifizieren
```bash
git commit -m "chore(upstream): Merge upstream/main — <N> Commits"
git push origin main
gh workflow run stackit-deploy.yml -f environment=dev -R CCJ-Development/voeb-chatbot
# Warten auf grünen Build + Health Check
```

### 8. TEST nach erfolgreichem DEV
```bash
gh workflow run stackit-deploy.yml -f environment=test -R CCJ-Development/voeb-chatbot
```

## Erster Upstream-Merge (2026-03-03) — Referenz

| Metrik | Wert |
|--------|------|
| Upstream-Commits | 415 |
| Konflikte | 4 (AGENTS.md, .claude/skills, Chart.yaml, Chart.lock) |
| Core-Datei-Konflikte | 0 (main.py auto-merged) |
| ext_-Code Konflikte | 0 |
| Infrastruktur-Konflikte | 0 |
| Zusätzlicher Fix | Helm Repo `python-sandbox` in CI/CD ergänzt |
| Merge-Dauer | ~5 Min (inkl. Verifikation) |

## Warum "Extend, don't modify" funktioniert
- Max 7 vorhersagbare Merge-Konflikte (Core-Dateien)
- Unser ext_-Code: Zero Konflikte (Ordner existiert nicht in Upstream)
- Unsere Infra (Terraform, Helm Values, CI/CD): Zero Konflikte (Pfade existieren nicht in Upstream)
- Unsere Docs: Zero Konflikte (existieren nicht in Upstream)
- Patches pro Core-Datei: 2-5 Zeilen, einfach neu anwendbar
- **Einzige Überraschungen:** Neue Helm-Dependencies → CI/CD Workflow anpassen
