# CI - Continuous Integration for MLOps

## Purpose and Scope

This folder contains automated validation and delivery checks for the MLOps lifecycle, including:

- **Model Training**: CI workflows for training pipelines
- **Model Evaluation**: Quality gates and evaluation checks
- **Model Deployment**: Promotion workflows and deployment triggers
- **Model Monitoring**: Drift detection and operational checks
- **Domain-Specific Tracks**: Fairness, federated learning, LLMOps, online learning, multi-cloud, and FinOps

## Folder Structure

- `github-actions/`: GitHub Actions workflows grouped by capability
  - `model-training/`: Training pipeline workflows
  - `model-evaluation/`: Quality gate workflows
  - `model-deployment/`: Promotion and deployment workflows
  - `model-monitoring/`: Drift detection and operational checks
  - `batch/`: Batch inference validation
  - `pipelines/`: Pipeline orchestration workflows
  - `promotion/`: Promotion gate workflows
  - `fairness/`: Fairness evaluation workflows
  - `federated/`: Federated learning workflows
  - `llmops/`: LLMOps-specific workflows
  - `online-learning/`: Online learning workflows
  - `multi-cloud/`: Multi-cloud serving workflows
  - `finops/`: FinOps monitoring workflows
  - `_shared/`: Reusable CI building blocks

- `dvc/`: Pipeline-oriented CI integration examples for data/model versioning
- `azure-ml/`: Azure ML job-based CI examples

## How to Use This as an Individual Component

1. **Pick a workflow relevant to your lifecycle stage** (for example, `ci/github-actions/model-training/train.yml`)
2. **Add required repository secrets and variables in GitHub**
3. **Trigger the workflow**:
   - Push/PR trigger if configured in the file
   - Manual trigger with `workflow_dispatch` from the Actions tab
4. **Reuse shared checks by referencing workflows in `ci/github-actions/_shared/`**
5. **Gate promotion using workflows in `ci/github-actions/promotion/`**

## Inputs and Outputs

- **Inputs**: Code changes, model/data artifacts, environment variables, cloud credentials
- **Outputs**: Build/test results, model quality reports, promotion decisions, and deployment triggers

## Related Resources

- Golden paths: See [docs/golden-paths/](../docs/golden-paths/)
- CI workflows: See [ci/github-actions/](github-actions/)
- CD workflows: See [cd/argo/pipelines/](../cd/argo/pipelines/)
