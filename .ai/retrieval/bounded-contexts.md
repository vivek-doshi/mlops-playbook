# Bounded Contexts

Repository contexts and their boundaries for retrieval and change planning.

## Core Contexts

- Experiment And Data Context
  - Scope: mlflow/, dvc/, feature-store/
  - Concern: experiment lineage, model artifacts, data versioning, and features
- CI Context
  - Scope: ci/github-actions/
  - Concern: training, evaluation, security scanning, promotion, and deployment automation
- Delivery Context
  - Scope: cd/kubernetes/, cd/argo/, serving/
  - Concern: model serving, deployment orchestration, and pipeline execution
- Infrastructure Context
  - Scope: terraform/
  - Concern: cloud-specific ML infrastructure provisioning
- Governance Context
  - Scope: policy/, fairness/
  - Concern: model approval, data governance, and fairness evaluation
- Monitoring Context
  - Scope: monitoring/, docs/runbooks/
  - Concern: drift detection, serving SLOs, alerts, and operational response
- FinOps Context
  - Scope: finops/
  - Concern: spend visibility, cost governance, optimization
- Documentation Context
  - Scope: docs/, docs/runbooks/, docs/golden-paths/, docs/decisions/
  - Concern: decision support and operational knowledge

## External Platform Context

`devops-playbook` provides cluster provisioning, secrets, OIDC, cluster observability, and notification integrations. Retrieve its published interfaces only when a task crosses the Integration Bridge.

## Boundary Rules

- Changes should remain in one primary context unless integration is required.
- Cross-context tasks must include integration files and validation steps.
- Guardrail contexts (security, policy, finops) are mandatory companions for production-impacting changes.
