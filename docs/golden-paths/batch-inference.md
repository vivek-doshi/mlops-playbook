# Batch Inference Golden Path

## Purpose and Scope

This guide walks you through running offline/batch inference on Kubernetes using the
MLOps Playbook batch pipeline. Follow these steps in order.

> **Beginner tip**: Batch inference is for scoring large datasets offline (millions of
> rows). It's separate from real-time serving (vLLM/Triton). Use batch when you don't
> need predictions in under a second.

---

## Prerequisites

| Requirement | How to verify |
|---|---|
| Kubernetes cluster accessible | `kubectl cluster-info` |
| MLflow model in `Production` or `Staging` stage | MLflow UI → Models |
| Budget file exists | `ls finops/budgets/<model-name>.yaml` |
| Batch scorer image built | `docker pull ghcr.io/<org>/batch-scorer:latest` |

---

## Step 1: Create a Job Config

Copy the schema template and fill in your values:

```bash
cp batch/jobs/_job-schema.yaml \
   batch/jobs/<model-name>-<environment>-batch-job.yaml
```

Minimum required fields:

```yaml
job_name:    fraud-detection-production-2024-01-15
namespace:   fraud-detection-production
environment: production
model:
  name:  fraud-detection
  stage: Production
input:
  path:   s3://my-bucket/input/data.parquet
  format: parquet
output:
  path:   s3://my-bucket/output/predictions.parquet
  format: parquet
labels:
  cost-center:  cc-1234
  team:         ml-platform
  model-name:   fraud-detection
  environment:  production
```

---

## Step 2: Validate Locally (Optional)

```bash
pip install mlflow pandas pyarrow pyyaml

# Validate input data.
python batch/runner/input_validator.py \
  --job-config batch/jobs/<model-name>-<env>-batch-job.yaml

# Run scoring locally.
python batch/runner/batch_scorer.py \
  --job-config batch/jobs/<model-name>-<env>-batch-job.yaml

# Check output quality.
python batch/runner/output_quality_gate.py \
  --job-config batch/jobs/<model-name>-<env>-batch-job.yaml \
  --predictions-path /tmp/predictions.parquet
```

---

## Step 3: Submit via GitHub Actions

### One-shot job

```bash
gh workflow run trigger-batch-job \
  --field model_name=fraud-detection \
  --field environment=production \
  --field job_config=batch/jobs/fraud-detection-production-batch-job.yaml
```

### Scheduled job

Update `ci/github-actions/batch/scheduled-batch.yml`:

```yaml
env:
  MODEL_NAME:  fraud-detection
  ENVIRONMENT: production
  JOB_CONFIG:  batch/jobs/fraud-detection-production-batch-job.yaml
  IMAGE_TAG:   v1.2.3

on:
  schedule:
    - cron: "0 2 * * *"   # daily at 02:00 UTC
```

---

## Step 4: Monitor

Watch job status:

```bash
kubectl get jobs -n fraud-detection-production -w
```

Tail logs:

```bash
kubectl logs -n fraud-detection-production \
  -l app=batch-inference -f
```

Check Prometheus alerts: see `monitoring/batch/batch-alerts.yaml`.

---

## Step 5: Check Output Quality

The pipeline runs the quality gate automatically. Key checks:

| Check | What it catches |
|---|---|
| Prediction coverage | > 0.1% null predictions |
| Dominant class guard | All predictions are one class (degenerate model) |
| Score distribution | Mean or std outside expected range |

---

## Cost Attribution

Every batch job must have these four pod labels in the job config:

| Label | Example |
|---|---|
| `cost-center` | `cc-1234` |
| `team` | `ml-platform` |
| `model-name` | `fraud-detection` |
| `environment` | `production` |

Without these labels, the job cost will appear as "untagged" in weekly reports and
may trigger a governance alert.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Job stuck in `Pending` | No nodes with matching resources | `kubectl describe pod ...` → check affinity/resources |
| `mlflow.exceptions.MlflowException: Run ... not found` | Wrong model name or stage | Check MLflow UI for correct model name |
| Input validation fails | Missing columns or out-of-range values | Check `expectations` in job config vs. actual data |
| Quality gate fails with "dominant class" | Model returning one class | Check model version — may need rollback |
| Notification not received | Slack webhook secret missing | `kubectl get secret batch-secrets -n <ns>` |

---

## Further Reading

- `batch/README.md` — module index
- `batch/jobs/_job-schema.yaml` — full job config schema
- `docs/decisions/ADR-ML-018-batch-inference.md` — framework selection
- `monitoring/batch/batch-alerts.yaml` — Prometheus alerts
- `ci/github-actions/batch/` — all batch CI workflows
