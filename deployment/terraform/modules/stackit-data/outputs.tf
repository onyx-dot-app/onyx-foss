# ===========================================================
# Outputs — Werden von Helm Values und CI/CD referenziert
# ===========================================================

# --- PostgreSQL ---

output "pg_host" {
  description = "PostgreSQL Flex connection host"
  value       = stackit_postgresflex_user.app.host
}

output "pg_port" {
  description = "PostgreSQL Flex connection port"
  value       = stackit_postgresflex_user.app.port
}

output "pg_username" {
  description = "PostgreSQL application username"
  value       = stackit_postgresflex_user.app.username
}

output "pg_password" {
  description = "PostgreSQL application password (auto-generated)"
  value       = stackit_postgresflex_user.app.password
  sensitive   = true
}

output "pg_uri" {
  description = "PostgreSQL connection URI"
  value       = stackit_postgresflex_user.app.uri
  sensitive   = true
}

output "pg_instance_id" {
  description = "PostgreSQL Flex instance ID"
  value       = stackit_postgresflex_instance.main.instance_id
}

# --- PostgreSQL Read-Only User ---

output "pg_readonly_username" {
  description = "PostgreSQL read-only username"
  value       = stackit_postgresflex_user.readonly.username
}

output "pg_readonly_password" {
  description = "PostgreSQL read-only password (auto-generated)"
  value       = stackit_postgresflex_user.readonly.password
  sensitive   = true
}

# --- Object Storage ---

output "bucket_name" {
  description = "S3 bucket name"
  value       = stackit_objectstorage_bucket.main.name
}

output "bucket_url" {
  description = "S3 bucket URL (path-style)"
  value       = stackit_objectstorage_bucket.main.url_path_style
}
