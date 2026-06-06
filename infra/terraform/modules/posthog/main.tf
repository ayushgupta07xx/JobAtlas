# Plan-only stub: PostHog analytics config.
# PostHog has no first-class Terraform provider, so project / feature-flag
# config is managed via the PostHog API today. This module documents the
# intended IaC surface and is intentionally not wired into any env. The
# terraform_data placeholder keeps it valid Terraform without a provider.

variable "project_name" {
  type    = string
  default = "JobAtlas"
}

variable "host" {
  type    = string
  default = "https://us.posthog.com"
}

resource "terraform_data" "posthog_config" {
  input = {
    project_name = var.project_name
    host         = var.host
  }
}
