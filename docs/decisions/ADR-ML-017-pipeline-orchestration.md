# ADR-ML-017 — Pipeline Orchestration

**Status:** Accepted  
**Date:** 2025-01-01  
**Deciders:** ML Platform, MLOps, Infra  
**Hard Merge Gate:** PRs that introduce a new pipeline or change orchestration backend MUST link to this ADR.

---

## Context

The MLOps Playbook needs a single, consistent way to chain ML pipeline steps (ingest → preprocess → train → evaluate → register → deploy) across local development, CI, and production Kubernetes clusters.  Key requirements:

1. Steps must be independently testable and reusable across pipelines.
2. Artifact passing between steps must be explicit and auditable.
3. Both training and batch inference pipelines must use the same component model.
4. The solution must support local execution (fast iteration) and cluster execution (production scale).
5. Cost attribution labels must be present on all workloads.

---

## Decision

### Primary backend: Argo Workflows on Kubernetes

Argo Workflows is adopted as the production pipeline execution engine because:

- Native Kubernetes CRD — no external service to manage.
- DAG and steps templates match the component chain model.
- PVC-based artifact passing is simple and transparent.
- Existing KubeRay and batch jobs already run in the same cluster.
- Open-source with active community.

### Secondary backend: GitHub Actions (CI and lightweight runs)

GitHub Actions workflows (`ci/github-actions/pipelines/`) wrap Argo submissions for CI-triggered runs.  For small models where the full cluster round-trip is unnecessary, the `--mode local` path runs all components in-process.

### Optional cloud backend: Vertex AI Pipelines (GCP)

`terraform/vertex-pipelines/` provisions the minimum GCP resources needed to submit Kubeflow Pipelines (KFP) to Vertex AI.  Teams on GCP may use this instead of Argo; the component interface is identical.

### Component model

Each pipeline step lives in `pipelines/components/<name>/component.py` and exposes:
- A pure-Python function (`ingest`, `preprocess`, `train`, `evaluate`, `register`, `deploy`)
- A CLI wrapper via `argparse` for container invocation

Artifact passing uses files on a shared PVC (`/workspace/`).

### Pipelines

| Pipeline | File | Trigger |
|----------|------|---------|
| Training | `pipelines/training_pipeline.py` | Manual, CI, drift |
| Batch inference | `pipelines/batch_inference_pipeline.py` | Scheduled, manual |
| Retraining | `pipelines/retraining_pipeline.py` | Drift report |

---

## Alternatives Considered

| Option | Reason Not Adopted |
|--------|-------------------|
| Kubeflow Pipelines (standalone) | Higher operational overhead than Argo for our cluster scale |
| Prefect / Airflow | Introduces a new scheduler daemon; Argo already available |
| MLflow Projects | Limited DAG support; no native K8s artifact handling |
| Vertex AI Pipelines (primary) | GCP-only; conflicts with multi-cloud strategy |
| SageMaker Pipelines | AWS-only |

---

## Consequences

### Positive

- All pipelines share the same component interface — a step moved between pipelines needs no rewrite.
- Local `--mode local` drastically reduces iteration time during development.
- Argo's native Kubernetes integration means pipeline pods inherit all existing cluster policies (cost labels, security context, spot scheduling).

### Negative / Trade-offs

- Teams must learn Argo Workflows YAML syntax.
- Shared PVC creates a bottleneck for very large artifacts — teams scoring >500 GB should use cloud object storage and pass URIs.
- Vertex AI path requires additional GCP IAM configuration.

---

## Compliance Requirements

- All Argo workflow pods MUST carry the four cost attribution labels: `cost-center`, `team`, `model-name`, `environment`.
- All pods MUST run as non-root (`runAsUser: 1000`, `allowPrivilegeEscalation: false`).
- Pipelines MUST NOT skip the registration threshold gate.
- Every new pipeline MUST be documented in `docs/golden-paths/pipeline-orchestration.md`.
