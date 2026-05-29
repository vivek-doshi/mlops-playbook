# Feast Integration (Phase 1)

This folder adds a baseline Feast integration for fraud-detection features.

## Structure

- `feature_store.yaml` — Feast project and local registry/online store configuration.
- `repo.py` — feature definitions used by both training and serving.

## Apply and materialize

```bash
pip install feast
cd feature-store/feast
feast apply
feast materialize-incremental "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

## Training integration pattern

Use Feast point-in-time retrieval to generate training datasets:

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature-store/feast")
features = store.get_historical_features(
    entity_df=entity_dataframe,
    features=[
        "fraud_features_v1:txn_count_24h",
        "fraud_features_v1:avg_amount_24h",
        "fraud_features_v1:chargeback_rate_30d",
    ],
).to_df()
```

## Serving integration pattern

Use online retrieval in inference services:

```python
online = store.get_online_features(
    features=[
        "fraud_features_v1:txn_count_24h",
        "fraud_features_v1:avg_amount_24h",
    ],
    entity_rows=[{"customer_id": "cust-001"}],
).to_dict()
```
