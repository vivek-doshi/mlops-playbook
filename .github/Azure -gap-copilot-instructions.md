# GitHub Copilot Instructions — Azure ML Gap Fill

## Model Configuration

```json
{
  "github.copilot.chat.models": {
    "default": "claude-sonnet-4-6"
  }
}
```

---

## Context: What Is Missing

The repo has Terraform for AWS SageMaker (`terraform/aws-sagemaker/`) and
GCP Vertex AI (`terraform/gcp-vertex-ai/`). Azure ML has **zero coverage**.

Azure is enterprise-dominant — financial services, healthcare, manufacturing,
and government workloads run predominantly on Azure. Azure ML with NDv5 H100
and NC H100 v5 is a primary GPU platform for enterprise LLM and MLOps workloads.
This gap means the repo is incomplete for any Azure-first organisation.

**Existing repo patterns to mirror exactly:**

| AWS file | GCP file | Azure equivalent to create |
|---|---|---|
| `terraform/aws-sagemaker/main.tf` | `terraform/gcp-vertex-ai/main.tf` | `terraform/azure-ml/main.tf` |
| `terraform/aws-sagemaker/variables.tf` | `terraform/gcp-vertex-ai/variables.tf` | `terraform/azure-ml/variables.tf` |
| — | `terraform/gcp-vertex-ai/main.tf` outputs block | `terraform/azure-ml/outputs.tf` |
| `dvc/remote-storage/s3.remote.sample` | `dvc/remote-storage/gcs.remote.sample` | `dvc/remote-storage/azure.remote.sample` ← **exists but incomplete** |
| `ci/github-actions/model-training/train.yml` | same | `ci/github-actions/model-training/train.yml` Azure credential block |
| `docs/golden-paths/model-serving.md` | same | Azure ML managed endpoint section |
| `docs/decisions/ADR-ML-006-infrastructure-terraform.md` | same | ADR update to include Azure ML |

---

## Deliverables — Generate These In Order

### 1. `terraform/azure-ml/main.tf`

Full workspace stack. Every resource below is required — do not skip any:

```
azurerm_resource_group
azurerm_storage_account          # ADLS Gen2, is_hns_enabled = true
azurerm_storage_container        # "ml-artifacts" + "dvc-remote"
azurerm_key_vault                # RBAC auth, purge_protection in prod
azurerm_log_analytics_workspace
azurerm_application_insights     # workspace_id → log analytics
azurerm_container_registry       # Premium in prod, Basic in dev
azurerm_machine_learning_workspace
  ├── identity { type = "SystemAssigned" }
  ├── application_insights_id
  ├── key_vault_id
  ├── storage_account_id
  └── container_registry_id
azurerm_role_assignment × 6      # workspace identity → storage/ACR/KV roles
azurerm_machine_learning_compute_cluster "cpu"
azurerm_machine_learning_compute_cluster "gpu_training"
azurerm_machine_learning_compute_cluster "gpu_inference"
azurerm_machine_learning_online_endpoint "serving"
azurerm_role_assignment × 2      # endpoint identity → storage/ACR
```

**Hard rules for main.tf:**
- `required_version = ">= 1.6.0"`, `azurerm ~> 4.0`, `azuread ~> 2.50`
- `local_auth_enabled = false` on every compute cluster — AAD only
- `public_network_access_enabled = var.allow_public_network_access`
- `vm_priority = "LowPriority"` default on GPU training (Spot saves 60–80%)
- `min_node_count = 0` on all clusters — scale-to-zero, never idle cost
- `purge_protection_enabled = var.environment == "production" ? true : false`
- `account_replication_type = var.environment == "production" ? "GRS" : "LRS"`
- Comment block at top: what the module provisions, integration bridge note,
  beginner note on apply order, SDK v2 note (SDK v1 EOL March 2025)
- `random_string` suffix for globally unique storage/ACR names
- `locals` block: `name_suffix`, `common_tags` (must include `cost-center`,
  `team`, `managed-by`, `environment`, `mlops-playbook`)

**GPU VM size reference — put in variable description, not hardcoded:**
```
Standard_NC6s_v3              1× V100 16GB      dev/experimentation
Standard_NC24ads_A100_v4      1× A100 80GB PCIe single-GPU training/inference
Standard_NC40ads_H100_v5      1× H100 NVL 96GB  LLM inference
Standard_ND96asr_v4           8× A100 40GB SXM4 distributed training (quota req)
Standard_ND96isr_H100_v5      8× H100 80GB SXM5 distributed training (quota req)
```

---

### 2. `terraform/azure-ml/variables.tf`

Required variables — include `description` and `validation` on every one:

```hcl
variable "environment"                  # validation: dev|staging|production
variable "location"                     # default "eastus"
variable "location_short"               # default "eus" — used in resource names
variable "model_name"                   # validation: lowercase-kebab-case regex
variable "cost_center"                  # no default — must be explicit
variable "team"                         # no default — must be explicit
variable "additional_tags"              # map(string), default {}
variable "allow_public_network_access"  # bool, default true
variable "vnet_resource_group_name"     # default null — private endpoint path
variable "vnet_name"                    # default null
variable "subnet_name"                  # default null
variable "cpu_cluster_vm_size"          # default "Standard_DS3_v2"
variable "cpu_cluster_max_nodes"        # validation: 1–100
variable "gpu_cluster_vm_size"          # default "Standard_NC24ads_A100_v4"
variable "gpu_cluster_vm_priority"      # validation: LowPriority|Dedicated
variable "gpu_cluster_max_nodes"        # validation: 1–16, note >4 needs approval
variable "gpu_inference_vm_size"        # default "Standard_NC24ads_A100_v4"
variable "gpu_inference_max_nodes"      # default 2
variable "acr_georeplica_location"      # default null — prod only
variable "customer_managed_key_id"      # default null, sensitive = true
```

---

### 3. `terraform/azure-ml/outputs.tf`

Every output needs a `description` explaining where it is consumed:

```hcl
output "workspace_id"
output "workspace_name"
output "workspace_resource_group"
output "mlflow_tracking_uri"            # azureml:// URI format, set as GH secret
output "workspace_discovery_url"
output "storage_account_name"
output "storage_account_id"
output "artifacts_container_name"
output "dvc_remote_container_name"
output "dvc_remote_url"                 # azure://<container> format
output "cpu_cluster_name"
output "gpu_training_cluster_name"
output "gpu_inference_cluster_name"
output "gpu_training_vm_size"
output "endpoint_name"
output "endpoint_scoring_uri"
output "endpoint_swagger_uri"
output "endpoint_principal_id"
output "acr_login_server"
output "acr_id"
output "key_vault_id"
output "key_vault_uri"
output "application_insights_connection_string"  # sensitive = true
output "log_analytics_workspace_id"
output "workspace_principal_id"
output "subscription_id"
output "resource_group_name"
```

---

### 4. `terraform/azure-ml/environments/dev.tfvars`

```hcl
environment    = "dev"
location       = "eastus"
location_short = "eus"
model_name     = "fraud-detection"
cost_center    = "ml-platform"
team           = "ml-platform-team"
allow_public_network_access = true
cpu_cluster_vm_size         = "Standard_DS3_v2"
cpu_cluster_max_nodes       = 2
gpu_cluster_vm_size         = "Standard_NC24ads_A100_v4"
gpu_cluster_vm_priority     = "LowPriority"
gpu_cluster_max_nodes       = 1
gpu_inference_vm_size       = "Standard_NC24ads_A100_v4"
gpu_inference_max_nodes     = 1
acr_georeplica_location     = null
```

### 5. `terraform/azure-ml/environments/staging.tfvars`

Same shape as dev but:
- `gpu_cluster_max_nodes = 2`
- `gpu_inference_max_nodes = 2`
- `gpu_cluster_vm_priority = "Dedicated"`
- `allow_public_network_access = false` (private endpoint path)

### 6. `terraform/azure-ml/environments/production.tfvars`

Same shape as staging but:
- `gpu_cluster_vm_size = "Standard_ND96isr_H100_v5"` (H100 NDv5)
- `gpu_cluster_max_nodes = 4`
- `gpu_inference_vm_size = "Standard_NC40ads_H100_v5"`
- `gpu_inference_max_nodes = 4`
- `acr_georeplica_location = "westeurope"`

---

### 7. `terraform/azure-ml/README.md`

Follow the exact structure of `terraform/gcp-vertex-ai/` comments. Include:
- What this module provisions (table)
- Prerequisites (Azure subscription, quota requests for NDv5)
- Apply commands per environment
- Integration bridge note (GPU cluster at scale → platform repo)
- SDK v2 note
- GPU quota note: NDv5/NDv4 require support ticket, 1–4 week wait

---

### 8. `dvc/remote-storage/azure.remote.sample` — fix the existing stub

Current file only has:
```ini
[core]
    remote = origin
['remote "origin"']
    url = azure://mlops-dvc-container/path
```

Replace with a complete sample matching `s3.remote.sample` depth:
```ini
[core]
    remote = origin

['remote "origin"']
    url = azure://dvc-remote
    account_name = <storage-account-name>
    # Auth option 1 — Managed Identity (recommended for CI and AKS workloads)
    # No credentials needed; identity must have Storage Blob Data Contributor role.

    # Auth option 2 — SAS token (for cross-tenant access)
    # sas_token = <token>   # store in GitHub Actions secret DVC_AZURE_SAS_TOKEN

    # Auth option 3 — connection string (dev only, never commit)
    # connection_string = DefaultEndpointsProtocol=https;...
```

Add a `README.md` note in `dvc/remote-storage/README.md` adding Azure to the
supported remotes table.

---

### 9. CI credential block — `ci/github-actions/model-training/train.yml`

The existing workflow only handles AWS and Azure Storage connection string.
Add a dedicated Azure ML auth step using OIDC federation (no stored secrets):

```yaml
# Add as a new step after "Configure DVC remote" in train.yml
- name: Authenticate to Azure (OIDC)
  if: github.event.inputs.dvc_remote == 'azure'
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

- name: Configure Azure ML workspace
  if: github.event.inputs.dvc_remote == 'azure'
  env:
    AZURE_ML_WORKSPACE: ${{ secrets.AZURE_ML_WORKSPACE }}
    AZURE_ML_RESOURCE_GROUP: ${{ secrets.AZURE_ML_RESOURCE_GROUP }}
    MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  run: |
    az ml job create \
      --workspace-name "${AZURE_ML_WORKSPACE}" \
      --resource-group "${AZURE_ML_RESOURCE_GROUP}" \
      --file ci/azure-ml/train-job.yaml
```

Add `ci/azure-ml/train-job.yaml` — Azure ML job definition YAML that maps
to the existing DVC pipeline stages. Include `compute`, `environment`,
`code`, `command`, `inputs`, `outputs` blocks. Reference cluster names
from Terraform outputs.

---

### 10. `docs/golden-paths/model-serving.md` — Azure section

Add an **Azure ML Managed Endpoint** section after the existing
"Serving Runtime Quick Reference" section. Include:

- When to use managed endpoints vs AKS-hosted serving
- How to create a blue/green deployment targeting the endpoint from Terraform
- Traffic split YAML (`traffic: {blue: 90, green: 10}`)
- Auth mode: `AMLToken` in production, `Key` in dev
- Health probe endpoint: `GET /score` (managed endpoint health)
- Rollback: `az ml online-deployment update --traffic blue=100`

---

### 11. `docs/decisions/ADR-ML-006-infrastructure-terraform.md` — update

Add an **Azure ML** row to the Module Layout table:

```markdown
| Azure ML | `terraform/azure-ml/` | `hashicorp/azurerm` |
```

Add a paragraph under **Consequences — Neutral** noting that NDv5 H100
quotas require a support ticket and 1–4 week wait in most Azure regions,
and that the `gpu_cluster_max_nodes` validation (≤ 16) aligns with typical
enterprise quota limits.

---

## Invariant Rules for All Azure Files

- `required_version = ">= 1.6.0"` and pin all provider versions
- `local_auth_enabled = false` on every compute resource
- Every resource carries `tags = local.common_tags` (must include `cost-center`)
- No hardcoded subscription IDs, tenant IDs, or storage account names
- `sensitive = true` on outputs that carry secrets or connection strings
- File naming: `lowercase-kebab-case`, match existing repo conventions
- Comment style: match `terraform/gcp-vertex-ai/main.tf` — inline `# ---` section
  headers, beginner notes on non-obvious settings
- SDK v2 (`azure-ai-ml`) only — never reference deprecated SDK v1 imports

---

## Quick-Start Prompts

```
@workspace Create terraform/azure-ml/main.tf following the Azure ML gap fill rules

@workspace Create terraform/azure-ml/variables.tf with all required variables and validations

@workspace Create terraform/azure-ml/outputs.tf with all integration point outputs

@workspace Create all three environment tfvars files for dev, staging, and production

@workspace Fix dvc/remote-storage/azure.remote.sample to match the depth of s3.remote.sample

@workspace Add the Azure ML OIDC auth step to ci/github-actions/model-training/train.yml

@workspace Add the Azure ML managed endpoint section to docs/golden-paths/model-serving.md

@workspace Update ADR-ML-006 to include the Azure ML Terraform module
```
