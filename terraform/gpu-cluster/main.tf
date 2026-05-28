terraform {
  required_version = ">= 1.6.0"
}

variable "platform" {
  type        = string
  description = "Target platform: aws-eks, azure-aks, gcp-gke"
}

variable "cluster_name" {
  type        = string
  description = "GPU cluster name"
}

variable "node_count" {
  type        = number
  description = "GPU node count"
  default     = 2
}

output "integration_note" {
  value = "Reference platform modules from the platform repository for ${var.platform}."
}
