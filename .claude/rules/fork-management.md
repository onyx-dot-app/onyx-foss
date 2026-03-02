# Fork-Management & Upstream-Sync

## Remotes
- `origin` → unser Fork
- `upstream` → Onyx FOSS (github.com/onyx-dot-app/onyx)

## Branches
- `main` ← Tracked Upstream-Releases
- `develop` ← Unsere Arbeit
- `feature/*` ← Feature-Branches von develop
- `release/*` ← Meilenstein-Releases

## Upstream-Sync (bei neuem Onyx-Release)
```
1. git fetch upstream
2. git checkout main && git merge upstream/main
   → Konflikte NUR in 7 Core-Dateien erwartet
   → Andere Konflikte = Regeln gebrochen
3. Core-Datei-Konflikte lösen:
   → Upstream übernehmen
   → Patches aus _core_originals/ neu anwenden
4. git checkout develop && git merge main
5. Tests durchlaufen
6. Wenn Tests brechen: ext_-Code anpassen (NICHT Onyx-Code)
```

## Warum "Extend, don't modify" funktioniert
- Max 7 vorhersagbare Merge-Konflikte
- Unser ext_-Code: Zero Konflikte (Ordner existiert nicht in Upstream)
- Patches pro Core-Datei: 2-5 Zeilen, einfach neu anwendbar
