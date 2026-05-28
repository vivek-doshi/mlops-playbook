variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "us-central1"
}

variable "artifact_bucket_name" {
  type        = string
  description = "GCS bucket for artifacts"
}

variable "featurestore_name" {
  type        = string
  description = "Vertex AI Feature Store name"
  default     = "mlops-featurestore"
}

# Service account that the MLflow tracking server runs as.
# This account is granted roles/storage.objectAdmin on the artifact bucket.
# Format: <name>@<project>.iam.gserviceaccount.com
variable "mlflow_service_account_email" {
  type        = string
  description = "Email of the GCP service account used by the MLflow tracking server"
}
