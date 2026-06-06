variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "gcs_bucket_name" {
  type = string
}

variable "enable_cloudsql" {
  type    = bool
  default = true
}
