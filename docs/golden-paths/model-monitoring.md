# Model Monitoring Golden Path

## Purpose and Scope

Detect data drift, prediction drift, and model performance degradation in production
so teams can trigger retraining or rollback before business impact occurs.

> **Beginner tip**: Models can "drift" — their performance degrades over time because
> the real-world data they receive changes compared to what they were trained on.
> For example, a fraud detection model trained in January might be less accurate in
> December because spending patterns changed. Monitoring catches this early.
> Evidently generates reports; Prometheus stores the numbers; Grafana visualises them.

---

## Prerequisites

| Requirement | Guide |
|-------------|-------|
| Model deployed and serving live traffic | `docs/golden-paths/model-serving.md` |
| Prometheus and Grafana running | `devops-playbook/observability/` |
| Evidently installed in the monitoring worker | `pip install evidently` |
| Reference dataset available | Saved at training time alongside the model |

---

## Monitoring Architecture

```
Live predictions + input features
           ↓
  (logged to object storage or database by the serving workload)
           ↓
  monitoring/evidently/drift_report.py  (scheduled job, daily or per N predictions)
           ↓
  Prometheus metrics exposition (via prometheus_client Pushgateway)
           ↓
  Grafana dashboards (monitoring/dashboards/model-health.json)
           ↓
  Prometheus alerting rules (monitoring/alerts/drift-alerts.yaml)
           ↓
  PagerDuty / Slack notifications (via devops-playbook/notifications/)
```

---

## Step-by-Step Implementation

### Step 1 — Log predictions from the serving workload

Add prediction logging to your serving handler:

```python
# In your model serving handler, log each prediction to a store.
# This creates the "current data" that will be compared against reference data.
import json
import boto3   # or azure-storage-blob, google-cloud-storage

def log_prediction(input_features: dict, prediction: float) -> None:
    """
    Write input features and prediction to object storage for drift analysis.
    This should be async or fire-and-forget to avoid adding latency.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "features": input_features,
        "prediction": prediction,
    }
    # Append to a daily partition in object storage.
    # Use the same bucket as your DVC remote for simplicity.
    key = f"predictions/{datetime.utcnow().strftime('%Y/%m/%d')}/pred.jsonl"
    # s3.put_object(Body=json.dumps(record) + "\n", Bucket=BUCKET, Key=key)
```

---

### Step 2 — Save the reference dataset at training time

```python
# In pipelines/train.py, save the training distribution as reference data.
# This is the baseline that drift reports compare against.
import pandas as pd

# Save training data statistics alongside the model artifact.
reference_df = pd.read_csv("data/processed/train.csv")
reference_df.to_csv("artifacts/reference_data.csv", index=False)

# Log the reference data to MLflow for provenance.
mlflow.log_artifact("artifacts/reference_data.csv")
```

---

### Step 3 — Run a drift report

The `monitoring/evidently/drift_report.py` script is the standard drift runner:

```bash
# Run manually or schedule in CI (see ci/github-actions/model-monitoring/drift-check.yml).
python monitoring/evidently/drift_report.py \
  --reference artifacts/reference_data.csv \
  --current   data/current/predictions_today.csv \
  --threshold 0.3

# Exit code 0 = no significant drift.
# Exit code 1 = drift score exceeds threshold. Triggers alert.
```

See `monitoring/evidently/README.md` for full installation and configuration.

---

### Step 4 — Expose metrics to Prometheus

```python
# In monitoring/evidently/drift_report.py (abbreviated example).
# The full script with argparse and HTML report is in monitoring/evidently/.
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://localhost:9091")

registry = CollectorRegistry()

# Create a Prometheus gauge for the drift score.
drift_gauge = Gauge(
    "model_drift_score",
    "Evidently dataset drift score (0–1). Values above 0.3 indicate drift.",
    labelnames=["model_name", "model_version"],
    registry=registry,
)
drift_gauge.labels(model_name="my-model", model_version="1").set(drift_score)

# Push to the Prometheus Pushgateway.
# The Pushgateway is a component in the devops-playbook observability stack.
push_to_gateway(PUSHGATEWAY_URL, job="drift_report", registry=registry)
```

---

### Step 5 — Configure Prometheus alerting

The alert rules in `monitoring/alerts/drift-alerts.yaml` must be applied to
Prometheus. Reference `devops-playbook/observability/prometheus/` for the
alert manager configuration.

```bash
# Apply as a Kubernetes ConfigMap if Prometheus is running in-cluster.
kubectl apply -f monitoring/alerts/drift-alerts.yaml
```

Alert thresholds (defined in `monitoring/alerts/drift-alerts.yaml`):

| Alert | Threshold | Severity |
|-------|-----------|----------|
| `DataDriftDetected` | drift score > 0.3 for 30 min | warning |
| `SevereDriftDetected` | drift score > 0.6 for 10 min | critical |
| `ModelAccuracyDegraded` | accuracy drop > 10% | warning |
| `PredictionVolumeAnomaly` | prediction rate drops > 50% | warning |

---

### Step 6 — Import the Grafana dashboard

Import `monitoring/dashboards/model-health.json` into Grafana:

1. Open Grafana → Dashboards → Import.
2. Upload `monitoring/dashboards/model-health.json`.
3. Select your Prometheus data source.

See `monitoring/dashboards/README.md` for ConfigMap-based import in-cluster.

---

## Retraining Trigger

When a `DataDriftDetected` alert fires:

```yaml
# Option 1: Automatic — add this to your alertmanager config.
# It triggers the training workflow via GitHub Actions API when drift is detected.
receivers:
  - name: retrain-trigger
    webhook_configs:
      - url: "https://api.github.com/repos/org/mlops-playbook/actions/workflows/train.yml/dispatches"
        http_config:
          authorization:
            credentials: "${GITHUB_PAT}"
```

Option 2: Manual — review the drift report, then trigger
`ci/github-actions/model-training/train.yml` via `workflow_dispatch`.

---

## Rollback Trigger

If error rate exceeds SLO before a retrain can complete:

1. Transition the current Production model version to Archived in MLflow.
2. Promote the previous Archived version back to Production.
3. See `docs/golden-paths/model-registry.md` — Rollback Procedure.

---

## Validation

```bash
# Confirm the drift report runs without errors.
python monitoring/evidently/drift_report.py \
  --reference artifacts/reference_data.csv \
  --current   artifacts/reference_data.csv \   # identical data = no drift
  --threshold 0.3
# Expected output: drift_score < 0.3, exit code 0.

# Confirm the metric reached Prometheus.
curl http://localhost:9091/metrics | grep model_drift_score
```

---

## Related

- `monitoring/evidently/README.md` — Evidently setup
- `monitoring/evidently/drift_report.py` — runnable drift script
- `monitoring/alerts/drift-alerts.yaml` — Prometheus alert rules
- `monitoring/dashboards/model-health.json` — Grafana dashboard
- `docs/golden-paths/model-training-pipeline.md` — triggering retraining
- `ci/github-actions/model-monitoring/drift-check.yml` — scheduled monitoring workflow
