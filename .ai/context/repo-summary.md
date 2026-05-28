# Repository Summary

## What This Repository Fundamentally Is

This repository is a production-oriented MLOps playbook.
It provides reusable patterns, templates, and guardrails for experiment tracking, data versioning, model registry promotion, model serving, and model monitoring.

## The Integration Bridge

The two repos are not islands. You create a deliberate, documented dependency.

- Platform layer is consumed from `cicd-reference`: GPU cluster provisioning, base Kubernetes primitives, secrets management, OIDC federation, policy controls, and observability baseline.
- ML lifecycle layer is implemented here: tracking, lineage, registry, serving patterns, and drift monitoring.

## Core Capabilities In This Repository

- MLOps golden paths in `docs/golden-paths/`.
- CI workflow templates for train, evaluate, and deploy in `ci/github-actions/`.
- Terraform starter configurations for SageMaker, Vertex AI, and GPU cluster integration in `terraform/`.
- MLflow local tracking stack bootstrap in `mlflow/tracking-server/`.
- DVC remote storage patterns and pipeline templates in `dvc/`.
- Serving topology placeholders in `serving/` for Triton, TorchServe, and vLLM.
- Monitoring and policy boundaries in `monitoring/` and `policy/`.

## How Teams Use It

1. Start with MLOps golden paths.
2. Connect to platform prerequisites from `cicd-reference`.
3. Adopt default lifecycle tooling (MLflow, DVC, Evidently, Triton/vLLM).
4. Promote only approved models through documented gates.

## Boundary Contract

- Infrastructure and compute provisioning belong to the platform repository.
- ML lifecycle implementation and operational playbooks belong to this repository.
