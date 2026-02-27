# ===========================================================
# DEV Environment — VÖB Service Chatbot
# ===========================================================
# Provisioniert:
#   - 1× SKE Cluster (1 Node: g1a.4d, 4 vCPU, 16 GB)
#   - 1× PostgreSQL Flex 2.4 Single (2 CPU, 4 GB)
#   - 1× Object Storage Bucket (vob-dev)
#
# Geschätzte Kosten: ~250 EUR/Monat
# ===========================================================

module "stackit" {
  source = "../../modules/stackit"

  project_id  = var.project_id
  region      = "eu01"
  environment = "dev"

  # SKE Cluster
  cluster_name       = "vob-chatbot"
  kubernetes_version = "1.32"
  availability_zones = ["eu01-3"]

  node_pool = {
    machine_type = "g1a.4d"
    minimum      = 1
    maximum      = 1
    volume_size  = 50
    volume_type  = "storage_premium_perf2"
  }

  # PostgreSQL Flex 2.4 Single
  pg_flavor = {
    cpu = 2
    ram = 4
  }
  pg_replicas        = 1
  pg_storage_size    = 20
  pg_backup_schedule = "0 2 * * *"
  pg_acl             = ["0.0.0.0/0"]

  # Object Storage
  bucket_name = "vob-dev"
}

# --- Variables ---

variable "project_id" {
  description = "StackIT Project ID"
  type        = string
}

# --- Outputs ---

output "kubeconfig" {
  description = "Kubeconfig für kubectl"
  value       = module.stackit.kubeconfig
  sensitive   = true
}

output "pg_host" {
  description = "PostgreSQL Host"
  value       = module.stackit.pg_host
}

output "pg_port" {
  description = "PostgreSQL Port"
  value       = module.stackit.pg_port
}

output "pg_password" {
  description = "PostgreSQL Passwort"
  value       = module.stackit.pg_password
  sensitive   = true
}

output "pg_readonly_password" {
  description = "PostgreSQL Read-Only Passwort"
  value       = module.stackit.pg_readonly_password
  sensitive   = true
}

output "bucket_name" {
  description = "S3 Bucket Name"
  value       = module.stackit.bucket_name
}
