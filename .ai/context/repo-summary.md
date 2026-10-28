# Repository Summary

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-10-28
**Source of Truth**: docs/golden-paths/
**Depends On**: docs/guides/, docs/decisions/
---

## What This Repository Is

This is a production-oriented MLOps playbook: opinionated golden paths, reusable implementation patterns, and operational guardrails for the machine-learning lifecycle. It is the lifecycle layer built on the shared platform capabilities supplied by `devops-playbook`.

## Responsibility Boundary

- `devops-playbook` supplies shared platform capabilities such as cluster provisioning, identity, secrets, and baseline observability.
- This repository implements ML lifecycle workflows and their operational controls.
- Cross-repository requirements are documented in `docs/topology/`; see the integration bridge and compatibility contract before changing that boundary.

## Capability Map

- **Core lifecycle**: MLflow tracking and registry (`mlflow/`), DVC data versioning (`dvc/`), training (`training/`), and reusable workflows (`pipelines/`).
- **Evaluation and governance**: model approval, data governance, fairness, and explainability (`policy/`, `fairness/`).
- **Delivery**: runtime patterns (`serving/`), Kubernetes and Argo workflows (`cd/`), and cloud-specific infrastructure examples (`terraform/`).
- **Operations**: drift detection, alerts, and SLOs (`monitoring/`); cost attribution and budgets (`finops/`); batch inference (`batch/`).
- **Advanced lifecycle patterns**: feature stores (`feature-store/`), online learning (`online_learning/`), federated learning (`federated_learning/`), multi-cloud serving (`multi_cloud_serving/`), model optimization (`model_optimization/`), LLMOps (`llmops/`), and self-service operations (`portal/`).
- **Guidance and decisions**: lifecycle walkthroughs (`docs/golden-paths/`), concepts (`docs/guides/`), architecture decisions (`docs/decisions/`), and platform integration (`docs/topology/`).
- **Presentation surface**: the generated template browser in `website/` mirrors the repository's top-level directories and is deployed through `.github/workflows/deploy-website.yml`.
- **Production hardening**: release safety, model inventory, lineage, observability, supply chain, and recovery acceptance criteria are defined under `docs/` and `policy/`.
- **Platform compatibility**: `docs/topology/platform-manifest.yaml` is the copy-ready manifest contract for the external `devops-playbook` repository.

## How Teams Use It

1. Select the matching workflow in `docs/golden-paths/`.
2. Satisfy its documented platform prerequisites from `devops-playbook`.
3. Adapt the relevant templates and domain examples.
4. Enforce evaluation, approval, security, and operational guardrails before promotion.
