# ===========================================================
# Terraform State Backend — TEST Environment
# ===========================================================
# Local State (wie DEV). Remote Backend vorbereitet.
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
#     key                         = "test/terraform.tfstate"
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
