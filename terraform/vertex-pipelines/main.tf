terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ──────────────────────────────────────────────────────────────────────────────
# Vertex AI Pipeline Storage Bucket
# ──────────────────────────────────────────────────────────────────────────────
resource "google_storage_bucket" "pipeline_artifacts" {
  name          = "${var.project_id}-vertex-pipeline-artifacts"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    cost-center  = var.cost_center
    team         = var.team
    environment  = var.environment
    managed-by   = "terraform"
  }
}

# ──────────────────────────────────────────────────────────────────────────────
# Service Account for Vertex Pipelines
# ──────────────────────────────────────────────────────────────────────────────
resource "google_service_account" "vertex_pipeline_sa" {
  account_id   = "vertex-pipeline-runner"
  display_name = "Vertex AI Pipeline Runner SA"
  project      = var.project_id
}

resource "google_project_iam_member" "vertex_pipeline_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_pipeline_sa.email}"
}

resource "google_project_iam_member" "vertex_pipeline_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.vertex_pipeline_sa.email}"
}

resource "google_project_iam_member" "vertex_pipeline_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.vertex_pipeline_sa.email}"
}

# ──────────────────────────────────────────────────────────────────────────────
# Artifact Registry for pipeline component images
# ──────────────────────────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "pipeline_images" {
  location      = var.region
  repository_id = "mlops-pipeline-images"
  description   = "Container images for MLOps pipeline components"
  format        = "DOCKER"

  labels = {
    cost-center = var.cost_center
    team        = var.team
    environment = var.environment
  }
}

# ──────────────────────────────────────────────────────────────────────────────
# Vertex AI Metadata Store (tracks pipeline lineage)
# ──────────────────────────────────────────────────────────────────────────────
resource "google_vertex_ai_metadata_store" "default" {
  name        = "default"
  region      = var.region
  description = "MLOps pipeline metadata store"
  project     = var.project_id
}

# ──────────────────────────────────────────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────────────────────────────────────────
output "pipeline_artifacts_bucket" {
  value = google_storage_bucket.pipeline_artifacts.name
}

output "vertex_pipeline_sa_email" {
  value = google_service_account.vertex_pipeline_sa.email
}

output "artifact_registry_hostname" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.pipeline_images.repository_id}"
}
