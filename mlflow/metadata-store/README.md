# ML Metadata Store (Phase 1)

This folder defines a lightweight metadata store for lineage tracking.

## Files

- `schema.sql` — relational schema for datasets, feature sets, runs, model versions, and deployments.
- `client.py` — Python client for schema bootstrap and lineage writes.

## Usage

```bash
python mlflow/metadata-store/client.py
```

Then use `MetadataStoreClient` in CI or training scripts to register:

1. Dataset versions (DVC hash + storage URI)
2. Training run metadata (trigger + git SHA + metrics)
3. Run input links (dataset/featureset lineage)
4. Model versions and deployment records
