# Continuous Integration (CI)

## What this folder does

This folder defines automated validation and delivery checks for the MLOps lifecycle.
It contains workflow templates for model training, evaluation, promotion gates, security scanning, and domain-specific tracks such as fairness, federated learning, and LLMOps.

## Folder description and details

- `github-actions/`: GitHub Actions workflows grouped by capability.
  - `model-training/`, `model-evaluation/`, `model-deployment/`, `model-monitoring/`
  - `batch/`, `pipelines/`, `promotion/`
  - `fairness/`, `federated/`, `llmops/`, `online-learning/`, `multi-cloud/`, `finops/`
  - `_shared/`: reusable CI building blocks.
- `dvc/`: pipeline-oriented CI integration examples for data/model versioning.
- `azure-ml/`: Azure ML job-based CI examples.

## How to use this as an individual component

1. Pick a workflow relevant to your lifecycle stage (for example, `ci/github-actions/model-training/train.yml`).
2. Add required repository secrets and variables in GitHub.
3. Trigger the workflow:
   - Push/PR trigger if configured in the file.
   - Manual trigger with `workflow_dispatch` from the Actions tab.
4. Reuse shared checks by referencing workflows in `ci/github-actions/_shared/`.
5. Gate promotion using workflows in `ci/github-actions/promotion/`.

## Inputs and outputs

- Inputs: code changes, model/data artifacts, environment variables, cloud credentials.
- Outputs: build/test results, model quality reports, promotion decisions, and deployment triggers.
