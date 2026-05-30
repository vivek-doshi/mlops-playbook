# MLOps Playbook

A production-oriented, opinionated guide for the full ML lifecycle — from raw data to monitored, production-serving models. Built for engineering teams that want reproducible experiments, auditable model promotion, and operational confidence in deployed models.

**New here?** → Start with [GETTING_STARTED.md](GETTING_STARTED.md) | Concepts guide → [docs/guides/concepts.md](docs/guides/concepts.md) | GPU / Dev Container setup → [docs/local-setup.md](docs/local-setup.md)

---

## The Integration Bridge

This repository and the platform repository are intentionally coupled through a documented dependency, not treated as isolated islands.

- **Platform layer** lives in the DevOps repository (`devops-playbook`): GPU cluster provisioning, Kubernetes base manifests, secrets management, OIDC federation, Kyverno policies, and observability stack.
- **ML lifecycle layer** lives in this repository: experiment tracking, data versioning, model registry, serving infrastructure, drift monitoring, and approval policy.

This repository consumes platform primitives from `devops-playbook` and focuses on ML-specific operational workflows on top of that foundation.

---

## Prerequisites

This repository assumes your platform layer is already provisioned.

The recommended platform foundation is: [devops-playbook](https://github.com/vivek-doshi/devops-playbook)

Specifically, you need:

- GPU cluster: `devops-playbook/docs/golden-paths/mlops-workflow.md`
- Secrets management: `devops-playbook/secrets/`
- Observability stack: `devops-playbook/observability/`

---

## What's Implemented

### Experiment Tracking
- MLflow tracking server (Docker Compose: PostgreSQL + MinIO + MLflow v2.14.2) in [`mlflow/tracking-server/`](mlflow/tracking-server/)
- Built-in basic authentication enabled via `--app-name basic-auth`
- Golden path: [`docs/golden-paths/experiment-tracking.md`](docs/golden-paths/experiment-tracking.md)

### Data Versioning
- DVC remote storage samples (S3, GCS, Azure Blob) in [`dvc/remote-storage/`](dvc/remote-storage/)
- DVC pipeline template in [`dvc/pipeline-templates/train-eval-deploy.yaml`](dvc/pipeline-templates/train-eval-deploy.yaml)
- Golden path: [`docs/golden-paths/data-versioning.md`](docs/golden-paths/data-versioning.md)

### CI/CD Pipelines
- **Train** — DVC repro + MLflow run ID capture: [`ci/github-actions/model-training/train.yml`](ci/github-actions/model-training/train.yml)
- **Continuous training (Phase 1)** — Scheduled + event-driven retraining with lineage artifact output: [`ci/github-actions/model-training/continuous-training.yml`](ci/github-actions/model-training/continuous-training.yml)
- **Evaluate** — Three-gate evaluation (accuracy + drift + lineage): [`ci/github-actions/model-evaluation/evaluate.yml`](ci/github-actions/model-evaluation/evaluate.yml)
- **Deploy** — GitHub approval gate + runtime-specific kubectl rollout: [`ci/github-actions/model-deployment/deploy.yml`](ci/github-actions/model-deployment/deploy.yml)
- **Drift check** — Scheduled daily Evidently scan: [`ci/github-actions/model-monitoring/drift-check.yml`](ci/github-actions/model-monitoring/drift-check.yml)
- **Security scan** — Reusable pip-audit + gitleaks + model size check: [`ci/github-actions/_shared/reusable-mlops-scan.yml`](ci/github-actions/_shared/reusable-mlops-scan.yml)

### Model Serving
- **Triton** — Multi-framework ONNX/TensorRT/Python serving: [`serving/triton/`](serving/triton/)
- **Triton shadow deployment (Phase 1)** — Mirror traffic to shadow model safely: [`serving/triton/shadow-deployment.yaml`](serving/triton/shadow-deployment.yaml)
- **TorchServe** — Custom PyTorch .mar archive serving: [`serving/torchserve/`](serving/torchserve/)
- **vLLM** — LLM serving with OpenAI-compatible API: [`serving/vllm/`](serving/vllm/)
- Decision tree for choosing a runtime: [`serving/README.md`](serving/README.md)
- Golden path: [`docs/golden-paths/model-serving.md`](docs/golden-paths/model-serving.md)

### Monitoring
- Evidently AI drift report script: [`monitoring/evidently/drift_report.py`](monitoring/evidently/drift_report.py)
- Prometheus alert rules (warning at 0.3, critical at 0.6): [`monitoring/alerts/drift-alerts.yaml`](monitoring/alerts/drift-alerts.yaml)
- vLLM serving SLO rules (Phase 1): [`monitoring/slos/vllm-serving-slo.yaml`](monitoring/slos/vllm-serving-slo.yaml)
- Grafana model health dashboard: [`monitoring/dashboards/model-health.json`](monitoring/dashboards/model-health.json)
- Golden path: [`docs/golden-paths/model-monitoring.md`](docs/golden-paths/model-monitoring.md)

### Policy & Governance
- Model approval registry + three-gate promotion process: [`policy/model-approval/`](policy/model-approval/)
- Data classification levels (public → restricted): [`policy/data-governance/README.md`](policy/data-governance/README.md)
- PII model promotion checklist (DPO sign-off required): [`policy/data-governance/pii-model-checklist.md`](policy/data-governance/pii-model-checklist.md)
- Feature store patterns: [`docs/guides/feature-store-patterns.md`](docs/guides/feature-store-patterns.md)
- Feast feature store integration (Phase 1): [`feature-store/feast/`](feature-store/feast/)
- Metadata lineage store schema + client (Phase 1): [`mlflow/metadata-store/`](mlflow/metadata-store/)
- Fraud model card (Phase 1): [`docs/model-cards/fraud-detection-model-card.md`](docs/model-cards/fraud-detection-model-card.md)
- GPU cost governance: [`docs/guides/gpu-cost-governance.md`](docs/guides/gpu-cost-governance.md)

### Architecture Decisions (ADRs)
- [ADR-ML-001: Experiment Tracking → MLflow](docs/decisions/ADR-ML-001-experiment-tracking.md)
- [ADR-ML-002: Data Versioning → DVC](docs/decisions/ADR-ML-002-data-versioning.md)
- [ADR-ML-003: Model Serving → Three-runtime strategy](docs/decisions/ADR-ML-003-model-serving.md)
- [ADR-ML-004: Drift Monitoring → Evidently AI](docs/decisions/ADR-ML-004-drift-monitoring.md)
- [ADR-ML-005: CI/CD Platform → GitHub Actions](docs/decisions/ADR-ML-005-ci-cd-platform.md)
- [ADR-ML-006: Infrastructure → Terraform](docs/decisions/ADR-ML-006-infrastructure-terraform.md)
- [ADR-ML-007: Dev Environment → Dev Containers](docs/decisions/ADR-ML-007-dev-container.md)
- [ADR-ML-008: Model Approval → Three-Gate Policy](docs/decisions/ADR-ML-008-model-approval-policy.md)
- [ADR-ML-009: Code Quality → Pre-commit Toolchain](docs/decisions/ADR-ML-009-pre-commit-toolchain.md)

### Infrastructure
- AWS SageMaker Terraform: [`terraform/aws-sagemaker/`](terraform/aws-sagemaker/)
- GCP Vertex AI Terraform (with IAM, lifecycle, outputs): [`terraform/gcp-vertex-ai/`](terraform/gcp-vertex-ai/)
- GPU cluster reference (documentation-as-code stub, consumes platform module): [`terraform/gpu-cluster/`](terraform/gpu-cluster/)
- Azure ML Terraform (workspace, compute clusters, online endpoint, ADLS Gen2): [`terraform/azure-ml/`](terraform/azure-ml/)

---

### Phase 2 — Production Hardening

- **Multi-environment promotion** — structured dev/staging/production Kubernetes namespaces
  with Kustomize overlays, ResourceQuotas, NetworkPolicies, PodDisruptionBudgets, and
  approval gates: `cd/kubernetes/environments/`, `ci/github-actions/promotion/`
- **Fairness & explainability** — Fairlearn bias metrics, SHAP explainability reports,
  CI fairness gate with configurable per-model thresholds: `fairness/`, `policy/fairness/`
- **ML cost attribution** — pod-level cost labelling, per-model budget files,
  daily/weekly/monthly reports, Grafana dashboard: `finops/`, `monitoring/dashboards/ml-cost-attribution.json`
- **Distributed training** — KubeRay (primary) and Kubeflow PyTorchJob/TFJob (secondary),
  spot node pools, CheckpointCallback, GPU approval gate: `training/`, `cd/kubernetes/training/`
- **Batch inference** — MLflow pyfunc scorer, input validator, output quality gate,
  downstream notifier, Kubernetes Job/CronJob: `batch/`, `cd/kubernetes/batch/`
- **Pipeline orchestration** — Argo Workflows DAGs, reusable Python components,
  drift-triggered retraining pipeline, optional Vertex AI backend:
  `pipelines/`, `cd/argo/`, `terraform/vertex-pipelines/`
- **Architecture Decisions** — ADR-ML-014 through ADR-ML-018 in `docs/decisions/`



| Task | Start here |
|------|-----------|
| First experiment | [GETTING_STARTED.md](GETTING_STARTED.md) |
| Understand MLOps concepts in this repo | [docs/guides/concepts.md](docs/guides/concepts.md) |
| Local / GPU / Dev Container setup | [docs/local-setup.md](docs/local-setup.md) |
| Full lifecycle walkthrough | [docs/golden-paths/mlops-workflow.md](docs/golden-paths/mlops-workflow.md) |
| Log metrics in code | [experiment-tracking.md](docs/golden-paths/experiment-tracking.md) |
| Version a dataset | [data-versioning.md](docs/golden-paths/data-versioning.md) |
| Promote a model | [model-registry.md](docs/golden-paths/model-registry.md) |
| Choose a serving runtime | [model-serving.md](docs/golden-paths/model-serving.md) |
| Monitor for drift | [model-monitoring.md](docs/golden-paths/model-monitoring.md) |
| Understand tool choices | [docs/decisions/](docs/decisions/) |

---

## Default Tooling Posture

| Tool | Role | Why |
|------|------|-----|
| MLflow | Experiment tracking + model registry | Self-hostable, no vendor lock-in, data residency |
| DVC | Data versioning + pipeline runner | Git-native, remote-agnostic, zero server required |
| Evidently AI | Drift monitoring | Open-source, Prometheus-compatible, works offline |
| Triton | Classical model serving | Multi-framework, dynamic batching, GPU acceleration |
| TorchServe | PyTorch serving | Native .mar handlers, custom pre/post-processing |
| vLLM | LLM serving | PagedAttention, OpenAI-compatible API |

W&B can be added as an optional integration for teams with budget, but is not the default dependency.

---

## Governance Boundary

| What | Where |
|------|-------|
| GPU node pool provisioning | `devops-playbook` |
| Kubernetes RBAC + namespaces | `devops-playbook` |
| Secrets management / Vault | `devops-playbook` |
| KEDA scale-to-zero | `devops-playbook` |
| ML experiment tracking | This repo |
| Model serving configs | This repo |
| Drift monitoring | This repo |
| Model approval policy | This repo |
