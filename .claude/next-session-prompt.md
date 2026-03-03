# Nächste Session — TEST LIVE, Aufräumen + Weiter

## Wo wir stehen (2026-03-03)

**TEST ist LIVE unter `http://188.34.118.201`.** 9 Pods Running (redis-operator läuft im default Namespace), Health Check OK.

## Ausstehender Commit

**Noch NICHT committed/gepusht.** Geänderte Dateien:
- `deployment/helm/values/values-test.yaml` — PG-Host eingetragen, DOMAIN/WEB_DOMAIN auf 188.34.118.201, nginx-test IngressClass
- `.claude/rules/voeb-projekt-status.md` — TEST LIVE Status
- `docs/CHANGELOG.md` — TEST LIVE Eintrag

Commit-Text:
```
chore(stackit-infra): TEST-Umgebung live — PG-Host, Domain, IngressClass

- values-test.yaml: POSTGRES_HOST eingetragen (d371f38d-...onstackit.cloud)
- values-test.yaml: DOMAIN/WEB_DOMAIN auf 188.34.118.201 (LoadBalancer)
- values-test.yaml: Eigene IngressClass nginx-test (Conflict mit DEV vermieden)
- Projektstatus + CHANGELOG: TEST LIVE dokumentiert
```

## Was in dieser Session erledigt wurde

1. ✅ Commit + Push: TEST-Vorbereitung (Terraform, Helm, ADR-004)
2. ✅ Terraform Auth: `~/.stackit/credentials.json` Wrapper → SA Key, chmod 600
3. ✅ SEC-01: PG ACL auf 188.34.93.194/32 + 109.41.112.160/32 eingeschränkt
4. ✅ terraform apply DEV: Node Pool 1→2, PG ACL live
5. ✅ terraform apply TEST: PG Flex `vob-test` + Bucket `vob-test`
6. ✅ Namespace `onyx-test` + Image Pull Secret + DB `onyx`
7. ✅ GitHub Environment `test` + 5 Secrets (PG, Redis, S3)
8. ✅ S3-Credentials für TEST separat erstellt (Enterprise-Trennung)
9. ✅ Erster Helm Deploy: `onyx-test` mit eigener IngressClass `nginx-test`
10. ✅ Health Check OK: `http://188.34.118.201/api/health` → 200

## Nächste Schritte

### Sofort (nächste Session)
1. **Commit + Push** der values-test.yaml + Status-Änderungen
2. **Helm Upgrade** mit korrekter DOMAIN (aktuell noch Platzhalter im Live-Cluster)
3. **CI/CD verifizieren**: `workflow_dispatch` für TEST ausführen
4. **LLM konfigurieren**: GPT-OSS 120B + Qwen3-VL in TEST Admin UI
5. **Login testen**: `http://188.34.118.201` im Browser öffnen

### Danach
- Embedding-Modell (E5 Mistral 7B) konfigurieren
- DNS + TLS (wenn VÖB DNS-Einträge liefert)
- SEC-02 bis SEC-07 vor PROD

## Wichtige Details

### Cluster-Egress-IP
- `188.34.93.194` — fest für Cluster-Lifecycle (StackIT NAT Gateway)

### TEST-Infrastruktur
- PG Host: `d371f38d-2ad5-458c-af27-c84f3004f1ba.postgresql.eu01.onstackit.cloud`
- PG Port: 5432
- Bucket: `vob-test`
- LoadBalancer: `188.34.118.201`
- Namespace: `onyx-test`
- IngressClass: `nginx-test`
- S3 Access Key ID: `EDDVRCB1NPDTFG88JAOS`

### K8s-Warnung
- `FreeDiskSpaceFailed` auf Node 1 — Disk fast voll, garbage collection findet nichts
- Kubernetes 1.32.12 deprecated — Update planen (1.33+)

### StackIT CLI
- Authentifiziert als SA `voeb-terraform-ys1hb4i8@sa.stackit.cloud`
- Kann `stackit auth login` für persönlichen Zugang nutzen
