# MLflow

## What this folder does

This folder provides MLflow building blocks for experiment tracking, metadata persistence, and model registry workflows.
It enables traceable model lifecycle management from training runs to deployment candidates.

## Folder description and details

- `tracking-server/`: local MLflow server bootstrap assets (`docker-compose.yml`, env example).
- `metadata-store/`: database schema and client helpers for metadata persistence.
- `model-registry/`: model versioning and promotion guidance assets.

## How to use this as an individual component

1. Start local tracking server:
   - `docker compose -f mlflow/tracking-server/docker-compose.yml up -d`
2. Configure your training code with `MLFLOW_TRACKING_URI`.
3. Log runs, params, metrics, and artifacts from training jobs.
4. Register candidate models in the registry and assign lifecycle stages.
5. Integrate with CI/CD gates for promotion decisions.

## Inputs and outputs

- Inputs: run metadata, metrics, parameters, model artifacts.
- Outputs: experiment history, registered model versions, and promotion-ready model lineage.
