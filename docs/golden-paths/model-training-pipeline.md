# Model Training Pipeline Golden Path

## Purpose and Scope

Define a reproducible, CI-triggered training pipeline that logs to MLflow, versions
artifacts with DVC, and gates promotion on evaluation thresholds. Every run produces
a fully auditable artifact that can be traced back to a specific code commit and
dataset version.

> **Beginner tip**: A "training pipeline" is not just a script — it is a sequence of
> verifiable stages (ingest → train → evaluate → register) where the output of each
> stage is tracked. If any stage fails or produces metrics below your quality bar,
> the pipeline stops and no model reaches production. This prevents bad models from
> being deployed silently.

---

## Prerequisites

| Requirement | Guide |
|-------------|-------|
| Experiment tracking configured | `docs/golden-paths/experiment-tracking.md` |
| Data versioning configured | `docs/golden-paths/data-versioning.md` |
| GitHub Actions secrets set | `MLFLOW_TRACKING_URI`, `DVC_ENDPOINT_URL`, cloud credentials |
| DVC remote accessible | `dvc/remote-storage/README.md` |

---

## Pipeline Stages

The following stages are defined in `ci/dvc/dvc-pipeline.yml` and the
`dvc.yaml` template at `dvc/pipeline-templates/train-eval-deploy.yaml`:

| Stage | Script | Inputs | Outputs |
|-------|--------|--------|---------|
| `ingest` | `pipelines/ingest.py` | `data/raw` | `data/processed` |
| `train` | `pipelines/train.py` | `data/processed` | `artifacts/model`, `metrics/train.json` |
| `evaluate` | `pipelines/evaluate.py` | `artifacts/model` | `metrics/eval.json` |
| `register` | `pipelines/register_model.py` | `artifacts/model`, `metrics/eval.json` | MLflow registry entry |

> **Intermediate note**: Each stage has declared `deps` (dependencies) and `outs`
> (outputs) in `dvc.yaml`. DVC uses file hashes to decide which stages to re-run.
> If `data/processed` has not changed since the last run, DVC skips `train`.
> This makes iterative development much faster.

---

## Step-by-Step Implementation

### Step 1 — Define your pipeline in dvc.yaml

```yaml
# dvc.yaml — defines the stages of your ML pipeline.
# Copy from dvc/pipeline-templates/train-eval-deploy.yaml and customise.
stages:
  ingest:
    cmd: python pipelines/ingest.py
    deps:
      - data/raw
      - pipelines/ingest.py
    outs:
      - data/processed

  train:
    cmd: python pipelines/train.py
    deps:
      - data/processed
      - pipelines/train.py
      - params.yaml        # hyperparameters are tracked as params
    outs:
      - artifacts/model
    metrics:
      - metrics/train.json:
          cache: false     # metrics files are small; don't cache them

  evaluate:
    cmd: python pipelines/evaluate.py
    deps:
      - artifacts/model
      - pipelines/evaluate.py
    metrics:
      - metrics/eval.json:
          cache: false

  register:
    cmd: python pipelines/register_model.py
    deps:
      - artifacts/model
      - metrics/eval.json
      - pipelines/register_model.py
```

---

### Step 2 — Write your training script (pipelines/train.py)

```python
# pipelines/train.py — minimal example with MLflow and DVC integration.
import json
import os
import subprocess
import mlflow
import yaml

# Load hyperparameters from params.yaml (tracked by DVC).
# This makes params visible in `dvc params diff` and MLflow tags.
with open("params.yaml") as f:
    params = yaml.safe_load(f)

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment(params.get("experiment_name", "default-experiment"))

with mlflow.start_run(run_name=f"train-{os.environ.get('GITHUB_RUN_ID', 'local')}"):

    # Log all params so every run is fully reproducible from the registry.
    mlflow.log_params(params)

    # -----------------------------------------------------------------------
    # YOUR TRAINING LOGIC HERE
    # Replace this block with your actual model training code.
    # -----------------------------------------------------------------------
    # model = build_model(params)
    # model.fit(train_data, epochs=params["epochs"])
    # val_loss = model.evaluate(val_data)
    val_loss = 0.23   # placeholder
    val_acc  = 0.91   # placeholder

    mlflow.log_metrics({"val_loss": val_loss, "val_acc": val_acc})
    mlflow.log_artifact("artifacts/model")

    # Tag the run with the DVC data hash for full traceability.
    dvc_hash = subprocess.check_output(
        ["dvc", "status", "--show-json"], text=True
    )
    mlflow.set_tag("dvc_data_hash", dvc_hash.strip())
    mlflow.set_tag("git_sha", os.environ.get("GITHUB_SHA", "local"))

# Write metrics to file so DVC can track them and the evaluation gate can read them.
os.makedirs("metrics", exist_ok=True)
with open("metrics/train.json", "w") as f:
    json.dump({"val_loss": val_loss, "val_acc": val_acc}, f, indent=2)
```

---

### Step 3 — Write your evaluation script (pipelines/evaluate.py)

```python
# pipelines/evaluate.py — runs offline evaluation against a held-out test set.
import json
import os
import mlflow

MODEL_URI = os.environ.get("MODEL_URI", "artifacts/model")

# Load the model from the path or MLflow URI.
# model = mlflow.pyfunc.load_model(MODEL_URI)

# -----------------------------------------------------------------------
# YOUR EVALUATION LOGIC HERE
# -----------------------------------------------------------------------
# accuracy = evaluate(model, test_data)
accuracy = 0.89   # placeholder

os.makedirs("metrics", exist_ok=True)
with open("metrics/eval.json", "w") as f:
    json.dump({"accuracy": accuracy, "threshold": 0.85}, f, indent=2)

print(f"Evaluation complete. accuracy={accuracy}")
```

---

### Step 4 — Add an evaluation gate in CI

Add this step to `ci/github-actions/model-training/train.yml` after the evaluate stage:

```yaml
- name: Enforce evaluation threshold
  run: |
    python - << 'PY'
    import json, sys

    # Read the metrics file produced by evaluate.py.
    with open("metrics/eval.json") as f:
        metrics = json.load(f)

    threshold = 0.85   # minimum acceptable accuracy for promotion

    if metrics.get("accuracy", 0) < threshold:
        print(f"FAILED: accuracy {metrics['accuracy']:.4f} is below threshold {threshold}")
        sys.exit(1)   # non-zero exit code fails the CI step

    print(f"PASSED: accuracy {metrics['accuracy']:.4f} >= threshold {threshold}")
    PY
```

---

### Step 5 — Model registration (pipelines/register_model.py)

```python
# pipelines/register_model.py — registers the trained model in MLflow registry.
import json
import os
import mlflow

TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]
mlflow.set_tracking_uri(TRACKING_URI)

# Read metrics to include as version tags.
with open("metrics/eval.json") as f:
    metrics = json.load(f)

# Register the model under a versioned name in the MLflow registry.
# On first registration this creates version 1; subsequent calls increment.
result = mlflow.register_model(
    model_uri="artifacts/model",
    name="my-model",
)

# Tag the version with lineage information for governance and rollback.
client = mlflow.tracking.MlflowClient()
client.set_model_version_tag(result.name, result.version, "git_sha", os.environ.get("GITHUB_SHA", ""))
client.set_model_version_tag(result.name, result.version, "accuracy", str(metrics["accuracy"]))

# Transition to Staging immediately — Production promotion requires manual approval.
client.transition_model_version_stage(
    name=result.name,
    version=result.version,
    stage="Staging",
)
print(f"Registered {result.name} version {result.version} → Staging")
```

---

## CI Workflow Overview

Reference `ci/github-actions/model-training/train.yml`:

```
trigger: workflow_dispatch (manual) or push to main
   ↓
pull data from DVC remote
   ↓
dvc repro train (runs all out-of-date stages)
   ↓
push artifacts to DVC remote
   ↓
register run in MLflow
   ↓
drift pre-check on new data (warning only)
   ↓
promotion to registry (via evaluate.yml and deploy.yml)
```

---

## Validation

1. Trigger the `model-training` workflow from GitHub Actions.
2. Check MLflow UI for a completed run with:
   - All parameters logged.
   - Metrics: `val_loss`, `val_acc`.
   - Tag: `dvc_data_hash`.
3. Check `dvc status` shows `Data and pipelines are up to date`.
4. Confirm the model version appears in `Staging` stage in the MLflow registry.

---

## Rollback / Failure Handling

| Situation | Action |
|-----------|--------|
| Evaluation gate fails | Fix the model or data, re-trigger the workflow. |
| DVC pull fails in CI | Check cloud credentials in GitHub Secrets. |
| Pipeline stuck at a stage | Run `dvc status` to see which stage is dirty. |
| Re-run at known-good SHA | Use `workflow_dispatch` with the old Git SHA checked out as a branch. |

---

## Related

- `ci/dvc/dvc-pipeline.yml` — DVC pipeline definition
- `ci/github-actions/model-training/train.yml` — CI workflow
- `docs/golden-paths/model-registry.md` — promoting models from Staging to Production
- `docs/golden-paths/experiment-tracking.md` — logging experiment details
