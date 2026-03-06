# Kostenoptimierung: DEV/TEST-Environments parken

**Stand:** 2026-03-06
**Erstellt von:** Nikolaj Ivanov (CCJ / Coffee Studios)
**Zweck:** Optionen zur Kostenreduktion bei Nichtnutzung von DEV- und TEST-Umgebungen

---

## 1. Zusammenfassung

DEV- und TEST-Umgebungen koennen bei laengerer Nichtnutzung (z.B. zwischen Meilensteinen)
teilweise oder vollstaendig heruntergefahren werden. Je nach Option lassen sich
**50-100% der laufenden Kosten** einsparen. Die Wiederherstellung ist vollstaendig
automatisierbar und dauert 15-60 Minuten.

---

## 2. Laufende Kosten DEV + TEST (Referenz)

| Service                    | EUR/Monat | Anteil  |
| -------------------------- | --------- | ------- |
| Worker Nodes (2x g1a.4d)  | 283,18    | 48,4%   |
| PostgreSQL Flex (2x)       | 211,08    | 36,1%   |
| SKE Cluster (Management)   | 71,71     | 12,3%   |
| Load Balancer (2x)         | 18,78     | 3,2%    |
| Object Storage (2x)        | 0,54      | < 0,1%  |
| **Gesamt**                 | **585,29**| **100%**|

> Alle Preise netto zzgl. MwSt. Quelle: StackIT Preisliste v1.0.36 (03.03.2026).
> Bei g1a.8d Nodes (nach Upstream-Merge): 868,47 EUR/Mo — Einsparungen entsprechend hoeher.

---

## 3. Optionen im Ueberblick

| Option | Einsparung/Mo | Parkkosten/Mo | Wiederherstellung | Datenverlust |
| ------ | ------------- | ------------- | ----------------- | ------------ |
| A: Nodes herunterskalieren | ~302 EUR | ~283 EUR | ~15 Min | Nein (PG bleibt) |
| B: Nodes + PG stoppen | ~513 EUR | ~72 EUR | ~30 Min | PG aus Backup |
| C: Alles loeschen | ~585 EUR | ~1 EUR | ~60 Min | Komplett neu |

---

## 4. Option A — Nodes herunterskalieren (empfohlen)

**Prinzip:** Kubernetes-Workloads entfernen, Node Pool auf 0 skalieren.
PostgreSQL und Object Storage laufen weiter.

### Was gespart wird

| Service               | Laufend   | Geparkt  | Ersparnis |
| --------------------- | --------- | -------- | --------- |
| Worker Nodes (2x)     | 283,18    | 0,00     | 283,18    |
| Load Balancer (2x)    | 18,78     | 0,00     | 18,78     |
| PostgreSQL Flex (2x)  | 211,08    | 211,08   | 0,00      |
| SKE Cluster           | 71,71     | 71,71    | 0,00      |
| Object Storage        | 0,54      | 0,54     | 0,00      |
| **Gesamt**            | **585,29**| **283,33**| **301,96**|

### Herunterfahren

```bash
# 1. Helm Releases entfernen (Pods, Services, Ingress werden geloescht)
helm uninstall onyx-dev -n onyx-dev
helm uninstall onyx-test -n onyx-test

# 2. Node Pool auf 0 skalieren (Terraform)
# In deployment/terraform/environments/dev/terraform.tfvars:
#   node_pool.minimum = 0
#   node_pool.maximum = 0
terraform apply

# 3. Verifizieren
kubectl get nodes  # Erwartung: keine Worker Nodes
```

### Hochfahren

```bash
# 1. Node Pool wieder hochskalieren
# In terraform.tfvars: minimum = 2, maximum = 2
terraform apply
# Warten bis Nodes Ready (~5 Min)
kubectl get nodes -w

# 2. Helm Releases neu installieren
helm upgrade --install onyx-dev deployment/helm/charts/onyx \
  -n onyx-dev \
  -f deployment/helm/values/values-common.yaml \
  -f deployment/helm/values/values-dev.yaml \
  --set auth.postgresql.values.password=$PG_PASSWORD \
  --set auth.redis.values.redis_password=$REDIS_PASSWORD \
  --set auth.dbreadonly.values.db_readonly_password=$DB_READONLY_PASSWORD \
  --set auth.objectstorage.values.s3_aws_access_key_id=$S3_ACCESS_KEY \
  --set auth.objectstorage.values.s3_aws_secret_access_key=$S3_SECRET_KEY

# (analog fuer onyx-test mit values-test.yaml)

# 3. Health Check
kubectl get pods -n onyx-dev -w  # Warten bis alle Running
curl -s http://<DEV-IP>/health | jq .
```

### Vorteile

- PostgreSQL-Daten bleiben vollstaendig erhalten (Konfiguration, Benutzer, Dokument-Metadaten)
- Kein Re-Index noetig (Vespa PVC wird geloescht, aber Re-Index startet automatisch beim Hochfahren)
- Kubeconfig bleibt gueltig (Cluster existiert weiterhin)
- DNS-Records muessen nicht geaendert werden (IP kann sich aendern — siehe Hinweis)
- Secrets in GitHub bleiben erhalten

### Hinweise

- **Load Balancer IP:** Beim Neuerstellen des Ingress-Controllers wird eine neue externe IP vergeben.
  DNS-Records (A-Records bei Cloudflare) muessen aktualisiert werden.
- **Vespa Re-Index:** Vespa-Daten liegen auf PersistentVolumeClaims. Nach `helm uninstall` werden
  PVCs standardmaessig beibehalten (`reclaimPolicy: Retain`). Pruefen mit `kubectl get pvc -n onyx-dev`.
- **Node Pool min=0:** Muss gegen StackIT SKE API verifiziert werden. Falls nicht unterstuetzt,
  Alternative: Node Pool komplett loeschen und neu erstellen (Terraform destroy/apply auf Node-Pool-Ebene).

---

## 5. Option B — Nodes + PostgreSQL stoppen

**Prinzip:** Wie Option A, zusaetzlich PostgreSQL Flex Instanzen loeschen.
Daten werden aus dem taeglichen Backup wiederhergestellt.

### Was gespart wird

| Service               | Laufend   | Geparkt | Ersparnis |
| --------------------- | --------- | ------- | --------- |
| Worker Nodes (2x)     | 283,18    | 0,00    | 283,18    |
| Load Balancer (2x)    | 18,78     | 0,00    | 18,78     |
| PostgreSQL Flex (2x)  | 211,08    | 0,00    | 211,08    |
| SKE Cluster           | 71,71     | 71,71   | 0,00      |
| Object Storage        | 0,54      | 0,54    | 0,00      |
| **Gesamt**            | **585,29**| **72,25**| **513,04**|

### Zusaetzliche Schritte beim Herunterfahren

```bash
# Nach Helm uninstall + Node-Skalierung:
# PostgreSQL Flex Instanzen loeschen
# ACHTUNG: lifecycle.prevent_destroy muss in Terraform temporaer entfernt werden
terraform destroy -target=stackit_postgresflex_instance.main
```

### Zusaetzliche Schritte beim Hochfahren

```bash
# 1. PostgreSQL neu provisionieren
terraform apply  # Erstellt PG Flex neu

# 2. Datenbank + User anlegen
# (Terraform erstellt onyx_app + db_readonly_user automatisch)

# 3. Datenbank 'onyx' anlegen (manuell oder per Script)
# Neues Passwort aus Terraform Output in GitHub Secrets aktualisieren

# 4. Helm install (wie Option A)
# Onyx fuehrt beim Start automatisch Alembic-Migrationen aus
```

### Risiken

- **Neue PG-Credentials:** Terraform generiert neue Passwoerter. GitHub Secrets muessen aktualisiert werden.
- **Neuer PG-Host:** Die Instanz bekommt eine neue UUID/Hostname. `values-dev.yaml` muss angepasst werden.
- **Datenverlust:** Alle Konfigurationen in der DB (LLM-Settings, Connectors, Benutzer) muessen
  neu eingerichtet werden, sofern kein PG-Dump vor dem Loeschen erstellt wurde.
- **Backup-Restore:** StackIT PG Flex Backups sind instanzgebunden — nach Loeschung der Instanz
  sind die Backups NICHT mehr verfuegbar. Vor dem Loeschen manuell `pg_dump` erstellen.

---

## 6. Option C — Alles loeschen

**Prinzip:** Komplette Infrastruktur per `terraform destroy` entfernen.
Nur Object Storage bleibt (separat verwaltet oder ebenfalls geloescht).

### Was gespart wird

Nahezu alles. Parkkosten: ~0,54 EUR/Mo (Object Storage) bzw. 0 EUR bei Loeschung.

### Wiederherstellung

```bash
# 1. Terraform apply (Cluster + PG + Bucket)
terraform apply  # ~15-20 Min

# 2. Kubeconfig holen
stackit ske kubeconfig create vob-chatbot --login

# 3. Namespaces + Secrets anlegen
kubectl create namespace onyx-dev
kubectl create namespace onyx-test
# Image Pull Secrets, Redis Operator, cert-manager neu installieren

# 4. Helm install (DEV + TEST)
# 5. DNS-Records aktualisieren (neue IPs)
# 6. TLS-Zertifikate neu ausstellen (cert-manager)
# 7. LLM-Konfiguration in Admin UI neu einrichten
```

### Risiken

- Hoechster Wiederherstellungsaufwand (~60 Min + manuelle Konfiguration)
- Neue IPs, neue PG-Hosts, neue Credentials — alles muss aktualisiert werden
- Kubeconfig-Ablauf wird zurueckgesetzt
- Alle manuellen K8s-Ressourcen (Secrets, NetworkPolicies) muessen neu applied werden

---

## 7. Entscheidungsmatrix

| Kriterium                    | Option A          | Option B          | Option C          |
| ---------------------------- | ----------------- | ----------------- | ----------------- |
| Einsparung pro Monat         | ~302 EUR (52%)    | ~513 EUR (88%)    | ~585 EUR (100%)   |
| Wiederherstellungszeit       | ~15 Min           | ~30 Min           | ~60 Min           |
| Automatisierbar              | Vollstaendig      | Weitgehend        | Weitgehend        |
| Datenverlust                 | Keiner            | PG (Backup noetig)| Alles             |
| DNS-Update noetig            | Moeglich (LB-IP)  | Moeglich          | Ja (neue IPs)     |
| Credentials-Update noetig    | Nein              | Ja (PG-Passwort)  | Ja (alles)        |
| Empfohlen fuer Pause von     | 1-4 Wochen        | 1-3 Monate        | > 3 Monate        |

---

## 8. Empfehlung

### Waehrend der aktiven Entwicklung (aktuell)

**DEV und TEST 24/7 laufen lassen.** Die Kosten von ~585 EUR/Mo stehen in keinem Verhaeltnis
zum Produktivitaetsverlust durch Warten auf Hochfahren. CI/CD-Pipelines, spontane Demos und
Tests erfordern jederzeit verfuegbare Environments.

### Zwischen Meilensteinen (z.B. nach M1-Abnahme)

**Option A anwenden**, wenn eine Pause von 2+ Wochen absehbar ist.
Park-Skripte (`scripts/park-env.sh`, `scripts/unpark-env.sh`) vorbereiten und im
Betriebskonzept dokumentieren.

### Nach Projektabschluss / PROD-Betrieb

**Option B oder C**, wenn DEV/TEST ueber Monate nicht benoetigt werden.
Vor dem Herunterfahren: `pg_dump` aller Datenbanken sichern.

---

## 9. Preisquellen

| Quelle | Verifiziert |
| ------ | ----------- |
| [StackIT Preisliste v1.0.36](https://stackit.com/en/prices/cloud) | 2026-03-05 |
| [StackIT Calculator](https://calculator.stackit.cloud/) | 2026-03-05 |

> Verwandtes Dokument: [Kostenvergleich Node-Upgrade](kostenvergleich-node-upgrade.md)
