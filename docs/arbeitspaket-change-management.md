# Arbeitspaket: Change & Release Management Dokumentation

**Erstellt**: 2026-03-05
**Priorität**: Hoch (vor M1-Abnahme)
**Geschätzter Aufwand**: 4-6 Stunden
**Verantwortlich**: Nikolaj Ivanov (CCJ)

---

## Hintergrund

Die technische Umsetzung (CI/CD Pipeline, Branch-Strategie, Helm Deployments) ist funktional und verifiziert. Die **Dokumentation** dieser Prozesse ist jedoch auf interne Arbeitsanweisungen (`.claude/rules/`) verteilt und nicht audit-fähig.

BAIT (Bankaufsichtliche Anforderungen an die IT) fordert unter anderem:
- Nachvollziehbares Änderungsmanagement (Kap. 8)
- Trennung von Entwicklung und Betrieb (Kap. 8.3)
- Tests vor Produktivnahme (Kap. 8.5)
- Freigabeverfahren mit dokumentierter Verantwortlichkeit (Kap. 8.6)

Ein externer Auditor sucht diese Informationen in **Betriebs- und Sicherheitskonzept**, nicht in AI-Instruktionsdateien.

---

## Was existiert bereits

| Thema | Wo dokumentiert | Audit-fähig? |
|-------|----------------|-------------|
| CI/CD Pipeline Ablauf | `docs/betriebskonzept.md` (Deployment-Prozess) | Teilweise |
| Rollback-Strategie | `docs/betriebskonzept.md` (3 Szenarien) | Ja |
| Helm Deployment Kommandos | `docs/betriebskonzept.md` + `docs/runbooks/helm-deploy.md` | Ja |
| Branch-Strategie | `.claude/rules/fork-management.md` | Nein (AI-Instruktion) |
| Commit-Workflow | `.claude/rules/commit-workflow.md` | Nein (AI-Instruktion) |
| Promotion-Modell (DEV→TEST→PROD) | `.claude/rules/fork-management.md` | Nein (AI-Instruktion) |
| Umgebungstrennung | `docs/adr/adr-004-umgebungstrennung-dev-test-prod.md` | Ja |
| Secrets Management | `docs/sicherheitskonzept.md` (Abschnitt 5) | Teilweise |

---

## Was fehlt — 6 Maßnahmen

### M-CM-1: Change-Management-Abschnitt im Betriebskonzept

**Wo**: `docs/betriebskonzept.md` — neuer Abschnitt nach "Deployment-Prozess"

**Inhalt**:
- Branching-Strategie (Simplified GitLab Flow) mit Diagramm
- Promotion-Pfad: `feature/*` → PR → `main` → DEV (auto) → `release/*` → TEST (manuell) → Tag → PROD (manuell)
- Änderungskategorien: Standard Change (Feature), Emergency Change (Hotfix), Upstream-Merge
- Freigabestufen pro Environment:
  - DEV: Automatisch nach PR-Merge auf `main`
  - TEST: Manueller Trigger durch Tech Lead (workflow_dispatch)
  - PROD: Manueller Trigger + GitHub Environment Approval
- Dokumentation jeder Änderung: Git Commit, PR-Beschreibung, CHANGELOG.md

**Quelle**: Inhalte aus `.claude/rules/fork-management.md` und `.claude/rules/commit-workflow.md` in Enterprise-Format überführen.

---

### M-CM-2: 4-Augen-Prinzip dokumentieren und konfigurieren

**Wo**: `docs/betriebskonzept.md` (Change Management) + `docs/sicherheitskonzept.md` (Zugriffskontrollen)

**Inhalt**:
- BAIT fordert: Keine Änderung an Produktion ohne zweite Freigabe
- Aktueller Stand (1-Person-Team): Tech Lead = Entwickler = Reviewer
- Geplante Umsetzung:
  - **GitHub Branch Protection** auf `main`: Require Pull Request, Require 1 Approval
  - **GitHub Environment Protection** auf `prod`: Required Reviewers (z.B. VÖB-Ansprechpartner oder zweiter CCJ-Mitarbeiter)
  - **Release-Branches**: Nur Tech Lead darf `release/*` schneiden und taggen
- Interims-Lösung (bis zweiter Reviewer verfügbar): Self-Review + dokumentierte PR-Checkliste + Commit-Freigabe durch Tech Lead
- Langfristig: VÖB-Stakeholder als Required Reviewer für PROD Environment

**Technisch umzusetzen**:
```
GitHub → Repository Settings → Branches → Branch protection rules:
  - Branch: main
  - Require a pull request before merging: ✅
  - Require approvals: 1 (sobald zweite Person verfügbar)
  - Do not allow bypassing: ✅ (für PROD)
  - Require status checks: CI muss grün sein

GitHub → Repository Settings → Environments → prod:
  - Required reviewers: [Tech Lead + VÖB-Kontakt]
  - Wait timer: optional (z.B. 10 Min Bedenkzeit)
```

---

### M-CM-3: Zugriffsmatrix im Sicherheitskonzept

**Wo**: `docs/sicherheitskonzept.md` — neuer Abschnitt oder Erweiterung bestehender Zugriffskontrollen

**Inhalt — Tabelle**:

| Ressource | Rolle | Zugriff | Bemerkung |
|-----------|-------|---------|-----------|
| GitHub Repository | Tech Lead (Niko) | Admin (Write, Merge, Settings) | Einziger Admin aktuell |
| GitHub Repository | VÖB | Read | Einsicht in Code + PRs |
| GitHub Environment `dev` | CI/CD (auto) | Deploy | Kein manueller Zugriff nötig |
| GitHub Environment `test` | Tech Lead | workflow_dispatch | Manueller Trigger |
| GitHub Environment `prod` | Tech Lead + Reviewer | workflow_dispatch + Approval | 4-Augen (geplant) |
| StackIT Kubeconfig | Tech Lead | Cluster-Admin | SEC-05: Separate Kubeconfigs geplant |
| StackIT Terraform | Tech Lead | SA `voeb-terraform` | Credentials auf Laptop (SEC-04: Remote State geplant) |
| PostgreSQL (DEV) | `onyx_app` | RW | ACL auf Cluster-Egress-IP |
| PostgreSQL (DEV) | `db_readonly_user` | RO | Für Knowledge Graph |
| PostgreSQL (PROD) | Gleiche User | RW/RO | + PG-Audit-Logging geplant |
| Container Registry | CI/CD Robot Account | Push/Pull | Credentials in GitHub Secrets |

---

### M-CM-4: Release-Management-Prozess

**Wo**: `docs/betriebskonzept.md` — neuer Abschnitt nach Change Management

**Inhalt**:
- Release-Planung: Pro Meilenstein (M1-M6) ein Release-Branch
- Release-Nomenklatur: `release/1.0` (Meilenstein), Tags `v1.0.0` (Patch-Level)
- Release-Checkliste:
  1. DEV stabil (Smoke Tests grün, keine offenen P0/P1 Bugs)
  2. Release-Branch von `main` schneiden
  3. TEST-Deploy + Validierung (UAT durch VÖB falls erforderlich)
  4. Bugfixes auf Release-Branch, Cherry-Pick zurück nach `main`
  5. Tag setzen (`v1.0.0`) + PROD-Deploy
  6. Release-Branch zurück nach `main` mergen
  7. CHANGELOG.md aktualisieren
  8. Abnahmeprotokoll ausfüllen
- Hotfix-Prozess: `hotfix/*` Branch von `release/*`, nach Fix Merge in Release-Branch + `main`
- Versioning: Semantic Versioning (Major.Minor.Patch)

---

### M-CM-5: Rollback-Runbook erweitern

**Wo**: `docs/runbooks/` — neues Dokument `rollback-verfahren.md` oder Erweiterung von `helm-deploy.md`

**Inhalt**:
- Entscheidungsbaum: Rollback vs. Hotfix (wann welcher Weg?)
- Helm Rollback Schritt-für-Schritt:
  ```
  helm history onyx-{env} -n onyx-{env}
  helm rollback onyx-{env} <revision> -n onyx-{env}
  kubectl rollout status ...
  Smoke Test
  ```
- Datenbank-Rollback: `alembic downgrade -1` (wann sicher, wann nicht)
- Kommunikation: Wer wird informiert? (Tech Lead, VÖB-Ansprechpartner)
- Post-Mortem: Vorlage für Fehleranalyse nach Rollback

---

### M-CM-6: CI/CD-Dokumentation im Betriebskonzept vervollständigen

**Wo**: `docs/betriebskonzept.md` — bestehenden Abschnitt "Deployment-Prozess" erweitern

**Inhalt**:
- `paths-ignore` erklären (Docs-only Commits triggern kein Deploy)
- Concurrency-Verhalten (nur 1 Deploy pro Environment, laufende abgebrochen)
- GitHub Actions SHA-Pinning erklären (Supply-Chain-Sicherheit)
- Smoke Test Verhalten pro Environment (DEV: 12 Versuche/2 Min, TEST/PROD: 18 Versuche/3 Min)
- Model Server Pinning erklären (Docker Hub `v2.9.8`, nicht selbst gebaut)
- Secret-Injection Ablauf (`--set` aus GitHub Environment Secrets)

---

## Umsetzungsreihenfolge

| Nr. | Maßnahme | Aufwand | Abhängigkeit |
|-----|----------|---------|-------------|
| 1 | M-CM-1: Change Management (Betriebskonzept) | 1.5h | Keine |
| 2 | M-CM-4: Release Management (Betriebskonzept) | 1h | Nach M-CM-1 |
| 3 | M-CM-3: Zugriffsmatrix (Sicherheitskonzept) | 1h | Keine |
| 4 | M-CM-6: CI/CD Doku vervollständigen (Betriebskonzept) | 0.5h | Keine |
| 5 | M-CM-5: Rollback-Runbook | 0.5h | Keine |
| 6 | M-CM-2: 4-Augen-Prinzip (Doku + GitHub Config) | 0.5h | Nach M-CM-1, M-CM-3 |

**Gesamt**: ~5 Stunden

---

## Abnahmekriterium

Ein externer BAIT-Auditor findet in `docs/betriebskonzept.md` und `docs/sicherheitskonzept.md`:
- Nachvollziehbaren Change-Management-Prozess mit Freigabestufen
- Dokumentierte Zugriffsmatrix mit Rollen und Berechtigungen
- Release-Management-Prozess mit Checkliste
- Rollback-Verfahren als Runbook
- 4-Augen-Prinzip dokumentiert (implementiert oder mit Interims-Lösung begründet)

Alle Informationen in **auditierbaren Enterprise-Dokumenten**, nicht in AI-Instruktionsdateien.
