# Experiment Tracking Golden Path

## Purpose and Scope

Standardise how experiments are logged, compared, and linked to data versions so that
every training run is reproducible and auditable. This guide covers MLflow as the
default experiment tracking tool, as decided in `docs/decisions/ADR-ML-001-experiment-tracking.md`.

Scope: any model training run — interactive notebook, scheduled pipeline, or CI-triggered job.

---

## Prerequisites

| Requirement | Where to configure |
|-------------|-------------------|
| MLflow tracking server running | `mlflow/tracking-server/` |
| DVC remote configured | `dvc/remote-storage/` |
| `MLFLOW_TRACKING_URI` env var set | GitHub Actions secret or local `.env` |
| Python ≥ 3.10 with `mlflow` installed | `pip install mlflow` |

> **Beginner tip**: The "tracking server" is simply a web application that records your
> experiment parameters, metrics, and model files. Think of it as a structured logbook
> that everyone on the team can read. Instead of saving your model to a folder and
> writing notes in a spreadsheet, MLflow does both automatically.

---

## Step-by-Step Implementation

### Step 1 — Start the local MLflow stack

```bash
cd mlflow/tracking-server

# Copy the example environment file and fill in secrets before starting.
# Never commit the real .env file — it is listed in .gitignore.
cp .env.example .env

# Start PostgreSQL, MinIO (S3-compatible storage), and the MLflow server.
docker compose up -d

# Confirm the stack is healthy — all three containers should show "running".
docker compose ps
```

Open `http://localhost:5000` to verify the MLflow UI is accessible.

---

### Step 2 — Set the tracking URI in your training script or notebook

```python
import os
import mlflow

# -----------------------------------------------------------------------
# TRACKING URI — tells the MLflow client where to send experiment data.
# In CI, this is read from the MLFLOW_TRACKING_URI secret.
# Locally, set it in your shell: export MLFLOW_TRACKING_URI=http://localhost:5000
# -----------------------------------------------------------------------
mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])

# An "experiment" groups related runs together, like "fraud-detection-v2".
# If the experiment does not exist, MLflow creates it automatically.
mlflow.set_experiment("my-experiment")
```

---

### Step 3 — Wrap your training loop with an MLflow run

```python
import subprocess

# -----------------------------------------------------------------------
# mlflow.start_run() opens a new run record in the tracking server.
# Everything logged inside this block is attached to this run.
# The context manager automatically calls mlflow.end_run() on exit,
# even if an exception is raised (status will be FAILED in that case).
# -----------------------------------------------------------------------
with mlflow.start_run(run_name="baseline-v1"):

    # Log hyperparameters — these are fixed before training starts.
    # Parameters are searchable and comparable across runs.
    mlflow.log_params({
        "lr": 0.01,
        "epochs": 10,
        "batch_size": 32,
        "model_architecture": "resnet50",
    })

    # --- your training loop goes here ---
    # val_loss, val_acc = train(model, data, params)

    # Log metrics — numeric values measured during or after training.
    # You can call log_metric() inside a loop to log per-epoch values.
    mlflow.log_metrics({"val_loss": 0.23, "val_acc": 0.91})

    # Log the trained model artifact.
    # mlflow.log_artifact uploads the file/folder to the artifact store.
    mlflow.log_artifact("artifacts/model")

    # -----------------------------------------------------------------------
    # Link DVC params to this run so the run is reproducible.
    # Anyone who checks this tag knows exactly which pipeline config was used.
    # -----------------------------------------------------------------------
    dvc_params = subprocess.check_output(
        ["dvc", "params", "diff", "--show-md"], text=True
    )
    mlflow.set_tag("dvc_params_diff", dvc_params)
```

---

### Step 4 — Link DVC data hash to the MLflow run

```python
# -----------------------------------------------------------------------
# This is the most important traceability step.
# It records which exact version of the dataset was used for this run.
# Without this, you cannot reproduce the run later even if you have the code.
# -----------------------------------------------------------------------
import json

dvc_status_raw = subprocess.check_output(
    ["dvc", "status", "--show-json"], text=True
)
dvc_hash = json.loads(dvc_status_raw)

# Store as a tag so it appears in the MLflow UI alongside the metrics.
mlflow.set_tag("dvc_data_hash", json.dumps(dvc_hash))
```

---

### Step 5 — Log a failure safely in CI

```python
# -----------------------------------------------------------------------
# Always end the run explicitly when wrapping training in a try/except.
# Failing to call end_run() leaves the run in a "RUNNING" state forever,
# which makes the run appear active when it is not.
# -----------------------------------------------------------------------
try:
    with mlflow.start_run(run_name="ci-run"):
        # ... training ...
        pass
except Exception as exc:
    mlflow.end_run(status="FAILED")
    raise
```

---

## CI Integration

Reference `ci/github-actions/model-training/train.yml`.

Add `MLFLOW_TRACKING_URI` as a GitHub Actions secret:

```yaml
- name: Register run in MLflow
  env:
    MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  run: |
    python - << 'PY'
    import mlflow, os
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    print("MLflow tracking configured:", mlflow.get_tracking_uri())
    PY
```

---

## Validation Steps

1. Open `http://localhost:5000` (or your server URI).
2. Select your experiment from the left sidebar.
3. Confirm a new run appears with:
   - Parameters: `lr`, `epochs`, etc.
   - Metrics: `val_loss`, `val_acc`.
   - Tags: `dvc_data_hash`.
4. Click the run name to expand the artifact browser and confirm `artifacts/model` is uploaded.

---

## Rollback / Failure Handling

| Situation | Action |
|-----------|--------|
| Tracking server unreachable | Set `MLFLOW_TRACKING_URI=./mlruns` to fall back to local file store. Import later with `mlflow experiments csv-import`. |
| Artifact store (MinIO/S3) unreachable | Check network, then `docker compose restart minio`. |
| Run stuck in RUNNING state | Call `mlflow.end_run(status="FAILED")` manually from the client, or use the MLflow UI > run > "Mark as failed". |
| Wrong experiment name | Use `mlflow.set_experiment()` again — it does not overwrite existing runs. |

---

## Related

- `docs/golden-paths/data-versioning.md` — data hash tagging
- `docs/golden-paths/model-training-pipeline.md` — CI integration
- `docs/golden-paths/model-registry.md` — promoting runs to registry
- `mlflow/tracking-server/README.md` — server setup
- `docs/decisions/ADR-ML-001-experiment-tracking.md` — why MLflow
