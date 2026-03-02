# ===========================================================
# VÖB Service Chatbot — StackIT Infrastructure
# ===========================================================
# Provisioniert: SKE Cluster, PostgreSQL Flex, Object Storage
# Region: EU01 (Frankfurt)
#
# Aktuell: Nur DEV-Setup (1 Node Pool, 1 PG Single, 1 Bucket)
# PROD Node Pool wird später ergänzt, wenn wir so weit sind.
# ===========================================================

provider "stackit" {
  default_region = var.region
}

# -----------------------------------------------------------
# 1. SKE Kubernetes Cluster
# -----------------------------------------------------------
# Ein Cluster mit einem Node Pool (devtest).
# PROD Node Pool wird in einem späteren Schritt hinzugefügt.
# -----------------------------------------------------------

resource "stackit_ske_cluster" "main" {
  project_id             = var.project_id
  name                   = var.cluster_name
  kubernetes_version_min = var.kubernetes_version

  node_pools = [
    {
      name               = "devtest"
      machine_type       = var.node_pool.machine_type
      minimum            = var.node_pool.minimum
      maximum            = var.node_pool.maximum
      availability_zones = var.availability_zones
      os_name            = "flatcar"
      volume_size        = var.node_pool.volume_size
      volume_type        = var.node_pool.volume_type
      labels = {
        "environment" = var.environment
        "project"     = "voeb-chatbot"
      }
    }
  ]

  maintenance = {
    enable_kubernetes_version_updates    = true
    enable_machine_image_version_updates = true
    start                                = "02:00:00Z"
    end                                  = "04:00:00Z"
  }

  extensions = {
    acl = {
      enabled       = true
      allowed_cidrs = var.cluster_acl
    }
  }
}

# Kubeconfig für kubectl/Helm Zugriff
resource "stackit_ske_kubeconfig" "main" {
  project_id   = var.project_id
  cluster_name = stackit_ske_cluster.main.name
}

# -----------------------------------------------------------
# 2. PostgreSQL Flex
# -----------------------------------------------------------
# DEV: Flex 2.4 Single (2 CPU, 4 GB, 1 Replica)
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
}

# Applikations-User (Passwort wird automatisch generiert)
resource "stackit_postgresflex_user" "app" {
  project_id  = var.project_id
  instance_id = stackit_postgresflex_instance.main.instance_id
  username    = "onyx_app"
  roles       = ["login", "createdb"]
}

# Read-Only User für Knowledge Graph Queries
# Onyx erstellt diesen User normalerweise per Alembic-Migration,
# aber Managed PG (StackIT Flex) erlaubt kein CREATEROLE.
resource "stackit_postgresflex_user" "readonly" {
  project_id  = var.project_id
  instance_id = stackit_postgresflex_instance.main.instance_id
  username    = "db_readonly_user"
  roles       = ["login"]
}

# -----------------------------------------------------------
# 3. Object Storage (S3-kompatibel)
# -----------------------------------------------------------

resource "stackit_objectstorage_bucket" "main" {
  project_id = var.project_id
  name       = var.bucket_name
}
