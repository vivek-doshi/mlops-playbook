# Pipeline Orchestration — Golden Path

This guide walks you from zero to a running end-to-end ML pipeline.

## Prerequisites

| Tool | Min Version | Notes |
|------|-------------|-------|
| Python | 3.11 | `python --version` |
| MLflow | 2.11 | `mlflow --version` |
| kubectl | 1.28 | For Kubernetes runs |
| Argo CLI | 3.5 | For Argo workflow submission |
| gh CLI | 2.40 | For GitHub Actions triggers |

---

## Step 1 — Create a pipeline config

```bash
cp pipelines/config/my-model.yaml pipelines/config/<your-model>.yaml
```

Minimum required keys:

```yaml
source_uri: s3://my-bucket/raw/data.parquet

label_column: is_fraud
test_size: 0.1
val_size: 0.1
scale_features: true

model_type: random_forest
model_name: my-model
experiment_name: my-model-dev
mlflow_tracking_uri: http://mlflow:5000

registration_thresholds:
  test_f1: 0.88
  test_auc: 0.92
```

---

## Step 2 — Validate locally

```bash
# Lint config
python -c "import yaml; yaml.safe_load(open('pipelines/config/<your-model>.yaml'))"

# Run full pipeline locally (uses tmpdir for artifacts)
python pipelines/training_pipeline.py \
  --config-file pipelines/config/<your-model>.yaml \
  --mode local
```

---

## Step 3 — Run via GitHub Actions (staging)

```bash
gh workflow run trigger-training-pipeline.yml \
  -f model_name=<your-model> \
  -f config_path=pipelines/config/<your-model>.yaml \
  -f environment=staging
```

Watch the run:

```bash
gh run watch
```

---

## Step 4 — Run via Argo Workflows (production)

```bash
# Submit workflow
argo submit cd/argo/pipelines/training-workflow.yaml \
  -n mlops \
  -p model_name=<your-model> \
  -p config_path=pipelines/config/<your-model>.yaml \
  -p environment=production

# Watch progress
argo watch <workflow-name> -n mlops

# View logs
argo logs <workflow-name> -n mlops
```

---

## Step 5 — Verify in MLflow

```bash
# List runs in experiment
mlflow experiments list
mlflow runs list --experiment-name <your-model>-dev

# Confirm model in Staging
python -c "
import mlflow
from mlflow.tracking import MlflowClient
client = MlflowClient()
for v in client.get_latest_versions('<your-model>', stages=['Staging']):
    print(f'Version {v.version} — {v.status}')
"
```

---

## Step 6 — Promote to Production (manual gate)

```bash
gh workflow run trigger-training-pipeline.yml \
  -f model_name=<your-model> \
  -f environment=production
```

Or via MLflow:

```bash
python -c "
from mlflow.tracking import MlflowClient
client = MlflowClient()
client.transition_model_version_stage('<your-model>', version='<ver>', stage='Production', archive_existing_versions=True)
print('Promoted to Production.')
"
```

---

## Step 7 — Enable Drift-Triggered Retraining

```bash
# Add retraining config to your model YAML:
# retraining:
#   drift_threshold: 0.10

# Run retraining pipeline (manual)
python pipelines/retraining_pipeline.py \
  --config-file pipelines/config/<your-model>.yaml \
  --drift-report monitoring/evidently/latest_drift_report.json
```

---

## Component Summary

| Component | Input | Output |
|-----------|-------|--------|
| `data_ingestion` | `source_uri` | `raw.parquet` |
| `preprocessing` | `raw.parquet` | `train/val/test.parquet` |
| `training` | `train/val.parquet` | `run_id.txt` |
| `evaluation` | `run_id.txt`, `test.parquet` | `metrics.json` |
| `registration` | `run_id.txt`, `metrics.json` | Model in Staging |
| `deployment` | Config | Model in Production + k8s rollout |

---

## Execution Backend Selection

| Scenario | Backend |
|----------|---------|
| Local development | `--mode local` |
| CI checks | GitHub Actions (`trigger-training-pipeline.yml`) |
| Production training | Argo Workflows (`training-workflow.yaml`) |
| Cloud-native (GCP) | Vertex AI Pipelines (`terraform/vertex-pipelines/`) |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `registration_thresholds not met` | Model underperforms | Check eval metrics; lower threshold or retune model |
| `No Staging version found` | Registration step failed | Inspect MLflow experiment; check threshold config |
| Argo workflow stuck in `Pending` | Insufficient cluster resources | Scale node pool or reduce resource requests |
| `source_uri` not accessible | Missing S3/GCS credentials | Ensure IAM role or secret is configured on the pod |
| `mlflow.exceptions.MlflowException` | Wrong tracking URI | Set `mlflow_tracking_uri` in config |

---

## Related Resources

- [ADR-ML-017 — Pipeline Orchestration](../decisions/ADR-ML-017-pipeline-orchestration.md)
- [Batch Inference Golden Path](batch-inference.md)
- [Distributed Training Golden Path](distributed-training.md)
- [Experiment Tracking Golden Path](experiment-tracking.md)
