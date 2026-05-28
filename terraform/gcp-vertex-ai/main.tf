# gcp-vertex-ai/main.tf
#
# Provisions GCP infrastructure for the ML platform:
#   - Cloud Storage bucket for MLflow artifacts.
#   - Vertex AI Feature Store.
#   - IAM binding so the MLflow service account can read/write artifacts.
#
# BEGINNER NOTE:
#   Terraform creates cloud resources declaratively — you describe WHAT you want
#   and Terraform figures out the API calls to make it happen.
#   Run `terraform plan` to preview changes before `terraform apply`.

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------------------------
# GCS ARTIFACT BUCKET
# MLflow stores model binaries, plots, and evaluation reports here.
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "ml_artifacts" {
  name                        = var.artifact_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true

  # Prevent accidental deletion of the bucket containing all model artifacts.
  lifecycle {
    prevent_destroy = true
  }

  # Versioning allows recovery of accidentally overwritten artifacts.
  versioning {
    enabled = true
  }

  # Lifecycle rule: transition objects older than 90 days to Nearline storage
  # to reduce costs (Nearline is ~50% cheaper than Standard for infrequent access).
  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 90
    }
  }
}

# ---------------------------------------------------------------------------
# IAM BINDING — MLflow Service Account → Artifact Bucket
# Grants the MLflow tracking server's service account permission to read
# and write objects in the artifact bucket.
#
# The service account email is passed in as a variable so this module can
# be used in multiple environments (dev, staging, production) without
# changing the resource definitions.
# ---------------------------------------------------------------------------
resource "google_storage_bucket_iam_member" "mlflow_artifact_access" {
  bucket = google_storage_bucket.ml_artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.mlflow_service_account_email}"
}

# ---------------------------------------------------------------------------
# VERTEX AI FEATURE STORE
# Stores pre-computed features for training and online serving.
# See docs/guides/feature-store-patterns.md for usage patterns.
# ---------------------------------------------------------------------------
resource "google_vertex_ai_featurestore" "primary" {
  name   = var.featurestore_name
  region = var.region

  # Online serving config controls how many nodes back the online serving API.
  # Start with 1 node and increase based on QPS requirements.
  online_serving_config {
    fixed_node_count = 1
  }

  labels = {
    managed-by  = "terraform"
    environment = "production"
    team        = "ml-platform"
  }
}

# ---------------------------------------------------------------------------
# OUTPUTS
# ---------------------------------------------------------------------------
# Outputs are used by other Terraform modules and by application configuration.

output "artifact_bucket_name" {
  description = "Name of the GCS bucket used for MLflow artifact storage"
  value       = google_storage_bucket.ml_artifacts.name
}

output "artifact_bucket_url" {
  description = "gs:// URL for use as MLFLOW_DEFAULT_ARTIFACT_ROOT"
  value       = "gs://${google_storage_bucket.ml_artifacts.name}"
}

output "featurestore_id" {
  description = "Vertex AI Feature Store resource ID"
  value       = google_vertex_ai_featurestore.primary.id
}
