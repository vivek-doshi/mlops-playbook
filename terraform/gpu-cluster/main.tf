# gpu-cluster/main.tf
#
# IMPORTANT: This file is a documentation-as-code stub.
# GPU cluster provisioning is owned by the platform team and lives in:
#   devops-playbook/terraform/gpu-cluster/
#
# This stub declares the contract between the MLOps playbook (consumer) and
# the platform repo (provider). It documents:
#   - What variables the cluster module expects.
#   - What outputs the MLOps platform uses.
#   - Which devops-playbook modules to reference.
#
# BEGINNER NOTE:
#   The Integration Bridge principle means this repo intentionally does NOT
#   own the GPU cluster Terraform. Instead it declares its requirements here
#   so the platform team knows exactly what the ML workloads need.

terraform {
  # Minimum Terraform version required by this module.
  # Matches the constraint used in devops-playbook/terraform/gpu-cluster/.
  required_version = ">= 1.6.0"

  # Remote state configuration.
  # Uncomment and configure the backend block to store state in your cloud:
  #
  # backend "gcs" {
  #   bucket = "my-terraform-state-bucket"
  #   prefix = "mlops/gpu-cluster"
  # }
  #
  # backend "s3" {
  #   bucket = "my-terraform-state-bucket"
  #   key    = "mlops/gpu-cluster/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# ---------------------------------------------------------------------------
# VARIABLE DECLARATIONS
# ---------------------------------------------------------------------------
# These variables must be provided by the calling module or a .tfvars file.
# They describe the GPU cluster requirements for ML workloads.

variable "platform" {
  type        = string
  description = "Target platform: aws-eks, azure-aks, gcp-gke"

  validation {
    condition     = contains(["aws-eks", "azure-aks", "gcp-gke"], var.platform)
    error_message = "platform must be one of: aws-eks, azure-aks, gcp-gke."
  }
}

variable "cluster_name" {
  type        = string
  description = "GPU cluster name (must match devops-playbook cluster name for workload identity)"
}

variable "region" {
  type        = string
  description = "Cloud region where the GPU cluster resides"
  default     = "us-central1"
}

variable "node_count" {
  type        = number
  description = "Number of GPU nodes in the node pool"
  default     = 2

  # GPU nodes are expensive — require explicit justification for > 4 nodes.
  # Larger clusters must go through the GPU approval gate in:
  #   devops-playbook/policy/gpu-approval-gate/
  validation {
    condition     = var.node_count >= 1 && var.node_count <= 16
    error_message = "node_count must be between 1 and 16."
  }
}

variable "gpu_type" {
  type        = string
  description = "GPU type (e.g. nvidia-tesla-t4, nvidia-a100-80gb)"
  default     = "nvidia-tesla-t4"
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace where ML workloads run"
  default     = "serving"
}

# ---------------------------------------------------------------------------
# PLATFORM MODULE REFERENCE
# ---------------------------------------------------------------------------
# To provision an actual GPU cluster, reference the platform module.
# Example (uncomment and configure):
#
# module "gpu_cluster" {
#   source = "git::https://github.com/your-org/devops-playbook.git//terraform/gpu-cluster?ref=v1.2.0"
#
#   platform     = var.platform
#   cluster_name = var.cluster_name
#   region       = var.region
#   node_count   = var.node_count
#   gpu_type     = var.gpu_type
#   namespace    = var.namespace
#
#   # KEDA scale-to-zero configuration (see docs/guides/gpu-cost-governance.md).
#   enable_keda       = true
#   scale_to_zero     = true
#   idle_minutes      = 15
#
#   # Required cost labels for GPU FinOps (see docs/guides/gpu-cost-governance.md).
#   labels = {
#     cost-center  = "ml-platform"
#     team         = "data-science"
#     environment  = "production"
#   }
# }

# ---------------------------------------------------------------------------
# OUTPUTS
# ---------------------------------------------------------------------------
# Outputs are consumed by other Terraform modules and by CI pipelines.

output "integration_note" {
  description = "Reminder that GPU cluster provisioning is delegated to the platform repo"
  value       = "Reference platform modules from devops-playbook/terraform/gpu-cluster/ for ${var.platform}."
}

# Example outputs that would be produced by the platform module:
#
# output "kubeconfig_path" {
#   description = "Path to the generated kubeconfig file"
#   value       = module.gpu_cluster.kubeconfig_path
# }
#
# output "node_pool_name" {
#   description = "Kubernetes node pool name for GPU scheduling"
#   value       = module.gpu_cluster.node_pool_name
# }
