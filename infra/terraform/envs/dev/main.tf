terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # ADC quota project stays on the live workload; override to JobAtlas here
  # instead of touching global ADC.
  user_project_override = true
  billing_project       = var.project_id
}

provider "random" {}

module "gcp" {
  source = "../../modules/gcp"

  project_id      = var.project_id
  region          = var.region
  gcs_bucket_name = var.gcs_bucket_name
  enable_cloudsql = var.enable_cloudsql
}
