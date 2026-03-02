# ===========================================================
# VÖB Service Chatbot — Variables für Data Services Modul
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
  description = "Target environment (dev, test, prod)"
  type        = string
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
}
