# Fork-Management & Upstream-Sync

## Remotes
- `origin` → unser Fork (CCJ-Development/voeb-chatbot)
- `upstream` → Onyx FOSS (onyx-dot-app/onyx-foss)

## Branch-Strategie (Simplified GitLab Flow)

**Kein `develop`-Branch.** `main` ist der einzige langlebige Branch.

- `main` ← Integrationsbranch, auto-deploy DEV, Upstream-Merges via Branch+PR
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

### 3. Merge-Branch erstellen + Merge durchführen
```bash
# Branch erstellen (Branch Protection verbietet Direct Push auf main)
git checkout -b chore/upstream-sync-YYYY-MM-DD

# Merge durchführen
git merge upstream/main --no-commit --no-ff
```

### 4. Konflikte lösen

**Erwartete Konflikte (harmlos):**
- `AGENTS.md`, `.claude/skills` → Unsere Version behalten (`git checkout --ours`)
- `Chart.yaml`, `Chart.lock` → Upstream übernehmen (`git checkout --theirs`)
- 9 Core-Dateien → Upstream übernehmen, Patches neu anwenden (siehe unten)
- `backend/Dockerfile` → Upstream übernehmen, COPY ext/ neu einfügen (siehe "Zusätzliche Merge-Stellen")
- `deployment/docker_compose/env.template` → Manuell mergen (wir appenden am Ende, Upstream ändert Mitte)

**Unerwartete Konflikte:**
- Dateien in `backend/onyx/`, `web/src/` (außer Core) = Regeln gebrochen
- Ursache analysieren, ext_-Code anpassen (NICHT Onyx-Code)

### 5. Core-Datei-Patches aktualisieren

Fuer JEDE gepatchte Core-Datei (aktuell 4: main.py, constants.ts, LoginText.tsx, AuthFlowContainer.tsx):

```bash
# Beispiel Backend-Datei:
git show upstream/main:backend/onyx/main.py > backend/ext/_core_originals/main.py.original
diff -u backend/ext/_core_originals/main.py.original backend/onyx/main.py \
  > backend/ext/_core_originals/main.py.patch

# Beispiel Frontend-Datei:
git show upstream/main:web/src/lib/constants.ts > backend/ext/_core_originals/constants.ts.original
diff -u backend/ext/_core_originals/constants.ts.original web/src/lib/constants.ts \
  > backend/ext/_core_originals/constants.ts.patch

# Analog fuer LoginText.tsx und AuthFlowContainer.tsx
```

Falls Core-Datei-Konflikte auftreten (auto-merge fehlschlägt):
```bash
# Upstream übernehmen:
git checkout --theirs backend/onyx/main.py  # oder web/src/lib/constants.ts etc.
# Patch anwenden:
patch -p0 < backend/ext/_core_originals/main.py.patch
# Prüfen ob Patch sauber angewendet wurde, ggf. manuell nachbessern
```

> **Alle Patches liegen zentral in `backend/ext/_core_originals/`** — sowohl Backend- als auch Frontend-Dateien. Pro Core-Datei genau ein `.original` + ein `.patch`.

### 6. Helm-Dependencies prüfen
```bash
# Neue Sub-Charts in Chart.yaml?
grep "repository:" deployment/helm/charts/onyx/Chart.yaml
# Vergleichen mit helm repo add in .github/workflows/stackit-deploy.yml
# Fehlende Repos in ALLEN 3 Deploy-Jobs (dev, test, prod) ergänzen
```

### 7. PR erstellen und mergen
```bash
git commit -m "chore(upstream): Merge upstream/main — <N> Commits"
git push origin chore/upstream-sync-YYYY-MM-DD

# PR erstellen
gh pr create --base main --title "chore(upstream): Merge upstream/main — <N> Commits" \
  --body "Upstream-Sync: <N> Commits, <X> Konflikte"

# Nach CI-Checks + Review: Merge
gh pr merge <PR-NR> --squash --delete-branch
```

> **Hinweis:** Direct Push auf main ist durch Branch Protection blockiert.
> PRs muessen 3 CI-Checks bestehen: helm-validate, build-backend, build-frontend.

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

## Zweiter Upstream-Merge (2026-03-06) — Referenz

| Metrik | Wert |
|--------|------|
| Upstream-Commits | 100 |
| Konflikte | 1 (AGENTS.md) |
| Core-Datei-Konflikte | 0 (main.py auto-merged, ext-Hook intakt) |
| ext_-Code Konflikte | 0 |
| Infrastruktur-Konflikte | 0 |
| Wichtig | PR #9014 entfernt Lightweight Mode, PR #9005 Embedding-Blocker aufgehoben |
| Merge-Dauer | ~5 Min |
| Workflow | Branch + PR (erstmals mit Branch Protection) |

## Zusätzliche Merge-Stellen (neben Core-Dateien)

Neben den 9 Core-Dateien ändern wir 2 weitere Upstream-Dateien. Diese sind KEINE Core-Dateien, aber bekannte Merge-Stellen:

### `backend/Dockerfile` (seit Phase 4a)

3 Zeilen zwischen `COPY ./ee` und `COPY ./onyx`:
```dockerfile
# VÖB Extension Framework
COPY --chown=onyx:onyx ./ext /app/ext
```

**Bei Upstream-Konflikt:**
```bash
git checkout --theirs backend/Dockerfile
# Manuell einfuegen: 3 Zeilen nach "COPY ./ee /app/ee" + "COPY supervisord.conf"
```

**Risiko:** Mittel — Upstream ändert Dockerfile aktiv (~5 Commits/Monat). Insertion-Stelle ist stabil (zwischen ee und onyx COPY).

### `deployment/docker_compose/env.template` (seit Phase 4b)

25 Zeilen am Dateiende: VÖB Extension Framework Feature Flags.

**Bei Upstream-Konflikt:**
```bash
# Meist auto-merge (Append am Ende). Falls nicht:
git checkout --theirs deployment/docker_compose/env.template
# Unseren Block am Ende wieder anfuegen
```

**Risiko:** Niedrig — Appends am Dateiende mergen fast immer automatisch.

### Vollständige Liste aller Upstream-Änderungen

| Datei | Art | Zeilen | Risiko |
|-------|-----|--------|--------|
| `backend/onyx/main.py` (CORE #1) | Hook | ~14 | Niedrig |
| `web/src/lib/constants.ts` (CORE #6) | 1 Zeile | 1 | Niedrig |
| `web/src/app/auth/login/LoginText.tsx` (CORE #8) | Conditional | ~8 | Niedrig |
| `web/src/components/auth/AuthFlowContainer.tsx` (CORE #9) | Logo+Name | ~25 | Mittel |
| `backend/Dockerfile` | COPY | 3 | Mittel |
| `deployment/docker_compose/env.template` | Append | 25 | Niedrig |

Alle anderen Dateien (ext/, docs/, .claude/, deployment/helm/values/) existieren nicht in Upstream → Zero Konflikte.

## Warum "Extend, don't modify" funktioniert
- Max 9 vorhersagbare Core-Konflikte + 2 bekannte Infra-Stellen
- Unser ext_-Code: Zero Konflikte (Ordner existiert nicht in Upstream)
- Unsere Infra (Terraform, Helm Values, CI/CD): Zero Konflikte (Pfade existieren nicht in Upstream)
- Unsere Docs: Zero Konflikte (existieren nicht in Upstream)
- Patches pro Core-Datei: 2-5 Zeilen, einfach neu anwendbar
- **Einzige Überraschungen:** Neue Helm-Dependencies → CI/CD Workflow anpassen
