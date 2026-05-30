# Golden Path — Online Learning

Adapt a production model to new data patterns using streaming mini-batches,
with automatic rollback if accuracy drops.

---

## Prerequisites

- Model in **Production** stage in the MLflow Model Registry.
- Streaming infrastructure provisioned (Kafka topic, Kinesis stream, or Pub/Sub subscription).
- Holdout dataset at `data/holdout.parquet` (static, representative).

---

## Step 1 — Confirm Drift is Occurring

Before triggering online learning, confirm that drift is the root cause:

```bash
# Check drift monitoring dashboard
open https://grafana.internal/d/drift-dashboard

# Or run evidently drift report
python monitoring/evidently/run_drift_report.py --model-name fraud-detector
```

If drift score > 0.15, proceed.

---

## Step 2 — Verify Stream Source Has Data

```python
from online_learning import StreamConsumer

consumer = StreamConsumer(
    source="kafka",
    config={
        "bootstrap_servers": "kafka:9092",
        "topic": "fraud-detector-feedback",
        "group_id": "ol-probe",
    },
    min_batch_size=10,  # Low threshold for probe
)

for batch in consumer.batches():
    print(f"Found {len(batch)} records in stream.")
    consumer.close()
    break
```

---

## Step 3 — Run Online Update (CI)

```bash
gh workflow run online-learning/online-update.yml \
  -f model_name=fraud-detector \
  -f model_version=12 \
  -f source=kafka \
  -f min_batch_size=500
```

The workflow will:
1. Load the Production model from MLflow.
2. Read one mini-batch (≥ 500 records) from Kafka.
3. Apply `partial_fit` (sklearn) or single gradient step (PyTorch).
4. Evaluate accuracy on `data/holdout.parquet`.
5. Fail and trigger `online-rollback.yml` if accuracy drops > 2%.

---

## Step 4 — Monitor the Update

```bash
# Check MLflow run tags
python - <<'EOF'
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
versions = client.get_latest_versions("fraud-detector", stages=["Production"])
for v in versions:
    print(v.version, v.tags)
EOF
```

Look for `online_update: true` on the new Production version.

---

## Step 5 — Manual Rollback (if needed)

```bash
gh workflow run online-learning/online-rollback.yml \
  -f model_name=fraud-detector \
  -f current_version=13 \
  -f reason=manual_override
```

---

## Step 6 — Tune Gates (if needed)

Edit `online_learning/updater.py` constants:

```python
_COOLDOWN_SECONDS = 1800  # 30 minutes — decrease if drift is fast
```

Edit `online_learning/validator.py`:

```python
_MAX_ACCURACY_DROP = 0.02  # 2% — tighten to 0.01 for critical models
```

---

## Related Resources

- [ADR-ML-019 — Online Learning](../decisions/ADR-ML-019-online-learning.md)
- [online_learning/README.md](../../online_learning/README.md)
- [ADR-ML-004 — Drift Monitoring](../decisions/ADR-ML-004-drift-monitoring.md)
