# Naechste Session — DNS/TLS aktivieren (C1)

## Wo wir stehen (2026-03-05)

**Security Quick Wins committed + deployed:** `27dec3dcf` (C6, H8, H11) — DEV + TEST verifiziert.
**CHANGELOG + Projektstatus:** Geaendert, noch NICHT committed (2 Dateien).
**DNS A-Records:** Gesetzt, loesen korrekt auf.
**Cloudflare API Token:** Erhalten von Leif.

---

## VOR DEM TLS-SETUP: 2 offene Commits

### Commit 1: Doku-Nachtrag (CHANGELOG + Projektstatus)
Dateien sind bereits geaendert, muessen nur committed werden:
- `docs/CHANGELOG.md` — 3 Quick Wins + Audit-Dokument als Security-Eintraege
- `.claude/rules/voeb-projekt-status.md` — Audit + Quick Wins ergaenzt, JNnovate-Blocker entfernt

### Commit 2 (optional): Runbook-Fix
- `docs/runbooks/dns-tls-setup.md` Zeile 601: `configMap.DB_READONLY_PASSWORD` → `auth.dbreadonly.values.db_readonly_password` (veraltet nach C6-Fix)

---

## BLOCKER: Cloudflare Proxy auf DNS-only umstellen

DNS loest auf, ABER ueber `cdn.cloudflare.net` (Proxy AN = orange Wolke).
**Leif muss in Cloudflare beide A-Records auf "DNS only" (graue Wolke) umstellen.**

Ohne das:
- Traffic geht ueber US-Infrastruktur (DSGVO-Verstoss)
- Cloudflare terminiert TLS (unser cert-manager waere wirkungslos)

Pruefung ob umgestellt:
```bash
dig +short dev.chatbot.voeb-service.de
# Erwartung: NUR "188.34.74.187" (kein cdn.cloudflare.net davor)
```

---

## AUFGABE: DNS/TLS Setup (Runbook Teil B, Schritte 1-6)

**Runbook:** `docs/runbooks/dns-tls-setup.md`
**Voraussetzung:** Cloudflare Proxy = DNS-only (graue Wolke)

### Reihenfolge (kritisch!)

1. **Pruefen:** DNS-only (kein cloudflare.net CNAME)
2. **Schritt 1:** cert-manager installieren (`helm install cert-manager jetstack/cert-manager`)
3. **Schritt 2:** Cloudflare API Token als K8s Secret
4. **Schritt 3a:** Staging ClusterIssuers erstellen (DEV + TEST)
5. **Schritt 3c:** Explizite Certificate-Ressourcen (ECDSA P-384, BSI-konform) — VOR Helm Deploy!
6. **Gate-Check:** Alle Voraussetzungen pruefen (DNS, Issuers READY, Certs READY)
7. **Schritt 4:** Helm Values anpassen (DOMAIN, WEB_DOMAIN → https://, ingress-Block)
8. **Schritt 5:** Deploy DEV, verifizieren, dann TEST
9. **Schritt 3b:** Staging → Production ClusterIssuers umschalten
10. **Schritt 6:** Vollstaendige Verifikation (BSI ECDSA P-384, HTTP→HTTPS Redirect, Login)

### Wichtige Hinweise
- `letsencrypt.enabled` bleibt `false` (eigener ClusterIssuer statt Chart-eigener)
- Certificates MUESSEN VOR dem Helm Deploy existieren (sonst erstellt Ingress-Shim RSA-2048)
- Erster TLS-Deploy besser manuell (nicht CI/CD) — cert-manager braucht 1-2 Min fuer Zertifikate
- Nach TLS: CI/CD Smoke Test funktioniert automatisch (liest WEB_DOMAIN aus ConfigMap)

---

## Regeln (Erinnerung)
- `--no-verify` nutzen
- NIEMALS Co-Authored-By fuer Claude
- Helm Chart Templates READ-ONLY
- Kein Commit ohne Nikos Freigabe
