# Lineage and Observability Contract

## Lineage

Training, evaluation, batch, and deployment workflows must record:

| Field | Meaning |
|---|---|
| `source_commit` | Git commit that defined the workflow and code |
| `dependency_lock_hash` | Hash of the resolved dependency set |
| `dataset_id` / `dvc_data_hash` | Exact dataset version |
| `feature_set_version` | Feature definitions and snapshot |
| `training_run_id` | MLflow or pipeline run identifier |
| `model_artifact_digest` | Immutable model artifact identity |
| `container_digest` | Immutable execution image identity |
| `deployment_id` | Runtime deployment identity |

OpenLineage events should model each workflow as a job/run with dataset inputs
and model outputs. MLflow remains the model registry; OpenLineage provides the
cross-system event contract.

## Telemetry

Serving and portal telemetry should use OpenTelemetry and include:

- `request_id`
- `model_name`
- `model_version`
- `deployment_id`
- `feature_set_version`
- `source_commit`
- environment and tenant

Required signals are metrics, logs, and traces. Do not log raw PII, prompts,
secrets, or full feature vectors. Correlate inference latency, errors, drift,
label delay, and business outcomes to the same deployment and model version.

## Promotion requirement

Lineage and observability fields are mandatory evidence. Missing fields block
production promotion rather than creating a warning-only result.
