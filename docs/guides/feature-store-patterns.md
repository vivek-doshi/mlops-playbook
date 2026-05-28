# Feature Store Patterns Guide

## Purpose and Scope

Show how to use a feature store to share, reuse, and govern ML features across
training and serving, preventing training-serving skew and accelerating model
development. This guide covers:

- The GCP Vertex AI Feature Store (provisioned in `terraform/gcp-vertex-ai/main.tf`)
- A portable offline pattern for teams on AWS or Azure
- DVC + feature store hybrid patterns for reproducible training

> **Beginner tip**: A "feature store" is a centralised repository for ML features —
> the numeric columns you feed to your model. Without one, team A computes
> "rolling 7-day average spend" one way in training, and team B computes it
> differently in the serving API. The model then gets different numbers at inference
> time than it was trained on. This is called "training-serving skew" and it causes
> silent accuracy degradation. A feature store solves this by storing one definition
> that both training and serving use.

---

## 1. When to Use a Feature Store vs Inline Feature Engineering

Use a **feature store** when:

- Multiple models share the same features (avoids recomputation and divergence).
- Features require expensive computation (e.g., aggregations over large event logs).
- You need point-in-time correct feature retrieval (crucial for time-series and financial models).
- You have regulatory requirements for feature auditability.

Use **inline feature engineering** when:

- You have a single model with simple, fast transformations.
- Features are computed fresh from raw data with no cross-model sharing.
- Your team is small and the overhead of a feature store is not justified yet.

> **Decision rule**: If two or more models share a feature, promote it to the feature
> store. If only one model uses a feature and it is computed in under 100ms, keep
> it inline and add it to the feature store when sharing becomes necessary.

---

## 2. GCP Vertex AI Feature Store

The Vertex AI Feature Store is provisioned by `terraform/gcp-vertex-ai/main.tf`.

### 2.1 Terraform resource overview

```hcl
# From terraform/gcp-vertex-ai/main.tf
resource "google_vertex_ai_featurestore" "primary" {
  name   = var.featurestore_name
  region = var.region
}
```

After applying Terraform, the Feature Store is accessible via the Vertex AI SDK.

### 2.2 Creating feature groups

```python
from google.cloud import aiplatform

# Initialise the SDK with your project and region.
aiplatform.init(project="my-project", location="us-central1")

# Create a feature group backed by a BigQuery table.
# The BigQuery table must have an entity_id column and a feature_timestamp column.
feature_group = aiplatform.FeatureGroup.create(
    name="user_features",
    source=aiplatform.FeatureGroup.BigQuerySource(
        uri="bq://my-project.my_dataset.user_features_table",
        entity_id_columns=["user_id"],
    ),
    labels={"team": "ml-platform", "environment": "production"},
)

print(f"Created feature group: {feature_group.resource_name}")
```

### 2.3 Serving features for training (batch retrieval)

```python
# Retrieve features for a list of entity IDs at a specific point in time.
# Point-in-time retrieval ensures no data leakage from future timestamps.
feature_view = aiplatform.FeatureView(...)

df = feature_view.read(
    entity_ids=["user_1", "user_2", "user_3"],
    # Timestamps prevent future data from leaking into training — critical for
    # any model that predicts events over time (churn, fraud, demand forecasting).
    feature_timestamp=training_end_date,
)
```

### 2.4 Serving features for online inference

```python
# Online feature retrieval is optimised for low-latency (< 10ms) serving.
# The Feature Store maintains a Redis-backed online store alongside the BigQuery offline store.
online_store = aiplatform.FeatureOnlineStore(...)
result = online_store.fetch_feature_values(
    data_key=aiplatform.FeatureOnlineStore.NearestNeighborSearchConfig.Embedding(
        value=[1.0, 2.0, 3.0]
    ),
    feature_view=feature_view,
)
```

---

## 3. Offline Pattern for AWS and Azure

Teams on AWS or Azure can use a versioned Parquet dataset tracked with DVC
as a lightweight feature store.

```
features/
├── user_features/
│   ├── v1/
│   │   └── user_features.parquet      # tracked by DVC
│   ├── v2/
│   │   └── user_features.parquet
│   └── latest -> v2/                  # symlink or pointer
```

### 3.1 Writing features

```python
import pandas as pd

# Compute features from raw data and save as Parquet.
# Parquet is columnar, efficient, and preserves data types exactly.
features_df = compute_user_features(raw_events_df)
features_df.to_parquet("features/user_features/v2/user_features.parquet", index=False)
```

Track with DVC:

```bash
dvc add features/user_features/v2/user_features.parquet
git add features/user_features/v2/user_features.parquet.dvc
git commit -m "feat: user features v2 with rolling 30d spend"
dvc push
```

### 3.2 Reading features in training and serving

```python
import pandas as pd

# Training uses the same path as serving — no transformation difference.
# This is the key property that prevents training-serving skew.
FEATURES_PATH = "features/user_features/v2/user_features.parquet"

features_df = pd.read_parquet(FEATURES_PATH)
```

---

## 4. Preventing Training-Serving Skew

Training-serving skew is one of the most common — and hardest to debug — issues
in production ML. Follow these rules:

1. **One feature definition, two callsites** — write the feature transformation
   once (a Python function), import it in both your training pipeline and your
   serving handler. Never copy-paste transformations.

2. **Version your transformations** — if a transformation changes, create a new
   feature group version. Never mutate existing versions in place.

3. **Log feature values at serving time** — write the actual values the model
   received to your prediction log. Compare them against training distributions
   using Evidently (see `docs/golden-paths/model-monitoring.md`).

4. **Pin feature versions in model registration** — when registering a model,
   tag the MLflow version with the feature group name and version used:

   ```python
   client.set_model_version_tag("my-model", version, "feature_group", "user_features_v2")
   ```

---

## 5. DVC + Feature Store Hybrid Pattern

Use DVC to snapshot feature group exports for reproducible training:

```bash
# 1. Export features from the Feature Store to a local file.
python scripts/export_features.py \
  --feature-group user_features \
  --version v2 \
  --output features/training_snapshot.parquet

# 2. Track the snapshot with DVC.
dvc add features/training_snapshot.parquet
git add features/training_snapshot.parquet.dvc
git commit -m "feat: training snapshot with user_features_v2"
dvc push
```

This approach gives you:
- Feature Store for online serving (low latency).
- DVC snapshot for reproducible training (exact dataset replay).
- MLflow tag linking the model version to the DVC pointer.

---

## 6. Integration with MLflow Experiment Tracking

Log feature group names and versions as MLflow tags on every training run:

```python
import mlflow

with mlflow.start_run():
    # ... training ...

    # Log which feature groups were used. This is essential for debugging
    # "why did model accuracy drop?" — feature group changes are often the cause.
    mlflow.set_tag("feature_groups", "user_features_v2,product_features_v1")
    mlflow.set_tag("feature_snapshot_dvc_hash", dvc_hash)
```

---

## Related

- `terraform/gcp-vertex-ai/main.tf` — Feature Store provisioning
- `dvc/remote-storage/README.md` — DVC remote for feature snapshots
- `docs/golden-paths/experiment-tracking.md` — logging feature tags in MLflow
- `docs/golden-paths/model-monitoring.md` — detecting training-serving skew in production
