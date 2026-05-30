# Online Learning

Real-time model updates from streaming data with automatic rollback.

---

## Architecture

```
Stream (Kafka / Kinesis / Pub/Sub)
        │
        ▼
  StreamConsumer
  (consumers/ dispatcher)
        │
        ▼  mini-batch ≥ 500 records
  OnlineUpdater
  (partial_fit or single-epoch gradient)
        │
        ▼
  OnlineValidator
  (holdout accuracy gate, 2% drop → rollback)
        │
        ▼
  MLflow Model Registry  ←──  OnlineRollback (auto-restore on failure)
```

---

## When to Use Online Learning

| Scenario | Recommended? |
|---|---|
| Concept drift detected by monitoring | ✅ |
| New label distribution in live traffic | ✅ |
| Model accuracy below SLO | ✅ |
| Initial model training | ❌ Use offline training pipeline |
| Major architecture change | ❌ Use full fine-tune (llmops/) |

---

## Quick Start

```python
from online_learning import StreamConsumer, OnlineUpdater, OnlineValidator, OnlineRollback

# 1. Load current Production model from MLflow
import mlflow
model = mlflow.sklearn.load_model("models:/fraud-detector/Production")

# 2. Create consumer
consumer = StreamConsumer(
    source="kafka",
    config={"bootstrap_servers": "kafka:9092", "topic": "feedback", "group_id": "ol-group"},
    min_batch_size=500,
)

# 3. Create updater and validator
updater = OnlineUpdater(model=model, mlflow_run_id="<run-id>")
validator = OnlineValidator(holdout_path="data/holdout.parquet")
rollback = OnlineRollback(model_name="fraud-detector")

# 4. Update loop
for batch in consumer.batches():
    applied = updater.apply(batch, label_col="is_fraud")
    if applied:
        passed, metrics = validator.evaluate(model, baseline_accuracy=0.94)
        if not passed:
            rollback.execute(current_version="12", reason="accuracy_drop")
            break
```

---

## Gates

Online learning applies the **same three gates** as offline training:

| Gate | Threshold |
|---|---|
| Accuracy drop | ≤ 2% vs. baseline |
| Cooldown | 30 minutes between updates |
| Min batch size | ≥ 500 records |

---

## MLflow Tags

| Tag | Value |
|---|---|
| `online_update` | `true` (active), `rolled_back`, `restored_after_rollback` |
| `rollback_reason` | `accuracy_drop` or custom string |
| `rollback_at` | ISO 8601 timestamp |

---

## Metrics Logged per Update

| Metric | Description |
|---|---|
| `update_batch_size` | Number of records in the mini-batch |
| `update_mini_batch_count` | Cumulative mini-batches applied this run |
| `stream_lag_seconds` | Consumer lag from stream source |

---

## CI Workflows

| Workflow | Trigger |
|---|---|
| `online-update.yml` | `workflow_dispatch` or stream event |
| `online-rollback.yml` | Accuracy gate failure |

---

## Related Decisions

- [ADR-ML-019 — Online Learning](../docs/decisions/ADR-ML-019-online-learning.md)
