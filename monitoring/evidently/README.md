# Evidently AI — Data and Model Drift Monitoring

Evidently is an open-source ML monitoring library that generates drift reports
comparing a reference dataset (training data) to a current dataset (recent
production traffic).

> **Beginner tip**: "Drift" means the data your model receives in production
> has changed compared to the data it was trained on. A common example:
> a fraud detection model trained on 2023 transaction data may degrade in
> 2024 as transaction patterns change. Evidently detects this change early
> so you know to retrain.

---

## Installation

```bash
pip install evidently
```

For Prometheus export:

```bash
pip install evidently prometheus-client
```

---

## Core Usage

See `monitoring/evidently/drift_report.py` for the runnable drift check script.

### Basic drift report

```python
import pandas as pd
from evidently.report import Report
from evidently.metric_presets import DataDriftPreset, TargetDriftPreset

# Load reference data (training set) and current data (last 24h production traffic).
reference_df = pd.read_parquet("data/reference/train_features.parquet")
current_df   = pd.read_parquet("data/current/today_features.parquet")

# Build a drift report with two preset metric groups:
# - DataDriftPreset: checks whether feature distributions have shifted.
# - TargetDriftPreset: checks whether prediction/label distribution has shifted.
report = Report(metrics=[DataDriftPreset(), TargetDriftPreset()])
report.run(reference_data=reference_df, current_data=current_df)

# Save an HTML report for human review.
report.save_html("reports/drift_report.html")

# Get machine-readable JSON summary.
result = report.as_dict()
drift_score = result["metrics"][0]["result"]["dataset_drift_score"]
print(f"Drift score: {drift_score:.3f}")
```

---

## MLflow Integration

After running a drift report, log it as an MLflow artifact so it appears in the
experiment run for easy review:

```python
import mlflow

with mlflow.start_run(run_name="drift_check"):
    # Log the drift score as a numeric metric.
    mlflow.log_metric("dataset_drift_score", drift_score)

    # Log the full HTML report as a viewable artifact.
    mlflow.log_artifact("reports/drift_report.html", artifact_path="monitoring")

    # Tag the run so you can filter drift check runs in the UI.
    mlflow.set_tag("run_type", "drift_check")
```

---

## Setting Up Reference Data

The reference dataset should be saved after training and versioned with DVC:

```bash
# After training, copy the training features to the reference location.
cp data/train_features.parquet data/reference/train_features.parquet

# Version the reference data with DVC.
dvc add data/reference/train_features.parquet
git add data/reference/train_features.parquet.dvc
git commit -m "chore: update reference dataset for drift monitoring"
dvc push
```

> **Important**: Never update the reference dataset without a corresponding
> model retraining. The reference dataset and the deployed model must always
> come from the same training run. Mis-aligned reference data produces false
> drift alerts.

---

## Drift Thresholds

| Threshold | Suggested action |
|-----------|-----------------|
| drift_score < 0.3 | No action — normal distribution variation |
| 0.3 ≤ drift_score < 0.6 | Warning — investigate specific drifted features |
| drift_score ≥ 0.6 | Critical — trigger retraining pipeline |

These thresholds are used by `monitoring/evidently/drift_report.py` and the
Prometheus alert rules in `monitoring/alerts/drift-alerts.yaml`.

---

## Related

- `monitoring/evidently/drift_report.py` — runnable CLI drift check script
- `monitoring/alerts/drift-alerts.yaml` — Prometheus alert rules for drift
- `monitoring/dashboards/model-health.json` — Grafana dashboard
- `docs/golden-paths/model-monitoring.md` — full monitoring golden path
