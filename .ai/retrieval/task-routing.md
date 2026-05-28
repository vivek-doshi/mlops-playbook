# Task Routing

Routes user intent to the minimum correct repository domain.

## Primary Routing

- "Containerize app" -> docker/ and compose/.
- "Set up CI" -> ci/<platform>/ and ci/.../_shared.
- "Deploy to cloud" -> cd/targets/<cloud>/ and terraform/<cloud-target>/.
- "Deploy to Kubernetes" -> cd/kubernetes/, cd/helm/, cd/gitops/.
- "Provision infrastructure" -> terraform/ (or cd/pulumi/ when explicitly requested).
- "Add security checks" -> security/ and policy/.
- "Incident response" -> secops/runbooks/ and docs/runbooks/.
- "Observability and alerting" -> observability/ and notifications/.
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
- "Architecture decision / why MLflow / why DVC / why three runtimes" -> docs/decisions/
- "Security scan / CVE / secrets scan / gitleaks" -> ci/github-actions/_shared/reusable-mlops-scan.yml
- "MLflow authentication / MLflow auth" -> mlflow/tracking-server/docker-compose.yml

## Secondary Routing

- If request is architecture/choice oriented -> docs/ARCHITECTURE_DECISION_GUIDE.md first, then docs/decisions/.
- If request asks "where do I start" -> GETTING_STARTED.md first, then docs/golden-paths/.
- If request mixes domains (for example CI + Terraform + security), route to:
  1. golden path
  2. target domain files
  3. enforcement files (security/policy/finops)

## Conflict Resolution

When multiple valid routes exist:

1. Prefer simpler golden path.
2. Prefer production-grade templates over demo examples.
3. Prefer reusable/shared templates.
4. Prefer cloud target explicitly named by the user.
5. If no cloud named, default to cloud-agnostic guidance and list supported targets.
