# Priority 4: Improve Routing Quality

**Date**: 2026-09-04
**Status**: Completed

## Overview

Implemented routing quality improvements to strengthen MLOps-specific routing patterns and add intent coverage for newer domains.

## Implementation Details

### Routing Quality Documentation

Created comprehensive routing quality documentation in [docs/topology/ROUTING-QUALITY.md](docs/topology/ROUTING-QUALITY.md) describing:

1. **Routing Overview**: Principles for MLOps-specific routing vs generic platform routing
2. **Routing Quality Improvements**: Two primary improvements
   - Split generic platform workflows from MLOps workflows
   - Add intent coverage for newer domains
3. **Routing Quality Guidelines**: Strong MLOps routing, Generic platform routing, Routing quality principles
4. **Routing Quality Improvements Summary**: Benefits of routing quality improvements
5. **Related Resources**: Links to related documentation

### Routing Quality Improvements

#### 1. Split Generic Platform Workflows from MLOps Workflows

**MLOps Routing Patterns**:
- Experiment Tracking: MLflow-based experiment tracking and model lineage
- Data Versioning: DVC-based data versioning and remote storage
- Model Registry: Model promotion and approval gates
- Model Serving: Production-ready serving patterns (Triton, TorchServe, vLLM)
- Model Monitoring: Drift detection and performance metrics
- Model Approval: Three-gate CI evaluation and approval process
- Data Governance: Classification levels, PII handling, and retention rules
- Architecture Decisions: Decision records and operational guidance

**Generic Platform Routing**:
- Infrastructure Provisioning: GPU cluster provisioning and workload scheduling
- Base Kubernetes: Base Kubernetes primitives and manifests
- Secrets Management: Secrets management and credential handling
- OIDC Federation: Identity federation and authentication
- Policy Controls: Policy enforcement and governance
- Observability Baseline: Monitoring and alerting infrastructure

#### 2. Add Intent Coverage for Newer Domains

**Batch Inference Routing**:
- "Run batch inference" -> docs/golden-paths/batch-inference.md
- "Batch scoring" -> batch/README.md or pipelines/README.md
- "Batch quality check" -> batch/ or pipelines/
- "Batch job" -> cd/kubernetes/batch/ or cd/argo/pipelines/
- "Batch quality gate" -> policy/ and finops/

**Pipeline Orchestration Routing**:
- "Create pipeline" -> docs/golden-paths/pipeline-orchestration.md
- "Pipeline workflow" -> pipelines/ or cd/argo/pipelines/
- "Pipeline runner" -> pipelines/README.md
- "Pipeline component" -> pipelines/components/
- "Drift-triggered retraining" -> pipelines/ or ci/github-actions/pipelines/

**Distributed Training Routing**:
- "Distributed training" -> docs/golden-paths/distributed-training.md
- "Ray training" -> training/ or cd/kubernetes/training/
- "Kubeflow training" -> training/ or cd/kubernetes/training/
- "Checkpoint management" -> training/ or cd/kubernetes/training/
- "Resource allocation" -> terraform/ray-cluster/ or cd/kubernetes/training/

**Feature Store Routing**:
- "Feature store" -> docs/guides/feature-store-patterns.md
- "Feature patterns" -> docs/guides/feature-store-patterns.md
- "Feast integration" -> feature-store/ or terraform/gcp-vertex-ai/
- "Feature versioning" -> feature-store/ or dvc/

**Fairness Routing**:
- "Fairness evaluation" -> docs/golden-paths/fairness-and-explainability.md
- "Fairness metrics" -> fairness/ or ci/github-actions/fairness/
- "Bias analysis" -> fairness/ or ci/github-actions/fairness/
- "Explainability" -> fairness/ or ci/github-actions/fairness/
- "Fairness gate" -> policy/ and ci/github-actions/fairness/

**Online Learning Routing**:
- "Online learning" -> docs/golden-paths/online-learning.md
- "Online inference" -> online-learning/ or cd/kubernetes/batch/
- "Model update" -> online-learning/ or ci/github-actions/pipelines/
- "Model rollback" -> online-learning/ or ci/github-actions/pipelines/
- "Model validator" -> online-learning/ or ci/github-actions/pipelines/

**Federated Learning Routing**:
- "Federated learning" -> docs/golden-paths/federated-learning.md
- "Federated training" -> federated-learning/ or ci/github-actions/federated/
- "Privacy-preserving" -> federated-learning/ or ci/github-actions/federated/
- "Distributed coordination" -> federated-learning/ or ci/github-actions/federated/
- "Federated evaluation" -> ci/github-actions/federated/

**Multi-Cloud Serving Routing**:
- "Multi-cloud serving" -> docs/golden-paths/multi-cloud-serving.md
- "Multi-cloud routing" -> multi-cloud-serving/ or cd/kubernetes/
- "Cloud-specific serving" -> multi-cloud-serving/ or serving/
- "Cloud routing config" -> multi-cloud-serving/router.py or cd/kubernetes/
- "Cloud health check" -> multi-cloud-serving/health_check.py

**Model Optimization Routing**:
- "Model optimization" -> docs/golden-paths/model-optimization.md
- "Model pruning" -> model_optimization/pruning.py
- "Model quantization" -> model_optimization/quantisation.py
- "Model distillation" -> model_optimization/distillation/
- "Model benchmarking" -> model_optimization/benchmark.py

### Routing Intent Coverage Matrix

Created comprehensive intent coverage matrix documenting routing for all newer domains:

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

## Related Changes

### Updated Files

1. **[docs/topology/ROUTING-QUALITY.md](docs/topology/ROUTING-QUALITY.md)** - Routing quality documentation
   - Owner: @mlops-team
   - Last Reviewed: 2026-09-04
   - Source of Truth: docs/guides/, docs/decisions/
   - Depends On: docs/guides/, docs/decisions/

2. **[task-routing.md](.ai/retrieval/task-routing.md)** - Updated routing documentation
   - Owner: @mlops-team
   - Last Reviewed: 2026-09-04
   - Source of Truth: docs/golden-paths/
   - Depends On: docs/guides/, docs/decisions/
   - Added MLOps-Specific Routing - Newer Domains section
   - Added Generic Platform Routing section

3. **[improvements.md](docs/improvements.md)** - Updated completion status
   - Priority 4 marked as Done (2026-09-04)
   - Documented implementation details

## Benefits

### Routing Quality Improvements Benefits

- **Strong Routing**: Strong routing is strong and focused
- **Intent Coverage**: Intent coverage is comprehensive
- **Implementation Patterns**: Implementation patterns are specific
- **Best Practices**: Best practices are specific

## Related Resources

- [Integration Bridge](docs/topology/INTEGRATION-BRIDGE.md) - Repository responsibility map and integration contract
- [Dependency Matrix](docs/topology/DEPENDENCY-MATRIX.md) - Executable dependency matrix
- [Control Planes](docs/topology/CONTROL-PLANES.md) - Control plane and data plane architecture
- [Compatibility Contract](docs/topology/COMPATIBILITY-CONTRACT.md) - Platform manifest requirements and compatibility
- [Architecture Decision Guide](docs/ARCHITECTURE_DECISION_GUIDE.md) - Architectural decisions and patterns
- [Golden Paths](docs/golden-paths/) - End-to-end workflows and implementation guides
- [CI Workflows](ci/github-actions/) - Training, evaluation, and deployment workflows
- [CD Workflows](cd/argo/pipelines/) - Production workflow DAGs
- [Infrastructure](terraform/) - Cloud-specific ML infrastructure starter configurations

## AI Folder Update (2026-09-04)

Updated `.ai` folder contents to reflect routing quality improvements:

### Context Files Updated
- [repo_map.md](../context/repo_map.md) - Added topology directory exclusion
- [repo-summary.md](../context/repo-summary.md) - Added integration bridge documentation reference
- [project_details.md](../context/project_details.md) - Added topology documentation reference
- [architecture-overview.md](../context/architecture-overview.md) - Added topology documentation anchors
- [glossary.md](../context/glossary.md) - Added topology documentation terms
- [terminology.md](../context/terminology.md) - Added topology documentation word choices

### Session Files Updated
- [session/README.md](../session/README.md) - Documented recent session notes

### Instructions Files Updated
- [instructions/README.md](../instructions/README.md) - Documented routing quality improvements

### Retrieval Files Updated
- [retrieval/README.md](../retrieval/README.md) - Documented routing quality improvements
