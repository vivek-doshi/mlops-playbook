# MLOps Playbook

## The Integration Bridge

This repository and the platform repository are intentionally coupled through a documented dependency, not treated as isolated islands.

- Platform layer lives in the DevOps repository (`cicd-reference`): GPU cluster provisioning, Kubernetes base manifests, secrets management, OIDC federation, Kyverno policies, and observability stack.
- ML lifecycle layer lives in this repository: experiment tracking, data versioning, model registry, model serving infrastructure, and drift monitoring.

This repository consumes platform primitives from `cicd-reference` and focuses on ML-specific operational workflows on top of that foundation.

## Prerequisites

This repository assumes your platform layer is already provisioned.

The recommended platform foundation is: [cicd-reference](https://github.com/vivek-doshi/devops-playbook)

Specifically, you need:

- GPU cluster: `cicd-reference/docs/golden-paths/mlops-workflow.md`
- Secrets management: `cicd-reference/secrets/`
- Observability stack: `cicd-reference/observability/`

## What Stays in This Repository

Keep GPU cluster Terraform/Kubernetes patterns and platform-focused provisioning guidance in the platform repository where they belong. That work is legitimately owned by a DevOps/platform team:

- GPU node pool provisioning
- Cost controls via Infracost
- Kyverno FinOps label enforcement
- Devcontainer GPU setup

Boundary definition:

- Infrastructure and compute provisioning live in `cicd-reference`
- ML lifecycle tooling and practices live in this repository

## Governance Recommendation

Apply the same structural discipline from day one that makes the platform repository valuable:

- Engineering principles document
- Golden paths before templates
- Guardrails embedded directly in golden paths
- ADRs for major tool choices (`MLflow` vs `W&B`, `DVC` vs `LakeFS`, `Triton` vs `TorchServe`)

A common failure mode is turning MLOps repositories into a dumping ground for notebooks and ad hoc scripts. Keep an opinionated posture with clearly documented paths and ownership boundaries.

## Default Tooling Posture

Recommended defaults based on the current landscape:

- MLflow for experiment tracking and model registry (self-hosted, no vendor lock-in)
- DVC for data versioning
- Evidently for drift monitoring
- vLLM for LLM serving
- Triton for classical model serving

W&B can be added as an optional integration for teams with budget, but should not be the default dependency.

## Implementation Status

Completed baseline implementation in this repository:

- CI workflow templates for model training, evaluation, and deployment in `ci/github-actions/`
- DVC pipeline definition in `ci/dvc/dvc-pipeline.yml`
- Terraform starter configs in `terraform/aws-sagemaker/`, `terraform/gcp-vertex-ai/`, and `terraform/gpu-cluster/`
- MLflow tracking stack bootstrap in `mlflow/tracking-server/`
- DVC remote storage samples in `dvc/remote-storage/`
- Bootstrap scripts in `scripts/`
- Copilot guidance in `.github/copilot-instructions.md`
- Repository intelligence updates in `.ai/` including a new skill: `senior-mlops-architect`
