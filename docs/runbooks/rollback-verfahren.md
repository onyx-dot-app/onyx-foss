# Runbook: Rollback-Verfahren

**Erstellt**: 2026-03-05
**Status**: Verifiziert (Prozess, nicht alle Szenarien live getestet)
**Verantwortlich**: Nikolaj Ivanov (CCJ)

---

## Entscheidungsbaum: Rollback vs. Hotfix

```
Problem erkannt
  │
  ├── Produktionssystem down / kritischer Bug?
  │     │
  │     ├── JA: Sofortiger Helm Rollback (< 5 Min)
  │     │     └── Danach: Root Cause Analysis + Hotfix
  │     │
  │     └── NEIN: Nicht-kritischer Bug?
  │           │
  │           ├── Workaround möglich?
  │           │     └── JA: Hotfix auf Feature-Branch, normaler Release-Prozess
  │           │
  │           └── Kein Workaround?
  │                 └── Rollback auf letzte stabile Version
  │
  └── Datenbank-Migration fehlgeschlagen?
        │
        ├── Migration reversibel? → alembic downgrade -1
        └── Migration irreversibel? → PG-Backup-Restore (StackIT Support)
```

**Faustregel**: Rollback bei akutem Schaden, Hotfix bei kontrolliertem Problem.

---

## 1. Helm Rollback (Anwendung)

### Voraussetzungen

- Kubeconfig konfiguriert (`~/.kube/config`)
- `helm` und `kubectl` installiert
- Zugriff auf den SKE Cluster

### Schritt-für-Schritt

```bash
# 1. Aktuelle Situation prüfen
helm history onyx-{env} -n onyx-{env}
# Zeigt alle Revisionen mit Status, Datum und Beschreibung

# 2. Stabile Revision identifizieren
# Die letzte Revision mit STATUS "deployed" VOR dem fehlerhaften Deploy
# Beispiel: Revision 5 = deployed (gut), Revision 6 = failed (schlecht)

# 3. Rollback durchführen
helm rollback onyx-{env} {REVISION} -n onyx-{env}
# Beispiel: helm rollback onyx-dev 5 -n onyx-dev

# 4. Rollout-Status prüfen
kubectl rollout status deployment/onyx-{env}-api-server -n onyx-{env} --timeout=5m
kubectl rollout status deployment/onyx-{env}-web-server -n onyx-{env} --timeout=5m
kubectl rollout status deployment/onyx-{env}-celery-worker-primary -n onyx-{env} --timeout=5m

# 5. Smoke Test
DOMAIN=$(kubectl get configmap env-configmap -n onyx-{env} -o jsonpath='{.data.WEB_DOMAIN}')
curl -s -f "${DOMAIN}/api/health"

# 6. Pod-Status verifizieren
kubectl get pods -n onyx-{env}
```

### Environment-spezifisches Verhalten

| Environment | --atomic | Automatischer Rollback | Helm History Max |
|-------------|----------|----------------------|-----------------|
| DEV | Nein | Nein (bewusst, für Debugging) | 5 Revisionen |
| TEST | Ja | Ja (bei Fehler) | 5 Revisionen |
| PROD | Ja | Ja (bei Fehler) | 5 Revisionen |

**Hinweis**: Bei TEST/PROD mit `--atomic` rollt Helm automatisch zurück, wenn der Deploy fehlschlägt (Pods starten nicht, Smoke Test schlägt fehl). Ein manueller Rollback ist nur nötig, wenn der Deploy "erfolgreich" war, aber die Anwendung danach fehlerhaft ist.

---

## 2. Datenbank-Rollback (Alembic)

### Wann sicher

- Die Migration hat nur Spalten/Tabellen **hinzugefügt** (additive Änderung)
- Kein Datenverlust beim `downgrade`
- Keine anderen Services schreiben parallel in die betroffenen Tabellen

### Wann NICHT sicher

- Die Migration hat Spalten **gelöscht** oder **umbenannt**
- Die Migration hat Daten transformiert (z.B. `UPDATE` auf bestehende Rows)
- Mehrere Migrationen müssen gleichzeitig zurückgerollt werden

### Schritt-für-Schritt

```bash
# 1. Aktuelle Migration prüfen
# Im API-Server Pod:
kubectl exec -n onyx-{env} deployment/onyx-{env}-api-server -- \
  python -c "from alembic.config import Config; from alembic import command; \
  config = Config('alembic.ini'); command.current(config)"

# 2. Eine Migration zurück
kubectl exec -n onyx-{env} deployment/onyx-{env}-api-server -- \
  alembic downgrade -1

# 3. Prüfen ob Downgrade erfolgreich
kubectl exec -n onyx-{env} deployment/onyx-{env}-api-server -- \
  alembic current
```

### PG-Backup-Restore (letzter Ausweg)

Falls ein Alembic-Downgrade nicht möglich ist:

1. StackIT Support kontaktieren
2. Point-in-Time Recovery (PITR) oder letztes tägliches Backup anfordern
3. Backup-Zeitpunkt bestimmen:
   - DEV: Tägliches Backup um 02:00 UTC
   - TEST: Tägliches Backup um 03:00 UTC
4. **Achtung**: Alle Daten nach dem Backup-Zeitpunkt gehen verloren

---

## 3. Kommunikation

### Wer wird wann informiert

| Severity | Informieren | Wann | Wie |
|----------|------------|------|-----|
| P1 (System down) | VÖB Operations + CISO | Sofort (innerhalb 15 Min) | E-Mail + Telefon |
| P2 (Teilausfall) | VÖB Operations | Innerhalb 1 Stunde | E-Mail |
| P3 (Minor, Workaround) | VÖB (optional) | Im nächsten Status-Update | E-Mail |
| P4 (Kosmetisch) | Keine externe Kommunikation | -- | -- |

### Kommunikationsvorlage (Rollback)

```
Betreff: [P{X}] VÖB Service Chatbot — Rollback auf {ENV}

Umgebung: {DEV/TEST/PROD}
Zeitpunkt: {YYYY-MM-DD HH:MM UTC}
Auswirkung: {Beschreibung}
Maßnahme: Rollback auf Version {vX.Y.Z} / Helm Revision {N}
Status: {Wiederhergestellt / In Bearbeitung}
Nächster Schritt: {Root Cause Analysis / Hotfix geplant}
```

---

## 4. Post-Mortem

Nach jedem Rollback auf TEST oder PROD wird eine Fehleranalyse durchgeführt.

### Post-Mortem Vorlage

```markdown
# Post-Mortem: [Titel]

**Datum**: YYYY-MM-DD
**Severity**: P1/P2/P3
**Dauer**: HH:MM (von Erkennung bis Wiederherstellung)
**Umgebung**: DEV/TEST/PROD

## Timeline
- **HH:MM UTC**: Problem erkannt (wie?)
- **HH:MM UTC**: Assessment begonnen
- **HH:MM UTC**: Rollback durchgeführt
- **HH:MM UTC**: Service wiederhergestellt
- **HH:MM UTC**: Root Cause identifiziert

## Root Cause
[Was war die eigentliche Ursache?]

## Impact
[Was war betroffen? Wie viele User? Datenverlust?]

## Maßnahmen
### Sofort (bereits umgesetzt)
- [Was wurde getan, um den Service wiederherzustellen?]

### Kurzfristig (nächste 7 Tage)
- [Hotfix, Konfigurationsänderung etc.]

### Langfristig (nächster Meilenstein)
- [Strukturelle Änderungen, um Wiederholung zu verhindern]

## Lessons Learned
- [Was lief gut?]
- [Was lief schlecht?]
- [Was ändern wir am Prozess?]
```

### Ablage

Post-Mortems werden in `docs/incidents/` abgelegt (Dateiname: `YYYY-MM-DD-{kurzbeschreibung}.md`).

---

## Referenzen

- Helm Deploy Runbook: `docs/runbooks/helm-deploy.md`
- CI/CD Pipeline Runbook: `docs/runbooks/ci-cd-pipeline.md`
- Betriebskonzept (Rollback-Strategie): `docs/betriebskonzept.md`
- Sicherheitskonzept (Incident Response): `docs/sicherheitskonzept.md`
