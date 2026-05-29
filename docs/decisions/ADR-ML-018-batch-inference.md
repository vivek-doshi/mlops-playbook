# ADR-ML-018: Batch Inference Architecture

**Status**: Accepted  
**Date**: 2026-01-01  
**Deciders**: ML Platform Team  
**Category**: Hard Merge Gate — required before any batch inference PR merges  

---

## Context

Real-time inference (ADR-ML-003) covers low-latency predictions. A separate pattern is
needed for offline/batch workloads — scoring millions of rows asynchronously, typically
on a schedule (nightly, weekly) or triggered by a data pipeline.

Requirements:
1. Score large datasets (tens of millions of rows) without impacting serving latency.
2. Integrate with existing MLflow model registry.
3. Enforce input validation and output quality gates before downstream consumers receive predictions.
4. Attribute costs via pod labels (finops workstream).
5. Notify downstream systems on completion or failure.

---

## Decision

### Runner: Python scripts on Kubernetes Jobs/CronJobs

Batch scoring runs as a **Kubernetes Job** (one-shot) or **CronJob** (scheduled).
The runner is a set of Python scripts (`batch/runner/`) invoked in sequence:

```
input_validator  →  batch_scorer  →  output_quality_gate  →  downstream_notifier
```

Rationale for Kubernetes Jobs over managed services (Vertex AI Batch, SageMaker Transform):
- Uses the same cluster as training and serving — no additional infrastructure.
- No per-job managed-service cost overhead.
- Custom quality gates are straightforward to add as Python scripts.
- Output can be written to any storage backend (S3, GCS, Azure Blob).

### Model loading: MLflow `pyfunc`

All models are loaded via `mlflow.pyfunc.load_model(uri)`.  This decouples the
batch runner from the model framework (scikit-learn, PyTorch, TF, XGBoost, etc.).

### Chunk-based scoring

Input data is loaded fully into memory, then scored in configurable chunks
(`chunk_size`, default 10,000 rows) to limit peak memory usage.

For very large datasets (> 100M rows), the recommended pattern is to pre-split
input files and submit one Job per partition. This is documented in
`docs/golden-paths/batch-inference.md`.

### Quality gates

Two mandatory gates before any predictions reach downstream consumers:

1. **Input gate** (`input_validator.py`): schema, null rates, value ranges.
2. **Output gate** (`output_quality_gate.py`): prediction coverage, class distribution,
   score distribution statistics.

CI exits 1 if either gate fails, blocking the promotion.

---

## Not adopted

| Alternative | Reason rejected |
|---|---|
| Spark batch (on k8s) | Adds significant complexity; Python ecosystem sufficient for current scale |
| Ray Data | Adds Ray dependency to batch path; overkill for current requirements |
| Vertex AI Batch Prediction | Vendor lock-in; adds managed-service cost |
| SageMaker Transform | AWS-only; contradicts cloud-agnostic strategy (ADR-ML-006) |

---

## Consequences

### Positive
- Simple, debuggable Python scripts — no distributed system complexity.
- Kubernetes Jobs integrate with existing monitoring (Prometheus, kube-state-metrics).
- `mlflow.pyfunc` means zero code changes when the model framework changes.
- Quality gates catch silent model failures before downstream impact.

### Negative
- Not suitable for datasets that don't fit in memory; requires pre-splitting.
- No streaming; all-or-nothing per batch run.
- Chunk-based scoring is sequential; parallelism requires multiple Jobs.

---

## Related Decisions

- ADR-ML-003: Real-time model serving.
- ADR-ML-006: Terraform for infrastructure — `cd/kubernetes/batch/` manifests managed here.
- ADR-ML-009: Pre-commit toolchain — `batch/*.py` must pass Black/Ruff/Bandit.
- Finops workstream: Pod labels required on all batch Jobs.
