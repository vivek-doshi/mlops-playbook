# Task Routing

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

## Secondary Routing

- If request is architecture/choice oriented -> docs/golden-paths/mlops-workflow.md first, then docs/decisions/.
- If request asks "where do I start" -> GETTING_STARTED.md first, then docs/golden-paths/.
- If request mixes domains (for example CI + Terraform + security), route to:
  1. golden path
  2. target domain files
  3. enforcement files (policy/monitoring/finops)

## Conflict Resolution

When multiple valid routes exist:

1. Prefer simpler golden path.
2. Prefer production-grade templates over demo examples.
3. Prefer reusable/shared templates.
4. Prefer cloud target explicitly named by the user.
5. If no cloud named, default to cloud-agnostic guidance and list supported targets.
