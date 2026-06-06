locals {
  required_apis = [
    "serviceusage.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "sqladmin.googleapis.com",
  ]
}

resource "google_project_service" "enabled" {
  for_each           = toset(local.required_apis)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# BigQuery dbt-marts dataset (free tier: 10 GB storage + 1 TB queries/mo)
resource "google_bigquery_dataset" "marts" {
  project                    = var.project_id
  dataset_id                 = var.bq_dataset_id
  location                   = var.bq_location
  delete_contents_on_destroy = true
  description                = "JobAtlas dbt marts (demo materialization)"
  depends_on                 = [google_project_service.enabled]
}

# GCS Parquet archive
resource "google_storage_bucket" "archive" {
  project                     = var.project_id
  name                        = var.gcs_bucket_name
  location                    = var.gcs_location
  force_destroy               = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = var.archive_retention_days
    }
    action {
      type = "Delete"
    }
  }
  depends_on = [google_project_service.enabled]
}

# Cloud SQL Postgres (only cost line; destroy same session)
resource "random_password" "sql" {
  count   = var.enable_cloudsql ? 1 : 0
  length  = 24
  special = false
}

resource "google_sql_database_instance" "postgres" {
  count               = var.enable_cloudsql ? 1 : 0
  project             = var.project_id
  name                = "jobatlas-pg"
  region              = var.region
  database_version    = var.cloudsql_db_version
  deletion_protection = false

  settings {
    edition           = "ENTERPRISE"
    tier              = var.cloudsql_tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_autoresize   = false

    backup_configuration {
      enabled = false
    }
    ip_configuration {
      ipv4_enabled = true
    }
  }
  depends_on = [google_project_service.enabled]
}

resource "google_sql_database" "jobatlas" {
  count    = var.enable_cloudsql ? 1 : 0
  project  = var.project_id
  name     = "jobatlas"
  instance = google_sql_database_instance.postgres[0].name
}

resource "google_sql_user" "app" {
  count    = var.enable_cloudsql ? 1 : 0
  project  = var.project_id
  instance = google_sql_database_instance.postgres[0].name
  name     = "jobatlas_app"
  password = random_password.sql[0].result
}

output "bq_dataset_id" {
  value = google_bigquery_dataset.marts.dataset_id
}

output "gcs_bucket_url" {
  value = google_storage_bucket.archive.url
}

output "cloudsql_connection_name" {
  value       = var.enable_cloudsql ? google_sql_database_instance.postgres[0].connection_name : null
  description = "null when enable_cloudsql=false"
}
