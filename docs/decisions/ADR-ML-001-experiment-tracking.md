# ADR-ML-001: MLflow as the Experiment Tracking Platform

**Status:** Accepted  
**Date:** 2024-06-01  
**Authors:** ML Platform Team  
**Reviewers:** @ml-approvers

---

## Context

The team needed a system to track machine learning experiments, including:

- Hyperparameter values for every training run.
- Metrics (accuracy, loss, F1, AUC) over time.
- Artifacts (model binaries, plots, evaluation reports).
- A model registry that tracks Staging / Production stage transitions.

Without a tracking platform, experiments are tracked manually in spreadsheets or
notebooks, which makes reproducibility and auditability nearly impossible.

---

## Decision

We will use **MLflow** (self-hosted, version ≥ 2.14) as the experiment tracking and
model registry platform.

The deployment stack is:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| MLflow server | Docker container | UI + REST API |
| Backend store | PostgreSQL | Metadata (runs, params, metrics, tags) |
| Artifact store | MinIO (S3-compatible) | Model binaries, plots, reports |

Configuration: `mlflow/tracking-server/docker-compose.yml`

---

## Alternatives Considered

### Weights & Biases (W&B)
- **Pros:** Polished UI, built-in collaboration features, sweep automation.
- **Cons:** SaaS product (vendor lock-in), data leaves our infrastructure, cost
  scales with seats and usage, not suitable for on-prem regulated workloads.

### Neptune.ai
- **Pros:** Good metadata management, team-oriented features.
- **Cons:** Same SaaS concerns as W&B. Self-hosted option adds operational burden
  without significant benefit over MLflow.

### Comet ML
- **Pros:** Reproducibility panel, production monitoring integration.
- **Cons:** SaaS, pricing model tied to runs volume.

### Custom solution (plain files + Git)
- **Pros:** Zero dependencies.
- **Cons:** No UI, no querying across runs, no model registry, no artifact management.
  Maintenance burden grows with team size.

---

## Why MLflow Won

1. **Open source and self-hostable.** Data stays in our infrastructure.
   Critical for GDPR and internal data governance policies.

2. **MLflow Model Registry.** Stage-based lifecycle (None → Staging → Production → Archived)
   maps directly to our approval gate workflow.

3. **Framework agnostic.** Works with scikit-learn, PyTorch, TensorFlow, Hugging Face,
   and custom Python models through the `pyfunc` interface.

4. **DVC integration.** We can log the DVC data hash as an MLflow run tag, giving us
   end-to-end lineage from data version to deployed model.

5. **REST API.** The `mlflow.tracking.MlflowClient` API allows CI pipelines to
   programmatically promote models and check stages without manual UI interaction.

6. **Community and ecosystem.** Large community, maintained by Databricks, widely
   used in the industry — reduces risk of abandonment.

---

## Consequences

### Positive
- Full control over data residency.
- Reproducible experiments via MLflow run IDs linked to DVC hashes.
- Automated promotion gates enforced in `ci/github-actions/model-evaluation/evaluate.yml`.

### Negative / Trade-offs
- We are responsible for operating the MLflow server (upgrades, backups, HA).
- The self-hosted UI is functional but less polished than W&B.
- Collaborative features (annotations, team comments) require manual process.

### Operational notes
- PostgreSQL database must be backed up daily. Configure backup in `devops-playbook`.
- MinIO data must be included in the disaster recovery plan.
- See `mlflow/tracking-server/README.md` for local development setup.

---

## Related

- `mlflow/tracking-server/docker-compose.yml`
- `docs/golden-paths/experiment-tracking.md`
- ADR-ML-002-data-versioning.md
