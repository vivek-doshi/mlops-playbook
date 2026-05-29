variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Vertex AI resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment: dev | staging | production"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "cost_center" {
  description = "Cost center label for billing attribution"
  type        = string
  default     = "ml-platform"
}

variable "team" {
  description = "Team label for billing attribution"
  type        = string
  default     = "mlops"
}
