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
