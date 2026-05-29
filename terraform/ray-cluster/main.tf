# terraform/ray-cluster/main.tf
# Terraform module: Ray cluster on Kubernetes (GPU node pool + KubeRay operator).
#
# PURPOSE:
#   Provisions:
#     - A GPU node pool in an existing Kubernetes cluster (EKS/GKE/AKS)
#     - KubeRay operator via Helm
#     - RBAC for KubeRay to manage RayJob / RayCluster CRDs
#
# USAGE:
#   terraform init
#   terraform apply -var-file=terraform.tfvars
#
# NOTE: This module assumes the cluster already exists and kubeconfig is
#       configured.  It does NOT create the cluster itself — use the
#       appropriate cluster module (aws-sagemaker, gcp-vertex-ai, etc.).

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.13.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.29.0"
    }
  }
}

# --------------------------------------------------------------------------- #
# Variables
# --------------------------------------------------------------------------- #

variable "namespace" {
  description = "Kubernetes namespace for the KubeRay operator."
  type        = string
  default     = "kuberay-operator"
}

variable "kuberay_version" {
  description = "KubeRay Helm chart version."
  type        = string
  default     = "1.1.1"
}

variable "ray_version" {
  description = "Ray version to use in RayCluster images."
  type        = string
  default     = "2.9.0"
}

variable "gpu_node_pool_enabled" {
  description = "Whether to create a dedicated GPU node pool."
  type        = bool
  default     = true
}

variable "gpu_instance_type" {
  description = "Cloud instance type for GPU nodes (e.g., g5.2xlarge on AWS)."
  type        = string
  default     = "g5.2xlarge"
}

variable "gpu_min_nodes" {
  description = "Minimum GPU node count."
  type        = number
  default     = 0
}

variable "gpu_max_nodes" {
  description = "Maximum GPU node count."
  type        = number
  default     = 8
}

variable "spot_enabled" {
  description = "Use spot/preemptible GPU nodes to reduce cost."
  type        = bool
  default     = true
}

variable "cost_center" {
  description = "Cost attribution label value."
  type        = string
  default     = "ml-platform"
}

variable "team" {
  description = "Team label for cost attribution."
  type        = string
  default     = "ml-platform"
}

# --------------------------------------------------------------------------- #
# KubeRay operator namespace
# --------------------------------------------------------------------------- #

resource "kubernetes_namespace" "kuberay" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "cost-center"                  = var.cost_center
      "team"                         = var.team
    }
  }
}

# --------------------------------------------------------------------------- #
# KubeRay operator (Helm)
# --------------------------------------------------------------------------- #

resource "helm_release" "kuberay_operator" {
  name       = "kuberay-operator"
  repository = "https://ray-project.github.io/kuberay-helm/"
  chart      = "kuberay-operator"
  version    = var.kuberay_version
  namespace  = kubernetes_namespace.kuberay.metadata[0].name

  set {
    name  = "image.tag"
    value = "v${var.kuberay_version}"
  }

  set {
    name  = "batchScheduler.enabled"
    value = "true"
  }

  depends_on = [kubernetes_namespace.kuberay]
}

# --------------------------------------------------------------------------- #
# RBAC — allow KubeRay to manage RayJob/RayCluster in all namespaces
# --------------------------------------------------------------------------- #

resource "kubernetes_cluster_role" "kuberay_manager" {
  metadata {
    name = "kuberay-manager"
  }

  rule {
    api_groups = ["ray.io"]
    resources  = ["rayclusters", "rayjobs", "rayservices"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services", "endpoints", "persistentvolumeclaims", "events"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }

  rule {
    api_groups = ["batch"]
    resources  = ["jobs"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
}

resource "kubernetes_cluster_role_binding" "kuberay_manager" {
  metadata {
    name = "kuberay-manager"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.kuberay_manager.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = "kuberay-operator"
    namespace = var.namespace
  }
}

# --------------------------------------------------------------------------- #
# Outputs
# --------------------------------------------------------------------------- #

output "kuberay_namespace" {
  description = "Namespace where KubeRay operator is deployed."
  value       = kubernetes_namespace.kuberay.metadata[0].name
}

output "kuberay_operator_release" {
  description = "Helm release name for the KubeRay operator."
  value       = helm_release.kuberay_operator.name
}
