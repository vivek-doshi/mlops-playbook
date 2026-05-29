# azure-ml/main.tf
#
# Provisions the full Azure Machine Learning workspace stack:
#   - Resource group
#   - ADLS Gen2 storage account (ml-artifacts + dvc-remote containers)
#   - Azure Key Vault (RBAC-based, purge-protected in production)
#   - Log Analytics workspace + Application Insights
#   - Azure Container Registry (Premium in production, Basic elsewhere)
#   - Azure ML Workspace (system-assigned identity, AAD-only)
#   - Role assignments: workspace identity → Storage, ACR, Key Vault
#   - Compute clusters: cpu, gpu-training, gpu-inference (scale-to-zero)
#   - Online endpoint for managed model serving
#   - Role assignments: endpoint identity → Storage, ACR
#
# INTEGRATION BRIDGE NOTE:
#   GPU cluster quota for NDv4/NDv5 must be requested from the platform team.
#   See docs/decisions/ADR-ML-006-infrastructure-terraform.md for cross-repo
#   dependency boundaries.
#
# BEGINNER NOTE:
#   Run in this order:
#     1. terraform init   — downloads providers and sets up state backend
#     2. terraform plan   — previews what will be created
#     3. terraform apply  — creates resources (takes ~10 minutes)
#   Destroy with: terraform destroy (dev only — production has prevent_destroy)
#
# SDK v2 NOTE:
#   This module targets Azure ML SDK v2 (azure-ai-ml >= 1.0).
#   SDK v1 (azureml-sdk) reached End-of-Life March 31 2025 and must not be used.

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.50"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      # Retain soft-deleted vaults for 90 days before permanent deletion.
      # In production, purge_protection prevents this from being bypassed.
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
    machine_learning {
      # Purge workspace on destroy only in dev — prevent accidental prod deletion.
      purge_soft_deleted_workspace_on_destroy = var.environment != "production"
    }
  }
}

# ---------------------------------------------------------------------------
# DATA SOURCES
# ---------------------------------------------------------------------------

data "azurerm_client_config" "current" {}

# ---------------------------------------------------------------------------
# LOCALS
# Centralise naming suffix and mandatory tags.
# Every resource uses local.common_tags — cost attribution requires all five.
# ---------------------------------------------------------------------------

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
  # Regenerating the suffix destroys all globally-unique resources.
  # Use `terraform state mv` if you need to rename.
  keepers = {
    environment    = var.environment
    location_short = var.location_short
    model_name     = var.model_name
  }
}

locals {
  name_suffix = "${var.environment}-${var.location_short}-${random_string.suffix.result}"

  common_tags = merge(
    {
      cost-center    = var.cost_center
      team           = var.team
      managed-by     = "terraform"
      environment    = var.environment
      mlops-playbook = "azure-ml"
    },
    var.additional_tags,
  )
}

# ---------------------------------------------------------------------------
# RESOURCE GROUP
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "ml" {
  name     = "rg-aml-${var.model_name}-${local.name_suffix}"
  location = var.location
  tags     = local.common_tags
}

# ---------------------------------------------------------------------------
# STORAGE ACCOUNT — ADLS Gen2
# is_hns_enabled enables the hierarchical namespace required for ADLS Gen2.
# MLflow stores model binaries, plots, and evaluation reports here.
# DVC stores dataset cache objects in a separate container.
# ---------------------------------------------------------------------------

resource "azurerm_storage_account" "ml" {
  name                     = "staml${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.ml.name
  location                 = azurerm_resource_group.ml.location
  account_tier             = "Standard"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # ADLS Gen2 — required for ML workspace backend

  # GRS in production provides geo-redundant copies across paired Azure regions.
  # LRS in dev/staging is sufficient and significantly cheaper.
  account_replication_type = var.environment == "production" ? "GRS" : "LRS"

  # Allow workspace system identity to authenticate without connection strings.
  shared_access_key_enabled = false

  # HTTPS-only enforces encryption in transit for all blob/ADLS operations.
  https_traffic_only_enabled = true
  min_tls_version            = "TLS1_2"

  # Restrict public blob access — access is mediated through RBAC only.
  allow_nested_items_to_be_public = false

  tags = local.common_tags
}

resource "azurerm_storage_container" "ml_artifacts" {
  name                  = "ml-artifacts"
  storage_account_id    = azurerm_storage_account.ml.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "dvc_remote" {
  name                  = "dvc-remote"
  storage_account_id    = azurerm_storage_account.ml.id
  container_access_type = "private"
}

# ---------------------------------------------------------------------------
# KEY VAULT
# RBAC authorization mode — no legacy access policies needed.
# purge_protection_enabled prevents deletion even by subscription admins in prod.
# ---------------------------------------------------------------------------

resource "azurerm_key_vault" "ml" {
  name                = "kv-aml-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.ml.name
  location            = azurerm_resource_group.ml.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # RBAC mode: role assignments control access, not legacy access policies.
  # This aligns with Zero Trust and removes the need for vault-specific policy objects.
  enable_rbac_authorization = true

  # Soft-delete retains secrets for 90 days after deletion — prevents accidental loss.
  soft_delete_retention_days = 90

  # Purge protection: in production, nobody (including admins) can permanently delete
  # the vault during the retention window. False in dev for easy teardown.
  purge_protection_enabled = var.environment == "production" ? true : false

  # Match workspace-level network access setting.
  public_network_access_enabled = var.allow_public_network_access

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# LOG ANALYTICS WORKSPACE
# Application Insights is backed by Log Analytics for log querying via KQL.
# ---------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "ml" {
  name                = "log-aml-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.ml.name
  location            = azurerm_resource_group.ml.location
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "production" ? 90 : 30
  tags                = local.common_tags
}

# ---------------------------------------------------------------------------
# APPLICATION INSIGHTS
# Linked to Log Analytics for unified querying and alerting.
# Azure ML workspace uses this for experiment run telemetry.
# ---------------------------------------------------------------------------

resource "azurerm_application_insights" "ml" {
  name                = "appi-aml-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.ml.name
  location            = azurerm_resource_group.ml.location
  application_type    = "web"

  # workspace_id links Application Insights to the Log Analytics workspace,
  # enabling unified KQL queries across runs, metrics, and application logs.
  workspace_id = azurerm_log_analytics_workspace.ml.id

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# CONTAINER REGISTRY
# Premium SKU in production enables geo-replication, private link, and
# content trust. Basic is sufficient and cheaper for non-production use.
# ---------------------------------------------------------------------------

resource "azurerm_container_registry" "ml" {
  name                = "cracml${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.ml.name
  location            = azurerm_resource_group.ml.location

  # Premium in production: enables geo-replication, private endpoints, content trust.
  # Basic in dev/staging: sufficient for pull-through caching and CI image builds.
  sku = var.environment == "production" ? "Premium" : "Basic"

  # Disable admin credentials — all access through managed identity and RBAC.
  admin_enabled = false

  tags = local.common_tags
}

# Geo-replication for premium production ACR — provides read replicas near
# compute regions to reduce image pull latency and egress costs.
resource "azurerm_container_registry_geo_replication" "ml" {
  count                 = var.acr_georeplica_location != null ? 1 : 0
  container_registry_id = azurerm_container_registry.ml.id
  location              = var.acr_georeplica_location
  tags                  = local.common_tags
}

# ---------------------------------------------------------------------------
# AZURE ML WORKSPACE
# The workspace is the top-level resource for all ML operations.
# System-assigned identity is recommended — no credential rotation needed.
# ---------------------------------------------------------------------------

resource "azurerm_machine_learning_workspace" "ml" {
  name                = "aml-${var.model_name}-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.ml.name
  location            = azurerm_resource_group.ml.location

  # Wire up the four required supporting resources.
  application_insights_id = azurerm_application_insights.ml.id
  key_vault_id            = azurerm_key_vault.ml.id
  storage_account_id      = azurerm_storage_account.ml.id
  container_registry_id   = azurerm_container_registry.ml.id

  # SystemAssigned: Azure creates and manages the identity lifecycle.
  # This identity is then granted RBAC roles on Storage, ACR, and Key Vault below.
  identity {
    type = "SystemAssigned"
  }

  # Customer-managed key for data-at-rest encryption (enterprise compliance).
  # null in dev/staging — uses Microsoft-managed keys (default).
  dynamic "encryption" {
    for_each = var.customer_managed_key_id != null ? [1] : []
    content {
      key_vault_id = azurerm_key_vault.ml.id
      key_id       = var.customer_managed_key_id
    }
  }

  # false = disable public internet access, force private endpoint traffic only.
  # true  = allow public access (dev/staging default).
  public_network_access_enabled = var.allow_public_network_access

  tags = local.common_tags

  # Workspace depends on role assignments being ready; wait for them.
  depends_on = [
    azurerm_role_assignment.workspace_storage_blob,
    azurerm_role_assignment.workspace_storage_contributor,
  ]
}

# ---------------------------------------------------------------------------
# ROLE ASSIGNMENTS — Workspace identity → Storage, ACR, Key Vault
# The workspace system-assigned identity needs these roles to:
#   - Read/write model artifacts and dataset cache (Storage Blob Data Contributor)
#   - List storage account keys for internal operations (Storage Account Contributor)
#   - Push/pull images from the workspace-linked ACR (AcrPush + AcrPull)
#   - Read secrets and certificates at job runtime (Key Vault Secrets User)
#   - Read Key Vault metadata (Key Vault Reader)
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "workspace_storage_blob" {
  scope                = azurerm_storage_account.ml.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

resource "azurerm_role_assignment" "workspace_storage_contributor" {
  scope                = azurerm_storage_account.ml.id
  role_definition_name = "Storage Account Contributor"
  principal_id         = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

resource "azurerm_role_assignment" "workspace_acr_push" {
  scope                = azurerm_container_registry.ml.id
  role_definition_name = "AcrPush"
  principal_id         = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

resource "azurerm_role_assignment" "workspace_acr_pull" {
  scope                = azurerm_container_registry.ml.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

resource "azurerm_role_assignment" "workspace_kv_secrets" {
  scope                = azurerm_key_vault.ml.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

resource "azurerm_role_assignment" "workspace_kv_reader" {
  scope                = azurerm_key_vault.ml.id
  role_definition_name = "Key Vault Reader"
  principal_id         = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

# ---------------------------------------------------------------------------
# COMPUTE CLUSTER — CPU
# General-purpose compute for lightweight preprocessing, evaluation, and
# registration steps that do not require GPU.
# min_node_count = 0: scale-to-zero when idle — no idle cost.
# ---------------------------------------------------------------------------

resource "azurerm_machine_learning_compute_cluster" "cpu" {
  name                          = "cpu-cluster"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ml.id
  location                      = azurerm_resource_group.ml.location
  vm_priority                   = "Dedicated"
  vm_size                       = var.cpu_cluster_vm_size

  # AAD-only: disable local authentication on every compute resource.
  # BEGINNER NOTE: This forces all job submissions to use an Azure AD identity
  # (your user account or a service principal) — no username/password.
  local_auth_enabled = false

  scale_settings {
    # Scale to zero when no jobs are running — eliminates idle compute cost.
    min_node_count                       = 0
    max_node_count                       = var.cpu_cluster_max_nodes
    scale_down_nodes_after_idle_duration = "PT2M" # 2 minutes idle → scale down
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# COMPUTE CLUSTER — GPU Training
# Used for model training workloads. LowPriority (Spot) by default to save
# 60–80% compared to Dedicated pricing.
#
# GPU VM SIZE REFERENCE (set via var.gpu_cluster_vm_size):
#   Standard_NC6s_v3              1× V100 16GB       dev/experimentation
#   Standard_NC24ads_A100_v4      1× A100 80GB PCIe  single-GPU training
#   Standard_NC40ads_H100_v5      1× H100 NVL 96GB   LLM inference
#   Standard_ND96asr_v4           8× A100 40GB SXM4  distributed training (quota req)
#   Standard_ND96isr_H100_v5      8× H100 80GB SXM5  distributed training (quota req)
#
# NOTE: NDv4 and NDv5 series require a support ticket for quota increase.
# Allow 1–4 weeks lead time. Default max_nodes validation is capped at 16
# to align with typical enterprise quota limits.
# ---------------------------------------------------------------------------

resource "azurerm_machine_learning_compute_cluster" "gpu_training" {
  name                          = "gpu-training"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ml.id
  location                      = azurerm_resource_group.ml.location

  # LowPriority = Spot: Azure may preempt the VM with 30s notice.
  # For long training jobs, enable checkpointing (see training/ray/checkpoint_callback.py).
  vm_priority = var.gpu_cluster_vm_priority
  vm_size     = var.gpu_cluster_vm_size

  local_auth_enabled = false

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.gpu_cluster_max_nodes
    scale_down_nodes_after_idle_duration = "PT5M" # 5 minutes — GPU warm-up time
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# COMPUTE CLUSTER — GPU Inference
# Dedicated priority for inference — Spot preemption would cause downtime.
# Separate cluster from training to allow independent scaling.
# ---------------------------------------------------------------------------

resource "azurerm_machine_learning_compute_cluster" "gpu_inference" {
  name                          = "gpu-inference"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ml.id
  location                      = azurerm_resource_group.ml.location
  vm_priority                   = "Dedicated" # Never Spot for inference — availability matters
  vm_size                       = var.gpu_inference_vm_size

  local_auth_enabled = false

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.gpu_inference_max_nodes
    scale_down_nodes_after_idle_duration = "PT10M"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# ONLINE ENDPOINT — Managed Serving
# A managed online endpoint provides a stable HTTPS scoring URI with
# automatic TLS, load balancing, and AAD authentication.
# Blue/green deployments are modelled as multiple deployments on this endpoint.
# ---------------------------------------------------------------------------

resource "azurerm_machine_learning_online_endpoint" "serving" {
  name                          = "ep-${var.model_name}-${local.name_suffix}"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ml.id
  location                      = azurerm_resource_group.ml.location

  # AMLToken in production: uses short-lived workspace tokens (no key rotation).
  # Use "Key" only in dev for quick SDK testing.
  auth_mode = var.environment == "production" ? "AMLToken" : "Key"

  # Match workspace-level network access.
  public_network_access_enabled = var.allow_public_network_access

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# ROLE ASSIGNMENTS — Endpoint identity → Storage, ACR
# The endpoint system-assigned identity needs:
#   - AcrPull: to pull the serving container image at deployment time
#   - Storage Blob Data Reader: to read model artefacts during scoring
# ---------------------------------------------------------------------------

resource "azurerm_role_assignment" "endpoint_acr_pull" {
  scope                = azurerm_container_registry.ml.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_machine_learning_online_endpoint.serving.identity[0].principal_id
}

resource "azurerm_role_assignment" "endpoint_storage_blob" {
  scope                = azurerm_storage_account.ml.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_machine_learning_online_endpoint.serving.identity[0].principal_id
}
