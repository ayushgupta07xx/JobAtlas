# Plan-only stub: front-end project config for Vercel.
# Not wired into any env; apply is intentionally deferred because free-tier
# deploys are driven by the Vercel GitHub integration today. This documents
# the intended IaC surface for the Next.js frontend.
terraform {
  required_providers {
    vercel = {
      source = "vercel/vercel"
    }
  }
}

variable "project_name" {
  type    = string
  default = "job-atlas"
}

variable "git_repo" {
  type    = string
  default = "ayushgupta07xx/JobAtlas"
}

resource "vercel_project" "frontend" {
  name      = var.project_name
  framework = "nextjs"

  git_repository = {
    type = "github"
    repo = var.git_repo
  }
}
