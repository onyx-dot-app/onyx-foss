# Runbooks — VÖB Service Chatbot

Verifizierte Step-by-Step-Anleitungen für Setup, Deployment und Betrieb der StackIT-Infrastruktur.

> **Hinweis:** Diese Runbooks dokumentieren die **tatsächlich funktionierenden Schritte** — nicht den ursprünglichen Plan. Abweichungen vom [Implementierungsplan](../referenz/stackit-implementierungsplan.md) sind als solche gekennzeichnet.

## Reihenfolge

| # | Runbook | Status | Beschreibung |
|---|---------|--------|-------------|
| 1 | [stackit-projekt-setup.md](./stackit-projekt-setup.md) | ✅ Verifiziert | StackIT CLI, Service Account, Container Registry |
| 2 | [stackit-postgresql.md](./stackit-postgresql.md) | ✅ Verifiziert | DB anlegen, Readonly-User, Managed PG Einschränkungen |
| 3 | [helm-deploy.md](./helm-deploy.md) | ✅ Verifiziert | Helm Install/Upgrade, Secrets, Redis, Troubleshooting |
| 4 | [ci-cd-pipeline.md](./ci-cd-pipeline.md) | ✅ Verifiziert | CI/CD Pipeline: Deploy, Rollback, Secrets, Troubleshooting |
| 5 | [dns-tls-setup.md](./dns-tls-setup.md) | Entwurf | DNS A-Records, cert-manager, Let's Encrypt, Helm TLS |

## Konventionen

- **Voraussetzungen** stehen am Anfang jedes Runbooks
- **Validierung** steht am Ende — jeder Schritt hat ein erwartetes Ergebnis
- **Abweichungen** vom Implementierungsplan sind mit `> KORREKTUR:` markiert
- Platzhalter wie `<PROJECT_ID>` müssen durch echte Werte ersetzt werden
- Sensible Daten (Keys, Passwörter) werden **nie** in Runbooks dokumentiert

## Referenzen

- [StackIT Implementierungsplan](../referenz/stackit-implementierungsplan.md) — Ursprünglicher Plan
- [StackIT Infrastruktur-Referenz](../referenz/stackit-infrastruktur.md) — Architekturentscheidungen
- [StackIT CLI Docs](https://github.com/stackitcloud/stackit-cli)
- [StackIT Terraform Provider](https://registry.terraform.io/providers/stackitcloud/stackit/latest/docs)
