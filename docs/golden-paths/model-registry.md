# Model Registry Golden Path

## Purpose and Scope

Formalise model promotion through Staging and Production stages in the MLflow Model
Registry so only approved, evaluated models reach production serving. This creates
a clear audit trail and approval gate between experimentation and deployment.

> **Beginner tip**: The MLflow Model Registry is like a version control system
> specifically for trained models. Each "version" corresponds to a specific training
> run. Models move through stages — None → Staging → Production — and each transition
> can be gated by automated checks and human approval. Only models in the
> `Production` stage are deployed by the serving pipeline.

---

## Prerequisites

| Requirement | Guide |
|-------------|-------|
| MLflow tracking server with PostgreSQL backend running | `mlflow/tracking-server/` |
| Training pipeline logging model artifacts | `docs/golden-paths/model-training-pipeline.md` |
| Promotion policy defined | `policy/model-approval/README.md` |

---

## Promotion Flow

```
Training Run
     ↓
Registered (stage: None)  ← automatically by register_model.py
     ↓
Staging                   ← automated via CI after evaluation passes
     ↓
[Approval Gate]           ← requires human approval + policy check
     ↓
Production                ← serves live traffic
     ↓
Archived                  ← previous Production version after rotation
```

---

## Step-by-Step Implementation

### Step 1 — Register a model from a training run

```python
import mlflow

# -----------------------------------------------------------------------
# register_model() links a specific run's artifacts to a named model in
# the registry. The run_id ties this version to an exact set of metrics,
# params, and data hash — providing complete provenance.
# -----------------------------------------------------------------------
run_id = "abc123"   # find this in the MLflow UI or from mlflow.active_run()

result = mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="my-model",   # this is the registry name teams will reference
)

print(f"Registered version: {result.version}")
```

---

### Step 2 — Transition to Staging (automated via CI)

```python
client = mlflow.tracking.MlflowClient()

# -----------------------------------------------------------------------
# Staging means "ready for evaluation, not yet approved for production".
# This transition happens automatically after the evaluation gate passes.
# archive_existing_versions=False keeps previous Staging versions visible
# for comparison. Use True to clean up.
# -----------------------------------------------------------------------
client.transition_model_version_stage(
    name="my-model",
    version=result.version,
    stage="Staging",
    archive_existing_versions=False,
)
```

---

### Step 3 — Approval gate before Production

Before transitioning to Production, all three conditions must be met:

1. **Automated CI checks pass** — accuracy ≥ threshold, no data quality failures.
   Reference `ci/github-actions/model-evaluation/evaluate.yml`.

2. **Human approval** — merge a PR that adds an entry to
   `policy/model-approval/approved-versions.yaml`, OR approve a GitHub Environment
   protection rule on the `production` environment.

3. **No open high-severity drift alerts** — check the monitoring dashboard before
   promoting. Reference `monitoring/alerts/drift-alerts.yaml`.

---

### Step 4 — Tag every version with lineage

```python
# -----------------------------------------------------------------------
# Lineage tags are critical for governance, debugging, and rollback.
# They answer: "Which code, which data, and who approved this model?"
# Always tag before transitioning to Production.
# -----------------------------------------------------------------------
import os

client.set_model_version_tag(
    name="my-model",
    version=result.version,
    key="git_sha",
    value=os.environ["GITHUB_SHA"],   # Git commit that produced this model
)
client.set_model_version_tag(
    name="my-model",
    version=result.version,
    key="dvc_data_hash",
    value=dvc_hash,       # hash from dvc status --show-json
)
client.set_model_version_tag(
    name="my-model",
    version=result.version,
    key="approved_by",
    value="platform-team",  # update with the actual approver
)
client.set_model_version_tag(
    name="my-model",
    version=result.version,
    key="eval_accuracy",
    value=str(eval_accuracy),
)
```

---

### Step 5 — Transition to Production

```python
# -----------------------------------------------------------------------
# archive_existing_versions=True automatically moves the current Production
# version to Archived. This ensures exactly one version is in Production
# at any time and preserves history for rollback.
# -----------------------------------------------------------------------
client.transition_model_version_stage(
    name="my-model",
    version=result.version,
    stage="Production",
    archive_existing_versions=True,
)

print(f"my-model v{result.version} is now in Production")
```

---

### Step 6 — Load the Production model in serving

```python
# -----------------------------------------------------------------------
# This is the standard pattern for loading a Production model in serving.
# The serving runtime reads the latest Production version at startup.
# If you need a specific version, use "models:/my-model/3" (version number).
# -----------------------------------------------------------------------
model = mlflow.pyfunc.load_model("models:/my-model/Production")

# The model exposes a predict() method regardless of the underlying framework.
predictions = model.predict(input_data)
```

---

## Rollback Procedure

When a Production model must be reverted immediately:

```python
# 1. Find the last Archived version (the previous Production).
client = mlflow.tracking.MlflowClient()
versions = client.search_model_versions("name='my-model'")
archived = [v for v in versions if v.current_stage == "Archived"]
archived.sort(key=lambda v: int(v.version), reverse=True)
rollback_version = archived[0].version

# 2. Transition it back to Production.
client.transition_model_version_stage(
    name="my-model",
    version=rollback_version,
    stage="Production",
    archive_existing_versions=True,   # archives the bad version
)

# 3. Verify lineage tags to confirm the rollback target is safe.
v = client.get_model_version("my-model", rollback_version)
print("Rollback target tags:", dict(v.tags))
```

---

## Validation

1. Open the MLflow UI → Models section.
2. Select `my-model`.
3. Confirm exactly one version is in `Production` stage.
4. Check the version tags: `git_sha`, `dvc_data_hash`, `approved_by` must all be set.
5. Run a serving health check against the deployed endpoint.

---

## Related

- `policy/model-approval/README.md` — approval requirements
- `policy/model-approval/approved-versions.yaml` — approval registry
- `mlflow/model-registry/README.md` — server-side registry configuration
- `docs/golden-paths/model-serving.md` — deploying the Production model
- `ci/github-actions/model-deployment/deploy.yml` — deployment workflow
