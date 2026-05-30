terraform {
  required_version = ">= 1.7.0"
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = var.github_org
}

variable "github_org" {
  description = "GitHub organisation or user that owns the repository."
  type        = string
}

variable "github_repo" {
  description = "Repository name for the MLOps playbook."
  type        = string
  default     = "mlops-playbook"
}

# Register the GitHub App for the portal.
# The portal uses the installation token — never a PAT.
resource "github_app" "mlops_portal" {
  name        = "mlops-portal"
  description = "GitHub App for MLOps self-service portal workflow dispatches."
  url         = "https://github.com/${var.github_org}/${var.github_repo}"
}

output "app_id" {
  description = "GitHub App ID — store as GITHUB_APP_ID secret."
  value       = github_app.mlops_portal.app_id
  sensitive   = true
}
