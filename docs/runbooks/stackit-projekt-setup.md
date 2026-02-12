# Runbook 1: StackIT Projekt-Setup

**Zuletzt verifiziert:** 2026-02-12
**Ausgeführt von:** Nikolaj Ivanov
**Dauer:** ca. 30 Minuten (ohne Wartezeit auf Berechtigungen)

---

## Voraussetzungen

- StackIT Account mit Zugang zur Organisation
- StackIT Projekt angelegt (über Portal)
- macOS mit Homebrew
- Docker installiert

## Ergebnisse nach diesem Runbook

- StackIT CLI installiert und eingeloggt
- Service Account für Terraform erstellt
- Service Account Key generiert und sicher abgelegt
- Container Registry aktiviert und eingeloggt
- Service Account hat `project.admin`-Rolle

---

## Schritt 1: StackIT CLI installieren

```bash
brew tap stackitcloud/tap
brew install --cask stackit
```

**Validierung:**
```bash
stackit --version
```

**Quelle:** [StackIT CLI Installation](https://github.com/stackitcloud/stackit-cli/blob/main/INSTALLATION.md)

---

## Schritt 2: CLI Login

```bash
stackit auth login
```

Öffnet den Browser automatisch. Mit StackIT-Credentials anmelden.

**Erwartete Ausgabe:** `Successfully logged into STACKIT CLI.`

---

## Schritt 3: Service Account erstellen

Der Service Account ist ein maschineller API-User für Terraform und CI/CD.

```bash
stackit service-account create \
  --name "voeb-terraform" \
  --project-id <PROJECT_ID>
```

> **Hinweis:** Name max. 20 Zeichen.

**Erwartete Ausgabe:**
```
Created service account for project "...". Email: voeb-terraform-XXXXXXXX@sa.stackit.cloud
```

Die Email-Adresse notieren — wird in allen folgenden Schritten benötigt.

---

## Schritt 4: Service Account Key generieren

```bash
stackit service-account key create \
  --email "<SA_EMAIL>" \
  --project-id <PROJECT_ID>
```

> **Hinweis:** Email in Anführungszeichen setzen, da das `@`-Zeichen sonst vom Terminal interpretiert wird.

**Erwartete Ausgabe:** JSON mit `active`, `createdAt`, `credentials`.

---

## Schritt 5: Credentials sicher ablegen

Credentials **außerhalb** des Repos speichern:

```bash
mkdir -p ~/.stackit
nano ~/.stackit/voeb-terraform-credentials.json
```

Kompletten JSON-Output aus Schritt 4 einfügen. Speichern mit `Ctrl+O` → `Enter` → `Ctrl+X`.

Umgebungsvariable setzen:

```bash
export STACKIT_SERVICE_ACCOUNT_KEY_PATH=~/.stackit/voeb-terraform-credentials.json
```

Für permanente Verfügbarkeit in `~/.zshrc` eintragen.

**Validierung:**
```bash
ls -la ~/.stackit/voeb-terraform-credentials.json
```

> **WICHTIG:** Diese Datei darf NIEMALS ins Git-Repository.

---

## Schritt 6: Service Account Berechtigungen

Der Service Account braucht eine Projekt-Rolle, um Ressourcen anlegen zu können. Dafür ist ein User mit `project.owner`-Rolle erforderlich.

```bash
stackit project member add <SA_EMAIL> \
  --project-id <PROJECT_ID> \
  --role project.admin
```

Falls 403 Forbidden — eigene Rolle prüfen:
```bash
stackit project member list --project-id <PROJECT_ID>
```

Benötigt mindestens `project.owner`. Falls nicht vorhanden → Org-Admin kontaktieren.

**Quelle:** [stackit project member add](https://github.com/stackitcloud/stackit-cli/blob/main/docs/stackit_project_member_add.md)

---

## Schritt 7: Container Registry aktivieren

Die Aktivierung erfolgt über das StackIT Portal:

1. [StackIT Portal](https://portal.stackit.cloud/) öffnen
2. Sidebar → **Container Registry**
3. "Go to Container Registry" klicken
4. Mit StackIT-Credentials anmelden

**Docker Login:**
```bash
docker login registry.onstackit.cloud
# Username: StackIT-Email
# Password: CLI Secret (Portal → Profilbild → User Profile)
```

Für CI/CD später einen **Robot Account** in der Registry-Oberfläche erstellen.

**Quelle:** [Container Registry — Getting Started](https://docs.stackit.cloud/products/developer-platform/container-registry/getting-started/getting-started-with-container-registry/)

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| SA-Name `too long (must be at most 20 chars)` | Max. 20 Zeichen verwenden |
| `403 Forbidden` bei Key-Erstellung | Email in `"Anführungszeichen"` setzen |
| `403 Forbidden` bei Rollenvergabe | Org-Admin kontaktieren, eigene Rolle prüfen |
| `No such file or directory` bei Credentials | `mkdir -p ~/.stackit` zuerst ausführen |

---

## Nächster Schritt

Sobald der Service Account die `project.admin`-Rolle hat → weiter mit [Runbook 2: Terraform Deploy](./stackit-terraform-deploy.md).
