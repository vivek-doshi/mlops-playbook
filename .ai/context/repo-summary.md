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
- CI workflow templates for train, evaluate, deploy, and drift monitoring in `ci/github-actions/`.
- Terraform starter configurations for SageMaker, Vertex AI, and GPU cluster integration in `terraform/`.
- MLflow local tracking stack bootstrap in `mlflow/tracking-server/`.
- DVC remote storage patterns and pipeline templates in `dvc/`.
- **Serving infrastructure** — production-ready configs for Triton, TorchServe, and vLLM in `serving/`.
- **Drift monitoring** — Evidently AI scripts, Prometheus alert rules, and Grafana dashboard in `monitoring/`.
- **Model approval policy** — three-gate CI evaluation + approval registry in `policy/model-approval/`.
- **Data governance policy** — classification levels, PII handling rules, retention, and PII checklist in `policy/data-governance/`.
- **Architecture Decision Records** — MLflow (ADR-001), DVC (ADR-002), three-runtime serving (ADR-003) in `docs/decisions/`.
- **Security hardening** — reusable CI security scan (pip-audit + gitleaks + model size check) in `ci/github-actions/_shared/`.
- `GETTING_STARTED.md` — 5-step first experiment walkthrough and ML lifecycle quick links.

## How Teams Use It

1. Start with MLOps golden paths.
2. Connect to platform prerequisites from `cicd-reference`.
3. Adopt default lifecycle tooling (MLflow, DVC, Evidently, Triton/vLLM).
4. Promote only approved models through documented gates.

## Boundary Contract

- Infrastructure and compute provisioning belong to the platform repository.
- ML lifecycle implementation and operational playbooks belong to this repository.
