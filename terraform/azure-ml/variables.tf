# azure-ml/variables.tf
#
# All input variables for the Azure ML workspace module.
# Every variable has a description. Variables with restricted value sets
# have a validation block to fail fast with a clear error message.

# ---------------------------------------------------------------------------
# ENVIRONMENT & LOCATION
# ---------------------------------------------------------------------------

variable "environment" {
  type        = string
  description = "Deployment environment. Controls SKUs, replication, and purge protection."
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be one of: dev, staging, production."
  }
}

variable "location" {
  type        = string
  description = "Primary Azure region for all resources. Run `az account list-locations -o table` for valid values."
  default     = "eastus"
}

variable "location_short" {
  type        = string
  description = "Short location code used in resource names (e.g. 'eus' for eastus, 'weu' for westeurope). Must be 2–5 lowercase characters."
  default     = "eus"
  validation {
    condition     = can(regex("^[a-z]{2,5}$", var.location_short))
    error_message = "location_short must be 2–5 lowercase letters, e.g. 'eus', 'weu', 'sea'."
  }
}

# ---------------------------------------------------------------------------
# WORKLOAD IDENTITY & COST ATTRIBUTION
# ---------------------------------------------------------------------------

variable "model_name" {
  type        = string
  description = "Logical model name. Used in resource names and cost tags. Must be lowercase-kebab-case (e.g. 'fraud-detection', 'churn-predictor')."
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]+[a-z0-9]$", var.model_name))
    error_message = "model_name must be lowercase-kebab-case with no leading/trailing hyphens (e.g. 'fraud-detection')."
  }
}

variable "cost_center" {
  type        = string
  description = "Billing cost center code. Required for cost attribution — no default. Example: 'ml-platform', 'data-science-eu'."
}

variable "team" {
  type        = string
  description = "Owning team name. Applied as a tag to every resource for ownership tracking. Example: 'ml-platform-team'."
}

variable "additional_tags" {
  type        = map(string)
  description = "Additional resource tags to merge with the common tag set. Use for project-specific or compliance labels."
  default     = {}
}

# ---------------------------------------------------------------------------
# NETWORK ACCESS
# ---------------------------------------------------------------------------

variable "allow_public_network_access" {
  type        = bool
  description = "Allow public internet access to the workspace, storage, and endpoint. Set false in staging/production to force private endpoint traffic only."
  default     = true
}

variable "vnet_resource_group_name" {
  type        = string
  description = "Resource group of the VNet used for private endpoints. Required when allow_public_network_access = false. Platform team provides this value."
  default     = null
}

variable "vnet_name" {
  type        = string
  description = "Name of the VNet used for private endpoints. Required when allow_public_network_access = false."
  default     = null
}

variable "subnet_name" {
  type        = string
  description = "Name of the subnet within vnet_name for private endpoint NICs. Must have private endpoint network policies disabled."
  default     = null
}

# ---------------------------------------------------------------------------
# CPU COMPUTE CLUSTER
# ---------------------------------------------------------------------------

variable "cpu_cluster_vm_size" {
  type        = string
  description = "VM size for the CPU compute cluster. Used for preprocessing, evaluation, and registration steps. Example: 'Standard_DS3_v2', 'Standard_D4s_v5'."
  default     = "Standard_DS3_v2"
}

variable "cpu_cluster_max_nodes" {
  type        = number
  description = "Maximum node count for the CPU compute cluster. Scale-to-zero is always enabled (min = 0). Valid range: 1–100."
  default     = 4
  validation {
    condition     = var.cpu_cluster_max_nodes >= 1 && var.cpu_cluster_max_nodes <= 100
    error_message = "cpu_cluster_max_nodes must be between 1 and 100."
  }
}

# ---------------------------------------------------------------------------
# GPU TRAINING CLUSTER
#
# VM size reference (pass via var.gpu_cluster_vm_size):
#   Standard_NC6s_v3              1× V100 16GB       dev/experimentation
#   Standard_NC24ads_A100_v4      1× A100 80GB PCIe  single-GPU training/inference
#   Standard_NC40ads_H100_v5      1× H100 NVL 96GB   LLM inference
#   Standard_ND96asr_v4           8× A100 40GB SXM4  distributed training (quota req)
#   Standard_ND96isr_H100_v5      8× H100 80GB SXM5  distributed training (quota req)
#
# NDv4 and NDv5 require a support ticket quota increase (1–4 week wait).
# ---------------------------------------------------------------------------

variable "gpu_cluster_vm_size" {
  type        = string
  description = "VM size for the GPU training cluster. See variable comment for full size reference. A100/H100 NDv4/NDv5 require quota increase via support ticket."
  default     = "Standard_NC24ads_A100_v4"
}

variable "gpu_cluster_vm_priority" {
  type        = string
  description = "VM priority for the GPU training cluster. LowPriority (Spot) saves 60–80% over Dedicated; Azure may preempt with 30s notice. Use Dedicated in production."
  default     = "LowPriority"
  validation {
    condition     = contains(["LowPriority", "Dedicated"], var.gpu_cluster_vm_priority)
    error_message = "gpu_cluster_vm_priority must be 'LowPriority' or 'Dedicated'."
  }
}

variable "gpu_cluster_max_nodes" {
  type        = number
  description = "Maximum node count for the GPU training cluster. Valid range: 1–16. Values >4 typically require a quota increase. Contact platform team for NDv5 (H100) quotas."
  default     = 1
  validation {
    condition     = var.gpu_cluster_max_nodes >= 1 && var.gpu_cluster_max_nodes <= 16
    error_message = "gpu_cluster_max_nodes must be between 1 and 16. Values >4 may require a support-ticket quota increase."
  }
}

# ---------------------------------------------------------------------------
# GPU INFERENCE CLUSTER
# ---------------------------------------------------------------------------

variable "gpu_inference_vm_size" {
  type        = string
  description = "VM size for the GPU inference cluster. Uses Dedicated priority — never Spot for inference availability."
  default     = "Standard_NC24ads_A100_v4"
}

variable "gpu_inference_max_nodes" {
  type        = number
  description = "Maximum node count for the GPU inference cluster. Scale-to-zero is enabled; set higher for production steady-state latency."
  default     = 2
  validation {
    condition     = var.gpu_inference_max_nodes >= 1 && var.gpu_inference_max_nodes <= 16
    error_message = "gpu_inference_max_nodes must be between 1 and 16."
  }
}

# ---------------------------------------------------------------------------
# CONTAINER REGISTRY
# ---------------------------------------------------------------------------

variable "acr_georeplica_location" {
  type        = string
  description = "Azure region for ACR geo-replication. Requires Premium SKU (automatically selected in production). null disables geo-replication. Example: 'westeurope'."
  default     = null
}

# ---------------------------------------------------------------------------
# ENCRYPTION
# ---------------------------------------------------------------------------

variable "customer_managed_key_id" {
  type        = string
  description = "Azure Key Vault key ID for customer-managed encryption of workspace data at rest. null uses Microsoft-managed keys. Required for FedRAMP/HIPAA compliance. Mark as sensitive — do not log."
  default     = null
  sensitive   = true
}
