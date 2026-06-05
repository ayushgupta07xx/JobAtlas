variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "bq_dataset_id" {
  type    = string
  default = "jobatlas_marts"
}

variable "bq_location" {
  type    = string
  default = "asia-south1"
}

variable "gcs_bucket_name" {
  type = string
}

variable "gcs_location" {
  type    = string
  default = "us-central1"
}

variable "archive_retention_days" {
  type    = number
  default = 30
}

variable "enable_cloudsql" {
  type    = bool
  default = true
}

variable "cloudsql_tier" {
  type    = string
  default = "db-f1-micro"
}

variable "cloudsql_db_version" {
  type    = string
  default = "POSTGRES_16"
}
