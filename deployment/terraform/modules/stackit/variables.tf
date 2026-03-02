# ===========================================================
# VÖB Service Chatbot — StackIT Terraform Variables
# ===========================================================
# Aktuell: Nur DEV-relevante Variablen.
# PROD-spezifische Variablen kommen später dazu.
# ===========================================================

# --- Projekt ---

variable "project_id" {
  description = "StackIT Project ID (UUID)"
  type        = string
}

variable "region" {
  description = "StackIT Region"
  type        = string
  default     = "eu01"
}

variable "environment" {
  description = "Target environment"
  type        = string
  default     = "dev"
}

# --- SKE Cluster ---

variable "cluster_name" {
  description = "SKE Cluster name (max 11 chars)"
  type        = string
  default     = "vob-chatbot"
  validation {
    condition     = length(var.cluster_name) <= 11
    error_message = "SKE cluster name must be 11 characters or less."
  }
}

variable "kubernetes_version" {
  description = "Minimum Kubernetes version"
  type        = string
  default     = "1.32"
}

variable "availability_zones" {
  description = "Availability zones for node pools"
  type        = list(string)
  default     = ["eu01-3"]
}

variable "cluster_acl" {
  description = "Cluster API ACL — allowed CIDRs"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# --- Node Pool ---

variable "node_pool" {
  description = "Node pool configuration"
  type = object({
    machine_type = string
    minimum      = number
    maximum      = number
    volume_size  = number
    volume_type  = string
  })
  default = {
    machine_type = "g1a.4d"  # 4 vCPU, 16 GB RAM
    minimum      = 1
    maximum      = 1
    volume_size  = 50
    volume_type  = "storage_premium_perf2"
  }
}

# --- PostgreSQL Flex ---

variable "pg_version" {
  description = "PostgreSQL major version"
  type        = string
  default     = "16"
}

variable "pg_flavor" {
  description = "PostgreSQL Flex flavor (CPU + RAM in GB)"
  type = object({
    cpu = number
    ram = number
  })
  default = {
    cpu = 2
    ram = 4
  }
}

variable "pg_replicas" {
  description = "PostgreSQL Flex replicas (1 = Single, 3 = HA)"
  type        = number
  default     = 1
  validation {
    condition     = contains([1, 3], var.pg_replicas)
    error_message = "PostgreSQL Flex replicas must be 1 (single) or 3 (replica set)."
  }
}

variable "pg_storage_size" {
  description = "PostgreSQL storage size in GB"
  type        = number
  default     = 20
}

variable "pg_storage_class" {
  description = "PostgreSQL storage performance class"
  type        = string
  default     = "premium-perf2-stackit"
}

variable "pg_acl" {
  description = "PostgreSQL ACL — allowed CIDRs"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "pg_backup_schedule" {
  description = "PostgreSQL backup cron schedule"
  type        = string
  default     = "0 2 * * *"
}

# --- Object Storage ---

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "vob-dev"
}
