# ===========================================================
# TEST Environment — VÖB Service Chatbot
# ===========================================================
# Provisioniert NUR Daten-Services (kein eigener Cluster!):
#   - 1× PostgreSQL Flex 2.4 Single (2 CPU, 4 GB)
#   - 1× Object Storage Bucket (vob-test)
#
# Der SKE-Cluster wird mit DEV geteilt (Node Pool "devtest",
# 2 Nodes). Siehe ADR-004 für die Begründung.
#
# Geschätzte Kosten TEST-Daten: ~35 EUR/Monat
# ===========================================================

module "stackit_data" {
  source = "../../modules/stackit-data"

  project_id  = var.project_id
  region      = "eu01"
  environment = "test"

  # PostgreSQL Flex 2.4 Single (identisch zu DEV)
  pg_flavor = {
    cpu = 2
    ram = 4
  }
  pg_replicas        = 1
  pg_storage_size    = 20
  pg_backup_schedule = "0 3 * * *" # 03:00 UTC (1h nach DEV, kein Overlap)
  # SEC-01: PG ACL auf Cluster-Egress-IP + Admin eingeschränkt (2026-03-03)
  # Gleicher Cluster wie DEV (ADR-004) → gleiche Egress-IP
  pg_acl = [
    "188.34.93.194/32",  # SKE Cluster Egress (alle Pods)
    "109.41.112.160/32", # Admin (Nikolaj Ivanov)
  ]

  # Object Storage
  bucket_name = "vob-test"
}

# --- Variables ---

variable "project_id" {
  description = "StackIT Project ID"
  type        = string
}

# --- Outputs ---

output "pg_host" {
  description = "PostgreSQL Host"
  value       = module.stackit_data.pg_host
}

output "pg_port" {
  description = "PostgreSQL Port"
  value       = module.stackit_data.pg_port
}

output "pg_password" {
  description = "PostgreSQL Passwort"
  value       = module.stackit_data.pg_password
  sensitive   = true
}

output "pg_readonly_password" {
  description = "PostgreSQL Read-Only Passwort"
  value       = module.stackit_data.pg_readonly_password
  sensitive   = true
}

output "bucket_name" {
  description = "S3 Bucket Name"
  value       = module.stackit_data.bucket_name
}
