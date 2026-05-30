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
- **Architecture Decision Records** — MLflow (ADR-001), DVC (ADR-002), three-runtime serving (ADR-003), Evidently drift monitoring (ADR-004), GitHub Actions CI (ADR-005), Terraform IaC (ADR-006), Dev Containers (ADR-007), three-gate model approval (ADR-008), pre-commit toolchain (ADR-009) in `docs/decisions/`.
- **MLOps Concepts Guide** — lifecycle-first concept reference with repository-linked examples in `docs/guides/concepts.md`.
- **Security hardening** — reusable CI security scan (pip-audit + gitleaks + model size check) in `ci/github-actions/_shared/`.
- **Local setup guide** — RTX 5070 GPU passthrough, Dev Container setup, vLLM/Triton local testing in `docs/local-setup.md`.
- `GETTING_STARTED.md` — Dev Container quickstart + 5-step first experiment walkthrough and ML lifecycle quick links.
- **Multi-environment promotion** — env overlays, staging/canary/production gates, approval workflows in `cd/kubernetes/promotion/` and `ci/github-actions/promotion/`. ADR-ML-010 through ADR-ML-015.
- **Fairness & Explainability** — Fairlearn bias metrics, SHAP global/local explanations, CI fairness gate in `fairness/` and `ci/github-actions/fairness/`.
- **ML Cost Attribution** — pod-level cost labelling, budget alerts, cross-cloud normalization, Grafana dashboard in `finops/` and `monitoring/dashboards/ml-cost-attribution.json`.
- **Distributed Training** — KubeRay (primary) and Kubeflow PyTorchJob/TFJob (secondary), spot node pools, checkpoint callback in `training/`, `cd/kubernetes/training/`, `terraform/ray-cluster/`. ADR-ML-016.
- **Batch Inference** — MLflow pyfunc scorer, input validation, output quality gate, downstream notifier, K8s Job + CronJob manifests in `batch/`, `cd/kubernetes/batch/`. ADR-ML-018.
- **Pipeline Orchestration** — Argo Workflows DAGs, reusable Python components, drift-triggered retraining pipeline, Vertex AI optional backend in `pipelines/`, `cd/argo/`, `ci/github-actions/pipelines/`, `terraform/vertex-pipelines/`. ADR-ML-017.
- **Website Markdown Browser Navigation** — in-app markdown link navigation with URL-based state (`?file=<path>`), repo-root fallback for markdown links, and browser back/forward support in `website/src/App.tsx` and `website/src/components/CodeViewer.tsx`.
- **Website Mobile Template Browser** — full-width mobile sidebar drawer with header/viewer reopen controls and auto-close on file selection in `website/src/App.tsx`, `website/src/components/Header.tsx`, and `website/src/components/Sidebar.tsx`.
- **Website SEO and Branding Assets** — favicon, Open Graph image, robots/sitemap, and metadata for GitHub Pages discoverability in `website/index.html` and `website/public/`.

## How Teams Use It

1. Start with MLOps golden paths.
2. Connect to platform prerequisites from `cicd-reference`.
3. Adopt default lifecycle tooling (MLflow, DVC, Evidently, Triton/vLLM).
4. Promote only approved models through documented gates.

## Boundary Contract

- Infrastructure and compute provisioning belong to the platform repository.
- ML lifecycle implementation and operational playbooks belong to this repository.
