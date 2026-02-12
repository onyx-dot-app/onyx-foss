# Runbooks — VÖB Service Chatbot

Verifizierte Step-by-Step-Anleitungen für Setup, Deployment und Betrieb der StackIT-Infrastruktur.

> **Hinweis:** Diese Runbooks dokumentieren die **tatsächlich funktionierenden Schritte** — nicht den ursprünglichen Plan. Abweichungen vom [Implementierungsplan](../referenz/stackit-implementierungsplan.md) sind als solche gekennzeichnet.

## Reihenfolge

| # | Runbook | Status | Beschreibung |
|---|---------|--------|-------------|
| 1 | [stackit-projekt-setup.md](./stackit-projekt-setup.md) | Verifiziert | StackIT CLI, Service Account, Container Registry |
| 2 | stackit-terraform-deploy.md | Ausstehend | Terraform init/plan/apply (SKE, PG, Storage) |
| 3 | stackit-k8s-namespace.md | Ausstehend | Namespace, Secrets, Resource Quota |
| 4 | stackit-helm-deploy.md | Ausstehend | Helm Install/Upgrade Onyx |
| 5 | stackit-ci-cd.md | Ausstehend | GitHub Actions Pipeline konfigurieren |
| 6 | stackit-troubleshooting.md | Ausstehend | Häufige Fehler + Lösungen |

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
