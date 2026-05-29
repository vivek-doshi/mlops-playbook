# Pipelines

End-to-end ML pipeline orchestration for the MLOps Playbook.

## Structure

```
pipelines/
├── training_pipeline.py          # Ingest → preprocess → train → evaluate → register
├── batch_inference_pipeline.py   # Ingest → score → quality-gate → notify
├── retraining_pipeline.py        # Drift-triggered conditional retraining
├── components/
│   ├── data_ingestion/component.py   # Step 1 — raw data download + schema check
│   ├── preprocessing/component.py   # Step 2 — feature engineering + splits
│   ├── training/component.py         # Step 3 — train + MLflow logging
│   ├── evaluation/component.py       # Step 4 — test-split metrics
│   ├── registration/component.py     # Step 5 — threshold gate + promote to Staging
│   └── deployment/component.py       # Step 6 — promote to Production + k8s rollout
└── config/
    └── <model-name>.yaml             # Per-model pipeline config (see template below)
```

## Quick Start

### Local training pipeline

```bash
python pipelines/training_pipeline.py \
  --config-file pipelines/config/fraud-detection.yaml \
  --mode local
```

### Trigger via GitHub Actions

```bash
gh workflow run trigger-training-pipeline.yml \
  -f model_name=fraud-detection \
  -f config_path=pipelines/config/fraud-detection.yaml \
  -f environment=staging
```

### Local batch inference pipeline

```bash
python pipelines/batch_inference_pipeline.py \
  --job-config batch/jobs/fraud-detection-production-batch-job.yaml
```

### Drift-triggered retraining

```bash
python pipelines/retraining_pipeline.py \
  --config-file pipelines/config/fraud-detection.yaml \
  --drift-report monitoring/evidently/latest_drift_report.json
```

## Pipeline Config Template

Create `pipelines/config/<model-name>.yaml`:

```yaml
# Data source
source_uri: s3://my-bucket/raw/fraud-features.parquet

# Ingestion options
ingestion:
  format: parquet

# Preprocessing
label_column: is_fraud
test_size: 0.1
val_size: 0.1
scale_features: true
drop_columns: [id, timestamp]
fill_strategy: median

# Training
model_type: random_forest           # random_forest | gradient_boosting | logistic_regression
model_name: fraud-detection
experiment_name: fraud-detection-dev
mlflow_tracking_uri: http://mlflow:5000
model_params:
  n_estimators: 200
  max_depth: 8

# Registration gates
registration_thresholds:
  test_f1: 0.90
  test_auc: 0.95

# Optional: Kubernetes rollout on promotion
kubernetes_deployment:
  namespace: fraud-detection-production
  name: fraud-detection-serving
  image_template: "my-registry/fraud-detection-serving:{version}"

# Retraining
retraining:
  drift_threshold: 0.10
```

## Execution Backends

| Mode | Command | Best For |
|------|---------|----------|
| Local | `--mode local` | Development and debugging |
| Argo Workflows | `cd/argo/pipelines/training-workflow.yaml` | Production Kubernetes runs |
| GitHub Actions | `ci/github-actions/pipelines/` | CI-triggered runs |

## Adding a Component

1. Create `pipelines/components/<name>/component.py` following the pattern:
   - Module docstring with Purpose, Usage, Dependencies
   - A `def <action>(args…) -> dict` function
   - CLI wrapper via `argparse`
2. Add the component to the relevant pipeline file.
3. Add a step to `cd/argo/pipelines/training-workflow.yaml`.
4. Update this README.

## Related Docs

- [Pipeline Orchestration Golden Path](../docs/golden-paths/pipeline-orchestration.md)
- [ADR-ML-017 — Pipeline Orchestration](../docs/decisions/ADR-ML-017-pipeline-orchestration.md)
- [Batch Inference](../batch/README.md)
