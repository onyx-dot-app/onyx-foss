# ===========================================================
# Terraform State Backend — StackIT Object Storage (S3)
# ===========================================================
# Wird erst konfiguriert, wenn der State-Bucket existiert.
# Bis dahin: local State (terraform.tfstate)
#
# terraform init -backend-config="access_key=..." \
#                -backend-config="secret_key=..."
# ===========================================================

# PHASE 1: Local Backend (jetzt)
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

# PHASE 2: Remote Backend (nach Bucket-Erstellung)
# terraform {
#   backend "s3" {
#     bucket                      = "voeb-terraform-state"
#     key                         = "dev/terraform.tfstate"
#     region                      = "eu01"
#     endpoints = {
#       s3 = "https://object.storage.eu01.onstackit.cloud"
#     }
#     skip_credentials_validation = true
#     skip_region_validation      = true
#     skip_s3_checksum            = true
#     skip_requesting_account_id  = true
#     skip_metadata_api_check     = true
#   }
# }
