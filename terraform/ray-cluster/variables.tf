# terraform/ray-cluster/variables.tf
# Input variables for the Ray cluster Terraform module.
# Override defaults in terraform.tfvars or via -var CLI flags.

variable "kubeconfig_path" {
  description = "Path to kubeconfig file for the target cluster."
  type        = string
  default     = "~/.kube/config"
}

variable "kubeconfig_context" {
  description = "Kubeconfig context to use."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Deployment environment (dev|staging|production)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be one of: dev, staging, production."
  }
}

variable "tags" {
  description = "Additional resource tags applied to all cloud resources."
  type        = map(string)
  default     = {}
}
