# Azure ML Terraform Module

Provisions the full Azure Machine Learning workspace stack for MLOps workloads.

## What This Module Provisions

| Resource | Purpose |
|---|---|
| `azurerm_resource_group` | Container for all module resources |
| `azurerm_storage_account` | ADLS Gen2 — MLflow artefacts + DVC dataset cache |
| `azurerm_storage_container` × 2 | `ml-artifacts` (MLflow) and `dvc-remote` (DVC) |
| `azurerm_key_vault` | Secrets at job runtime; CMK encryption anchor |
| `azurerm_log_analytics_workspace` | Log sink for Application Insights and diagnostics |
| `azurerm_application_insights` | Experiment telemetry and training run traces |
| `azurerm_container_registry` | Serving and training container images (Premium in prod) |
| `azurerm_machine_learning_workspace` | Top-level ML resource; links all dependencies above |
| `azurerm_role_assignment` × 6 | Workspace identity → Storage, ACR, Key Vault |
| `azurerm_machine_learning_compute_cluster` × 3 | cpu, gpu-training, gpu-inference (all scale-to-zero) |
| `azurerm_machine_learning_online_endpoint` | Stable HTTPS scoring URI for managed deployments |
| `azurerm_role_assignment` × 2 | Endpoint identity → ACR, Storage |

## Prerequisites

1. **Azure subscription** with Contributor (or custom ML role) on the target subscription.
2. **Terraform >= 1.6.0** installed locally or in CI.
3. **Azure CLI** authenticated: `az login` or federated OIDC identity in CI.
4. **GPU quota**: NDv4 (`Standard_ND96asr_v4`) and NDv5 (`Standard_ND96isr_H100_v5`) series
   require a **support ticket** quota increase. Request 1–4 weeks before planned training runs.
   Use `az vm list-skus --location eastus --size Standard_ND --output table` to check availability.
5. Remote state backend configured in the platform repository (`devops-playbook`).

## Apply Commands

```bash
# Initialise (first time, or after provider version bump)
terraform -chdir=terraform/azure-ml init \
  -backend-config="resource_group_name=rg-tfstate" \
  -backend-config="storage_account_name=sttfstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=azure-ml/${environment}.tfstate"

# Preview changes
terraform -chdir=terraform/azure-ml plan \
  -var-file="environments/${environment}.tfvars" \
  -out=tfplan

# Apply
terraform -chdir=terraform/azure-ml apply tfplan

# Destroy (dev only — production has prevent_destroy)
terraform -chdir=terraform/azure-ml destroy \
  -var-file="environments/dev.tfvars"
```

Replace `${environment}` with `dev`, `staging`, or `production`.

## Environment Files

| File | Purpose |
|---|---|
| `environments/dev.tfvars` | LowPriority GPU, public access, minimal nodes |
| `environments/staging.tfvars` | Dedicated GPU, private endpoint, medium scale |
| `environments/production.tfvars` | H100 NDv5, ACR geo-replication, full scale |

## Integration Bridge

This module provisions **compute and workspace** only.  
Infrastructure primitives (VNet, subnet, NSG, private DNS zones) are owned by
the platform repository (`devops-playbook`). Pass the VNet/subnet names from
platform outputs into `vnet_name`, `subnet_name`, and `vnet_resource_group_name`
when `allow_public_network_access = false`.

## SDK v2 Note

This module targets **Azure ML SDK v2** (`azure-ai-ml >= 1.0`).  
SDK v1 (`azureml-sdk`) reached End-of-Life **March 31 2025** — do not use it in
new code. All CI job definitions (`ci/azure-ml/train-job.yaml`) use the v2 YAML schema.

## GPU Quota Note

NDv4 (`Standard_ND96asr_v4`) and NDv5 (`Standard_ND96isr_H100_v5`) are
**restricted SKUs** in most Azure regions. To request quota:

1. Go to Azure Portal → Subscriptions → Your subscription → Usage + Quotas.
2. Filter by `ND`, select the region, and click **Request Increase**.
3. Allow **1–4 weeks** for approval in most regions.
4. The `gpu_cluster_max_nodes` validation is capped at 16 to align with
   typical enterprise quota limits after approval.

## Post-Apply — Set GitHub Secrets

After `terraform apply`, capture these outputs and add them as GitHub Actions secrets:

```bash
terraform -chdir=terraform/azure-ml output -raw mlflow_tracking_uri
terraform -chdir=terraform/azure-ml output -raw workspace_name
terraform -chdir=terraform/azure-ml output -raw workspace_resource_group
terraform -chdir=terraform/azure-ml output -raw storage_account_name
```
