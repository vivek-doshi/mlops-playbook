# Task Routing

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-09-04
**Source of Truth**: docs/golden-paths/
**Depends On**: docs/guides/, docs/decisions/
---

Routes user intent to the minimum correct repository domain.

## Primary Routing

- "Set up MLOps CI" -> ci/github-actions/ and ci/github-actions/_shared/.
- "Deploy a model" -> serving/, cd/kubernetes/, and terraform/<cloud-target>/.
- "Deploy to Kubernetes" -> cd/kubernetes/ and cd/argo/.
- "Provision ML infrastructure" -> terraform/<cloud-target>/.
- "Add security checks" -> ci/github-actions/_shared/reusable-mlops-scan.yml and policy/.
- "Incident response" -> docs/runbooks/, monitoring/, and external `devops-playbook` notification controls.
- "Observability and alerting" -> monitoring/ and external `devops-playbook` observability controls.
- "Cost control/FinOps" -> finops/.

## MLOps-Specific Routing

- "Log an experiment / track a run" -> docs/golden-paths/experiment-tracking.md
- "Log metrics / parameters" -> docs/golden-paths/experiment-tracking.md
- "Version a dataset / DVC" -> docs/golden-paths/data-versioning.md
- "Create a training pipeline / dvc repro" -> docs/golden-paths/model-training-pipeline.md
- "Promote a model / model registry / Staging to Production" -> docs/golden-paths/model-registry.md + policy/model-approval/
- "Deploy a model / choose serving runtime / Triton / TorchServe / vLLM" -> docs/golden-paths/model-serving.md + serving/
- "Monitor for drift / Evidently / data drift" -> docs/golden-paths/model-monitoring.md + monitoring/evidently/drift_report.py
- "Drift alert / Prometheus alert / Grafana dashboard" -> monitoring/alerts/ + monitoring/dashboards/
- "Model approval gate / policy" -> policy/model-approval/README.md + policy/model-approval/approved-versions.yaml
- "Data governance / PII / classification" -> policy/data-governance/README.md
- "Feature store / Vertex AI features" -> docs/guides/feature-store-patterns.md + terraform/gcp-vertex-ai/
- "GPU cost / GPU approval / KEDA scale-to-zero" -> docs/guides/gpu-cost-governance.md
- "End-to-end MLOps workflow" -> docs/golden-paths/mlops-workflow.md
- "Architecture decision / why MLflow / why DVC / why three runtimes / why Evidently / why GitHub Actions / why Terraform / why Dev Container / why pre-commit" -> docs/decisions/
- "Local setup / dev container / GPU setup / CUDA / RTX / vLLM local / Triton local / Windows setup" -> docs/local-setup.md
- "Security scan / CVE / secrets scan / gitleaks" -> ci/github-actions/_shared/reusable-mlops-scan.yml
- "MLflow authentication / MLflow auth" -> mlflow/tracking-server/docker-compose.yml

## MLOps-Specific Routing - Newer Domains

- "Run batch inference" -> docs/golden-paths/batch-inference.md
- "Batch scoring" -> batch/README.md or pipelines/README.md
- "Batch quality check" -> batch/ or pipelines/
- "Batch job" -> cd/kubernetes/batch/ or cd/argo/pipelines/
- "Batch quality gate" -> policy/ and finops/
- "Create pipeline" -> docs/golden-paths/pipeline-orchestration.md
- "Pipeline workflow" -> pipelines/ or cd/argo/pipelines/
- "Pipeline runner" -> pipelines/README.md
- "Pipeline component" -> pipelines/components/
- "Drift-triggered retraining" -> pipelines/ or ci/github-actions/pipelines/
- "Distributed training" -> docs/golden-paths/distributed-training.md
- "Ray training" -> training/ or cd/kubernetes/training/
- "Kubeflow training" -> training/ or cd/kubernetes/training/
- "Checkpoint management" -> training/ or cd/kubernetes/training/
- "Resource allocation" -> terraform/ray-cluster/ or cd/kubernetes/training/
- "Feature store" -> docs/guides/feature-store-patterns.md
- "Feature patterns" -> docs/guides/feature-store-patterns.md
- "Feast integration" -> feature-store/ or terraform/gcp-vertex-ai/
- "Feature versioning" -> feature-store/ or dvc/
- "Fairness evaluation" -> docs/golden-paths/fairness-and-explainability.md
- "Fairness metrics" -> fairness/ or ci/github-actions/fairness/
- "Bias analysis" -> fairness/ or ci/github-actions/fairness/
- "Explainability" -> fairness/ or ci/github-actions/fairness/
- "Fairness gate" -> policy/ and ci/github-actions/fairness/
- "Online learning" -> docs/golden-paths/online-learning.md
- "Online inference" -> online-learning/ or cd/kubernetes/batch/
- "Model update" -> online-learning/ or ci/github-actions/pipelines/
- "Model rollback" -> online-learning/ or ci/github-actions/pipelines/
- "Model validator" -> online-learning/ or ci/github-actions/pipelines/
- "Federated learning" -> docs/golden-paths/federated-learning.md
- "Federated training" -> federated-learning/ or ci/github-actions/federated/
- "Privacy-preserving" -> federated-learning/ or ci/github-actions/federated/
- "Distributed coordination" -> federated-learning/ or ci/github-actions/federated/
- "Federated evaluation" -> ci/github-actions/federated/
- "Multi-cloud serving" -> docs/golden-paths/multi-cloud-serving.md
- "Multi-cloud routing" -> multi-cloud-serving/ or cd/kubernetes/
- "Cloud-specific serving" -> multi-cloud-serving/ or serving/
- "Cloud routing config" -> multi-cloud-serving/router.py or cd/kubernetes/
- "Cloud health check" -> multi-cloud-serving/health_check.py
- "Model optimization" -> docs/golden-paths/model-optimization.md
- "Model pruning" -> model_optimization/pruning.py
- "Model quantization" -> model_optimization/quantisation.py
- "Model distillation" -> model_optimization/distillation/
- "Model benchmarking" -> model_optimization/benchmark.py

## Generic Platform Routing

- "Provision GPU cluster" -> terraform/gpu-cluster/
- "Provision Kubernetes cluster" -> cd/kubernetes/
- "Manage secrets" -> cd/kubernetes/secrets/
- "Configure OIDC federation" -> cd/kubernetes/oidc/
- "Enforce policy controls" -> policy/
- "Set up monitoring baseline" -> monitoring/
