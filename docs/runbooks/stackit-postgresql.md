# Runbook: StackIT PostgreSQL Flex — Betriebswissen

**Zuletzt verifiziert:** 2026-02-27
**Ausgeführt von:** Nikolaj Ivanov

---

## Kontext

StackIT PostgreSQL Flex ist ein Managed Database Service. Im Vergleich zu selbst betriebenen PostgreSQL-Instanzen gibt es wichtige Unterschiede die beim Betrieb beachtet werden müssen.

---

## Datenbank anlegen

Terraform erstellt die PG-Instanz und den Applikations-User, aber NICHT die Datenbank selbst. Die Datenbank muss manuell angelegt werden bevor Onyx starten kann.

### Voraussetzung
- PG Flex Instanz provisioniert (terraform apply)
- User-Credentials aus `terraform output pg_password`
- kubectl Zugriff auf den Cluster (für temporären Pod)

### Befehl (via temporären Pod)

```bash
kubectl run pg-createdb --restart=Never --namespace onyx-dev \
  --image=postgres:16-alpine \
  --env="PGPASSWORD=<PG_PASSWORD>" \
  --command -- psql -h <PG_HOST> -p 5432 -U onyx_app -d postgres \
  -c "CREATE DATABASE onyx OWNER onyx_app ENCODING 'UTF8';"

# Ergebnis prüfen
sleep 8 && kubectl logs pg-createdb -n onyx-dev
# Erwartete Ausgabe: "CREATE DATABASE"

# Aufräumen
kubectl delete pod pg-createdb -n onyx-dev
```

### Validierung

```bash
kubectl run pg-check --restart=Never --namespace onyx-dev \
  --image=postgres:16-alpine \
  --env="PGPASSWORD=<PG_PASSWORD>" \
  --command -- psql -h <PG_HOST> -p 5432 -U onyx_app -d onyx -c "SELECT 1;"

sleep 5 && kubectl logs pg-check -n onyx-dev
kubectl delete pod pg-check -n onyx-dev
```

---

## Managed PG: Kein CREATEROLE

StackIT PG Flex erlaubt NICHT, dass App-User andere Rollen erstellen. Der Terraform-Provider unterstützt nur die Rollen `login` und `createdb`.

### Auswirkung auf Onyx

Die Alembic-Migration `495cb26ce93e_create_knowlege_graph_tables.py` versucht beim Startup einen `db_readonly_user` per SQL anzulegen (`CREATE USER`). Das schlägt fehl mit:

```
asyncpg.exceptions.InsufficientPrivilegeError: permission denied to create role
```

### Lösung

Den `db_readonly_user` als separate `stackit_postgresflex_user`-Resource in Terraform anlegen:

```hcl
resource "stackit_postgresflex_user" "readonly" {
  project_id  = var.project_id
  instance_id = stackit_postgresflex_instance.main.instance_id
  username    = "db_readonly_user"
  roles       = ["login"]
}
```

Das Passwort wird automatisch generiert. Es muss als `DB_READONLY_PASSWORD` ENV-Variable in den Pods landen (über configMap in values-dev-secrets.yaml, gitignored).

Die Alembic-Migration prüft per `IF NOT EXISTS` ob der User existiert und überspringt die Erstellung wenn er bereits vorhanden ist.

---

## Verfügbare User-Rollen

| Rolle | Bedeutung | Terraform |
|-------|-----------|-----------|
| `login` | Kann sich anmelden | Standard |
| `createdb` | Kann Datenbanken erstellen | Für App-User |
| `createrole` | Kann Rollen erstellen | **NICHT verfügbar** auf StackIT PG Flex |
| `superuser` | Volle Admin-Rechte | **NICHT verfügbar** auf StackIT PG Flex |

---

## Verbindung testen (ohne lokales psql)

Temporärer Pod mit PostgreSQL-Client:

```bash
kubectl run pg-client --restart=Never --namespace onyx-dev \
  --image=postgres:16-alpine \
  --env="PGPASSWORD=<PG_PASSWORD>" \
  --command -- psql -h <PG_HOST> -p 5432 -U onyx_app -d onyx -c "\dt"

sleep 8 && kubectl logs pg-client -n onyx-dev
kubectl delete pod pg-client -n onyx-dev
```

---

## Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `database "onyx" does not exist` | DB nicht angelegt nach Terraform | DB manuell anlegen (siehe oben) |
| `permission denied to create role` | Managed PG hat kein CREATEROLE | User per Terraform anlegen |
| `Connection refused` | PG Flex ACL blockiert | ACL in `variables.tf` prüfen (aktuell `0.0.0.0/0` für DEV) |
| `password authentication failed` | Falsches Passwort | `terraform output -raw pg_password` prüfen |
