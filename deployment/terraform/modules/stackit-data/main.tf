# ===========================================================
# VÖB Service Chatbot — StackIT Data Services (ohne Cluster)
# ===========================================================
# Provisioniert nur PostgreSQL Flex + Object Storage.
# Für Environments die einen bestehenden SKE-Cluster mitnutzen
# (z.B. TEST im shared DEV+TEST Cluster, siehe ADR-004).
# ===========================================================

provider "stackit" {
  default_region = var.region
}

# -----------------------------------------------------------
# 1. PostgreSQL Flex
# -----------------------------------------------------------

resource "stackit_postgresflex_instance" "main" {
  project_id      = var.project_id
  name            = "vob-${var.environment}"
  version         = var.pg_version
  acl             = var.pg_acl
  backup_schedule = var.pg_backup_schedule

  flavor = {
    cpu = var.pg_flavor.cpu
    ram = var.pg_flavor.ram
  }

  replicas = var.pg_replicas

  storage = {
    class = var.pg_storage_class
    size  = var.pg_storage_size
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Applikations-User (Passwort wird automatisch generiert)
resource "stackit_postgresflex_user" "app" {
  project_id  = var.project_id
  instance_id = stackit_postgresflex_instance.main.instance_id
  username    = "onyx_app"
  roles       = ["login", "createdb"]
}

# Read-Only User für Knowledge Graph Queries
# Managed PG (StackIT Flex) erlaubt kein CREATEROLE — deshalb per Terraform.
resource "stackit_postgresflex_user" "readonly" {
  project_id  = var.project_id
  instance_id = stackit_postgresflex_instance.main.instance_id
  username    = "db_readonly_user"
  roles       = ["login"]
}

# -----------------------------------------------------------
# 2. Object Storage (S3-kompatibel)
# -----------------------------------------------------------

resource "stackit_objectstorage_bucket" "main" {
  project_id = var.project_id
  name       = var.bucket_name
}
