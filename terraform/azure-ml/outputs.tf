# azure-ml/outputs.tf
#
# Exposes integration points for downstream consumers:
#   - GitHub Actions secrets (MLflow tracking URI, App Insights connection string)
#   - DVC remote configuration (storage account name + container)
#   - Serving deploy scripts (endpoint scoring URI, cluster names)
#   - Platform team cross-references (workspace ID, ACR login server)

# ---------------------------------------------------------------------------
# WORKSPACE
# ---------------------------------------------------------------------------

output "workspace_id" {
  description = "Azure ML Workspace resource ID. Used by `az ml` CLI commands and SDK v2 MLClient initialisation."
  value       = azurerm_machine_learning_workspace.ml.id
}

output "workspace_name" {
  description = "Azure ML Workspace name. Set as GitHub Actions secret AZURE_ML_WORKSPACE for CI job submissions."
  value       = azurerm_machine_learning_workspace.ml.name
}

output "workspace_resource_group" {
  description = "Resource group containing the workspace. Set as GitHub Actions secret AZURE_ML_RESOURCE_GROUP."
  value       = azurerm_resource_group.ml.name
}

output "mlflow_tracking_uri" {
  description = "AzureML MLflow tracking URI (azureml:// format). Set as GitHub Actions secret MLFLOW_TRACKING_URI. SDK v2 resolves this automatically when authenticated."
  value       = "azureml://eastus.api.azureml.ms/mlflow/v1.0/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.ml.name}/providers/Microsoft.MachineLearningServices/workspaces/${azurerm_machine_learning_workspace.ml.name}"
}

output "workspace_discovery_url" {
  description = "Azure ML workspace discovery URL. Used by SDK v2 MLClient when authenticating non-interactively."
  value       = "https://ml.azure.com/workspaces/${azurerm_machine_learning_workspace.ml.id}"
}

output "workspace_principal_id" {
  description = "Object ID of the workspace system-assigned managed identity. Used to grant additional RBAC roles outside this module."
  value       = azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

# ---------------------------------------------------------------------------
# STORAGE
# ---------------------------------------------------------------------------

output "storage_account_name" {
  description = "Storage account name. Required for DVC remote configuration and dataset registration."
  value       = azurerm_storage_account.ml.name
}

output "storage_account_id" {
  description = "Storage account resource ID. Used for additional role assignments from calling modules."
  value       = azurerm_storage_account.ml.id
}

output "artifacts_container_name" {
  description = "Blob container name for ML artefacts (model binaries, evaluation reports). Used in MLflow artifact store configuration."
  value       = azurerm_storage_container.ml_artifacts.name
}

output "dvc_remote_container_name" {
  description = "Blob container name for DVC dataset cache objects."
  value       = azurerm_storage_container.dvc_remote.name
}

output "dvc_remote_url" {
  description = "DVC remote URL in azure:// format. Paste into .dvc/config under url = <this value>."
  value       = "azure://${azurerm_storage_container.dvc_remote.name}"
}

# ---------------------------------------------------------------------------
# COMPUTE CLUSTERS
# ---------------------------------------------------------------------------

output "cpu_cluster_name" {
  description = "CPU compute cluster name. Reference in Azure ML job YAML as compute: azureml:<this value>."
  value       = azurerm_machine_learning_compute_cluster.cpu.name
}

output "gpu_training_cluster_name" {
  description = "GPU training compute cluster name. Reference in training job YAML and distributed training configs."
  value       = azurerm_machine_learning_compute_cluster.gpu_training.name
}

output "gpu_inference_cluster_name" {
  description = "GPU inference compute cluster name. Used for batch inference and pipeline inference steps."
  value       = azurerm_machine_learning_compute_cluster.gpu_inference.name
}

output "gpu_training_vm_size" {
  description = "VM size used by the GPU training cluster. Exposed for documentation and cost attribution."
  value       = azurerm_machine_learning_compute_cluster.gpu_training.vm_size
}

# ---------------------------------------------------------------------------
# ONLINE ENDPOINT
# ---------------------------------------------------------------------------

output "endpoint_name" {
  description = "Online endpoint resource name. Used by blue/green deployment scripts and traffic split updates."
  value       = azurerm_machine_learning_online_endpoint.serving.name
}

output "endpoint_scoring_uri" {
  description = "HTTPS scoring URI for the managed endpoint. POST JSON payloads here for real-time inference."
  value       = azurerm_machine_learning_online_endpoint.serving.scoring_uri
}

output "endpoint_swagger_uri" {
  description = "Swagger/OpenAPI spec URI for the managed endpoint. Useful for SDK clients and API gateway integration."
  value       = azurerm_machine_learning_online_endpoint.serving.swagger_uri
}

output "endpoint_principal_id" {
  description = "Object ID of the endpoint system-assigned managed identity. Grant additional RBAC roles here if the scoring container needs access to other Azure services."
  value       = azurerm_machine_learning_online_endpoint.serving.identity[0].principal_id
}

# ---------------------------------------------------------------------------
# CONTAINER REGISTRY
# ---------------------------------------------------------------------------

output "acr_login_server" {
  description = "ACR login server hostname (e.g. cracmlxyz123.azurecr.io). Used in Docker build/push commands and Kubernetes imagePullSecrets."
  value       = azurerm_container_registry.ml.login_server
}

output "acr_id" {
  description = "Container registry resource ID. Used for additional role assignments from platform modules."
  value       = azurerm_container_registry.ml.id
}

# ---------------------------------------------------------------------------
# KEY VAULT
# ---------------------------------------------------------------------------

output "key_vault_id" {
  description = "Key Vault resource ID. Grant Key Vault Secrets Officer role to engineers who need to write secrets."
  value       = azurerm_key_vault.ml.id
}

output "key_vault_uri" {
  description = "Key Vault vault URI (https://<name>.vault.azure.net/). Use in SDK v2 for secret store references."
  value       = azurerm_key_vault.ml.vault_uri
}

# ---------------------------------------------------------------------------
# OBSERVABILITY
# ---------------------------------------------------------------------------

output "application_insights_connection_string" {
  description = "Application Insights connection string. Set as APPLICATIONINSIGHTS_CONNECTION_STRING in serving containers. Mark as secret — contains instrumentation key."
  value       = azurerm_application_insights.ml.connection_string
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace resource ID. Used to configure diagnostic settings on additional resources."
  value       = azurerm_log_analytics_workspace.ml.id
}

# ---------------------------------------------------------------------------
# IDENTITY & SUBSCRIPTION
# ---------------------------------------------------------------------------

output "subscription_id" {
  description = "Azure subscription ID. Used by CI/CD scripts to scope az CLI commands."
  value       = data.azurerm_client_config.current.subscription_id
}

output "resource_group_name" {
  description = "Resource group name. Convenience alias for workspace_resource_group."
  value       = azurerm_resource_group.ml.name
}
