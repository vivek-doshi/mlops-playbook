# Routing Quality

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-09-04
**Source of Truth**: docs/topology/INTEGRATION-BRIDGE.md
**Depends On**: docs/guides/, docs/decisions/
---

## Routing Overview

This document describes the routing quality improvements for the MLOps repository. The routing system has been strengthened to:

1. **Split generic platform workflows from MLOps workflows**: The MLOps routes are strong; the inherited generic routes dilute them
2. **Add intent coverage for the repo’s actual newer domains**: Batch inference, pipeline orchestration, distributed training, feature store, fairness, online learning, federated learning, multi-cloud serving, and model optimization

## Routing Principles

### MLOps-Specific Routing

The MLOps repository implements strong, MLOps-specific routing patterns that focus on ML lifecycle workflows:

- **Experiment Tracking**: MLflow-based experiment tracking and model lineage
- **Data Versioning**: DVC-based data versioning and remote storage
- **Model Registry**: Model promotion and approval gates
- **Model Serving**: Production-ready serving patterns (Triton, TorchServe, vLLM)
- **Model Monitoring**: Drift detection and performance metrics
- **Model Approval**: Three-gate CI evaluation and approval process
- **Data Governance**: Classification levels, PII handling, and retention rules
- **Architecture Decisions**: Decision records and operational guidance

### Generic Platform Routing

The platform repository implements generic routing patterns that focus on infrastructure and operational workflows:

- **Infrastructure Provisioning**: GPU cluster provisioning and workload scheduling
- **Base Kubernetes**: Base Kubernetes primitives and manifests
- **Secrets Management**: Secrets management and credential handling
- **OIDC Federation**: Identity federation and authentication
- **Policy Controls**: Policy enforcement and governance
- **Observability Baseline**: Monitoring and alerting infrastructure

## Routing Quality Improvements

### 1. Split Generic Platform Workflows from MLOps Workflows

The routing system has been strengthened to separate generic platform workflows from MLOps workflows:

#### MLOps Routing Patterns

**Strong MLOps Routing**:
- **Experiment Tracking**: MLflow-based experiment tracking and model lineage
- **Data Versioning**: DVC-based data versioning and remote storage
- **Model Registry**: Model promotion and approval gates
- **Model Serving**: Production-ready serving patterns (Triton, TorchServe, vLLM)
- **Model Monitoring**: Drift detection and performance metrics
- **Model Approval**: Three-gate CI evaluation and approval process
- **Data Governance**: Classification levels, PII handling, and retention rules
- **Architecture Decisions**: Decision records and operational guidance

**Generic Platform Routing**:
- **Infrastructure Provisioning**: GPU cluster provisioning and workload scheduling
- **Base Kubernetes**: Base Kubernetes primitives and manifests
- **Secrets Management**: Secrets management and credential handling
- **OIDC Federation**: Identity federation and authentication
- **Policy Controls**: Policy enforcement and governance
- **Observability Baseline**: Monitoring and alerting infrastructure

### 2. Add Intent Coverage for Newer Domains

The routing system has been strengthened to add intent coverage for the repo's actual newer domains:

#### Batch Inference Routing

**Intent Coverage**:
- "Run batch inference" -> docs/golden-paths/batch-inference.md
- "Batch scoring" -> batch/README.md or pipelines/README.md
- "Batch quality check" -> batch/ or pipelines/
- "Batch job" -> cd/kubernetes/batch/ or cd/argo/pipelines/
- "Batch quality gate" -> policy/ and finops/

**Implementation**:
- `batch/` - MLflow pyfunc-based batch scoring with input validation, output quality gating, and downstream notification
- `cd/kubernetes/batch/` - K8s Job + CronJob manifests for batch inference
- `ci/github-actions/batch/` - Batch quality check workflows

#### Pipeline Orchestration Routing

**Intent Coverage**:
- "Create pipeline" -> docs/golden-paths/pipeline-orchestration.md
- "Pipeline workflow" -> pipelines/ or cd/argo/pipelines/
- "Pipeline runner" -> pipelines/README.md
- "Pipeline component" -> pipelines/components/
- "Drift-triggered retraining" -> pipelines/ or ci/github-actions/pipelines/

**Implementation**:
- `pipelines/` - Local-mode pipeline runners (training, batch inference, drift-triggered retraining)
- `pipelines/components/` - Reusable step components
- `cd/argo/pipelines/` - Argo Workflows DAG definitions for production execution
- `ci/github-actions/pipelines/` - Pipeline workflow templates

#### Distributed Training Routing

**Intent Coverage**:
- "Distributed training" -> docs/golden-paths/distributed-training.md
- "Ray training" -> training/ or cd/kubernetes/training/
- "Kubeflow training" -> training/ or cd/kubernetes/training/
- "Checkpoint management" -> training/ or cd/kubernetes/training/
- "Resource allocation" -> terraform/ray-cluster/ or cd/kubernetes/training/

**Implementation**:
- `training/` - Distributed training scripts for KubeRay (primary) and Kubeflow (secondary)
- `cd/kubernetes/training/` - Kubernetes training manifests
- `terraform/ray-cluster/` - Ray cluster configuration
- `cd/kubernetes/training/checkpointing-pvc.yaml` - Checkpoint management

#### Feature Store Routing

**Intent Coverage**:
- "Feature store" -> docs/guides/feature-store-patterns.md
- "Feature patterns" -> docs/guides/feature-store-patterns.md
- "Feast integration" -> feature-store/ or terraform/gcp-vertex-ai/
- "Feature versioning" -> feature-store/ or dvc/

**Implementation**:
- `feature-store/` - Feast integration patterns
- `docs/guides/feature-store-patterns.md` - Feature store patterns and best practices
- `terraform/gcp-vertex-ai/` - Vertex AI feature store configuration
- `dvc/` - Data versioning and feature store integration

#### Fairness Routing

**Intent Coverage**:
- "Fairness evaluation" -> docs/golden-paths/fairness-and-explainability.md
- "Fairness metrics" -> fairness/ or ci/github-actions/fairness/
- "Bias analysis" -> fairness/ or ci/github-actions/fairness/
- "Explainability" -> fairness/ or ci/github-actions/fairness/
- "Fairness gate" -> policy/ and ci/github-actions/fairness/

**Implementation**:
- `fairness/` - Fairlearn bias metrics and SHAP explainability analysis
- `ci/github-actions/fairness/` - CI fairness gate workflows
- `docs/golden-paths/fairness-and-explainability.md` - Fairness and explainability patterns
- `docs/guides/fairness-patterns.md` - Fairness best practices

#### Online Learning Routing

**Intent Coverage**:
- "Online learning" -> docs/golden-paths/online-learning.md
- "Online inference" -> online-learning/ or cd/kubernetes/batch/
- "Model update" -> online-learning/ or ci/github-actions/pipelines/
- "Model rollback" -> online-learning/ or ci/github-actions/pipelines/
- "Model validator" -> online-learning/ or ci/github-actions/pipelines/

**Implementation**:
- `online-learning/` - Online learning patterns and workflows
- `online-learning/consumer.py` - Online learning consumer
- `online-learning/updater.py` - Model update patterns
- `online-learning/validator.py` - Model validation patterns
- `online-learning/rollback.py` - Model rollback patterns

#### Federated Learning Routing

**Intent Coverage**:
- "Federated learning" -> docs/golden-paths/federated-learning.md
- "Federated training" -> federated-learning/ or ci/github-actions/federated/
- "Privacy-preserving" -> federated-learning/ or ci/github-actions/federated/
- "Distributed coordination" -> federated-learning/ or ci/github-actions/federated/
- "Federated evaluation" -> ci/github-actions/federated/

**Implementation**:
- `federated-learning/` - Federated learning patterns and workflows
- `federated-learning/coordinator.py` - Distributed coordination
- `federated-learning/party.py` - Party patterns
- `ci/github-actions/federated/` - Federated evaluation workflows
- `ci/github-actions/federated/federated-eval.yml` - Federated evaluation workflow

#### Multi-Cloud Serving Routing

**Intent Coverage**:
- "Multi-cloud serving" -> docs/golden-paths/multi-cloud-serving.md
- "Multi-cloud routing" -> multi-cloud-serving/ or cd/kubernetes/
- "Cloud-specific serving" -> multi-cloud-serving/ or serving/
- "Cloud routing config" -> multi-cloud-serving/router.py or cd/kubernetes/
- "Cloud health check" -> multi-cloud-serving/health_check.py

**Implementation**:
- `multi-cloud-serving/` - Multi-cloud serving patterns and workflows
- `multi-cloud-serving/router.py` - Cloud routing configuration
- `multi-cloud-serving/registry.py` - Cloud registry patterns
- `multi-cloud-serving/health_check.py` - Cloud health check patterns
- `serving/` - Production-ready serving stacks for multi-cloud serving

#### Model Optimization Routing

**Intent Coverage**:
- "Model optimization" -> docs/golden-paths/model-optimization.md
- "Model pruning" -> model_optimization/pruning.py
- "Model quantization" -> model_optimization/quantisation.py
- "Model distillation" -> model_optimization/distillation/
- "Model benchmarking" -> model_optimization/benchmark.py

**Implementation**:
- `model_optimization/` - Model optimization patterns and workflows
- `model_optimization/pruning.py` - Model pruning patterns
- `model_optimization/quantisation.py` - Model quantization patterns
- `model_optimization/distillation/` - Model distillation patterns
- `model_optimization/benchmark.py` - Model benchmarking patterns

## Routing Intent Coverage

### Intent Coverage Matrix

| Intent | Routing | Implementation |
|--------|---------|---------------|
| Batch Inference | docs/golden-paths/batch-inference.md | batch/, cd/kubernetes/batch/, ci/github-actions/batch/ |
| Pipeline Orchestration | docs/golden-paths/pipeline-orchestration.md | pipelines/, cd/argo/pipelines/, ci/github-actions/pipelines/ |
| Distributed Training | docs/golden-paths/distributed-training.md | training/, cd/kubernetes/training/, terraform/ray-cluster/ |
| Feature Store | docs/guides/feature-store-patterns.md | feature-store/, terraform/gcp-vertex-ai/, dvc/ |
| Fairness | docs/golden-paths/fairness-and-explainability.md | fairness/, ci/github-actions/fairness/, docs/guides/ |
| Online Learning | docs/golden-paths/online-learning.md | online-learning/, cd/kubernetes/batch/, ci/github-actions/pipelines/ |
| Federated Learning | docs/golden-paths/federated-learning.md | federated-learning/, ci/github-actions/federated/ |
| Multi-Cloud Serving | docs/golden-paths/multi-cloud-serving.md | multi-cloud-serving/, serving/, cd/kubernetes/ |
| Model Optimization | docs/golden-paths/model-optimization.md | model_optimization/, model_optimization/distillation/, model_optimization/benchmark/ |

## Routing Quality Guidelines

### 1. Strong MLOps Routing

- **Strong Routing**: MLOps-specific routing patterns are strong and focused
- **Intent Coverage**: Intent coverage for MLOps-specific domains
- **Implementation Patterns**: Implementation patterns are MLOps-specific
- **Best Practices**: Best practices are MLOps-specific

### 2. Generic Platform Routing

- **Generic Routing**: Generic platform routing patterns are generic and infrastructure-focused
- **Infrastructure Patterns**: Infrastructure patterns are generic
- **Operational Workflows**: Operational workflows are generic
- **Platform Primitives**: Platform primitives are generic

### 3. Routing Quality Principles

- **Strong Routing**: Strong routing is strong and focused
- **Intent Coverage**: Intent coverage is comprehensive
- **Implementation Patterns**: Implementation patterns are specific
- **Best Practices**: Best practices are specific

## Routing Quality Improvements Summary

### Routing Quality Improvements

1. **Split Generic Platform Workflows from MLOps Workflows**: The routing system has been strengthened to separate generic platform workflows from MLOps workflows
2. **Add Intent Coverage for Newer Domains**: The routing system has been strengthened to add intent coverage for the repo's actual newer domains

### Routing Quality Improvements Benefits

- **Strong Routing**: Strong routing is strong and focused
- **Intent Coverage**: Intent coverage is comprehensive
- **Implementation Patterns**: Implementation patterns are specific
- **Best Practices**: Best practices are specific

## Related Resources

- [Integration Bridge](INTEGRATION-BRIDGE.md) - Repository responsibility map and integration contract
- [Dependency Matrix](DEPENDENCY-MATRIX.md) - Executable dependency matrix
- [Control Planes](CONTROL-PLANES.md) - Control plane and data plane architecture
- [Compatibility Contract](COMPATIBILITY-CONTRACT.md) - Platform manifest requirements and compatibility
- [Architecture Decision Guide](ARCHITECTURE_DECISION_GUIDE.md) - Architectural decisions and patterns
- [Golden Paths](docs/golden-paths/) - End-to-end workflows and implementation guides
- [CI Workflows](ci/github-actions/) - Training, evaluation, and deployment workflows
- [CD Workflows](cd/argo/pipelines/) - Production workflow DAGs
- [Infrastructure](terraform/) - Cloud-specific ML infrastructure starter configurations
