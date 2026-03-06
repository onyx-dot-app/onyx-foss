# Naechste Session — Offene Themen

## Kontext (2026-03-06)

### Erledigte Themen dieser Session
1. **Kostenvergleich Node-Upgrade** — Dokument komplett, alle Preise gegen StackIT Preisliste v1.0.36 verifiziert
   - `docs/referenz/kostenvergleich-node-upgrade.md` + PDF
   - IST DEV+TEST: 585,29 EUR | SOLL (g1a.8d): 868,47 EUR | PROD: 963,96 EUR | GESAMT: 1.832,43 EUR
2. **Review-Gegenvorschlag analysiert** — Review hatte falsche Helm-Keys, zu niedrige Memory-Limits, Rechenfehler
   - `docs/referenz/review-antwort-node-upgrade.md` + PDF
   - Fazit: g1a.4d kann mit Tuning funktionieren, erst deployen + monitoren, dann entscheiden
3. **Upstream-Analyse** — Embedding-Blocker aufgehoben (PR #9005), Lightweight Worker entfernt (PR #9014)

### Offene Themen (Prioritaet)

**1. Nikos Infrastruktur-Frage** — wurde angekuendigt aber noch nicht gestellt. Direkt fragen.

**2. TLS/HTTPS aktivieren** — BLOCKIERT durch Cloudflare API Token
- cert-manager installiert, ClusterIssuers ready, Certificates blocked
- Wartet auf Token-Fix von Leif (E-Mail gesendet)
- Details: MEMORY.md Section "DNS/TLS Setup"
- Runbook: `docs/runbooks/dns-tls-setup.md`

**3. Upstream-Merge (57 Commits)** — nach Node-Upgrade-Entscheidung
- Entfernt Lightweight Worker Mode (PR #9014)
- Erfordert: `USE_LIGHTWEIGHT_BACKGROUND_WORKER` entfernen, 6 Worker aktivieren
- Worker Resource Requests in values-dev.yaml + values-test.yaml setzen
- Empfohlene Werte: siehe `docs/referenz/review-antwort-node-upgrade.md` Section 7

**4. Embedding-Modell wechseln** — nach Upstream-Merge
- Von nomic-embed-text-v1 auf Qwen3-VL-Embedding 8B (StackIT AI Model Serving)
- Konfiguration ueber Admin UI, Re-Index im Hintergrund

**5. Entra ID (Phase 3)** — Termin war 06.03, Status pruefen

## Referenz-Dokumente
| Thema | Datei |
|-------|-------|
| Kostenvergleich (verifiziert) | `docs/referenz/kostenvergleich-node-upgrade.md` |
| Review-Antwort | `docs/referenz/review-antwort-node-upgrade.md` |
| TLS-Runbook | `docs/runbooks/dns-tls-setup.md` |
| Helm Values DEV | `deployment/helm/values/values-dev.yaml` |
| Helm Values TEST | `deployment/helm/values/values-test.yaml` |
| Helm Chart Defaults | `deployment/helm/charts/onyx/values.yaml` |
| Projektstatus | `.claude/rules/voeb-projekt-status.md` |

## Regeln
- `--no-verify` nutzen
- NIEMALS Co-Authored-By fuer Claude
- Helm Chart Templates READ-ONLY
- Kein Commit ohne Nikos Freigabe
- Feature-Branch Pflicht
