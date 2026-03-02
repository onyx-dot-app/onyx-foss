terraform {
  required_version = ">= 1.5"

  required_providers {
    stackit = {
      source  = "stackitcloud/stackit"
      version = "~> 0.80"
    }
  }
}
