# Model Approval Policy

Every model promoted from **Staging** to **Production** in the MLflow Model Registry
must pass the approval gate defined here. The gate is automated in CI but a
designated approver from the team must review and merge the approval PR.

> **Beginner tip**: "Staging" is a holding area for models that have passed
> automated tests but have not yet been released to production. The approval gate
> is the set of automated and human checks that must pass before a model is
> allowed to serve real user traffic.

---

## Approval Requirements

All three conditions must be met to promote a model to Production:

### 1. Model performance threshold

The model's accuracy (or primary metric) on the held-out test set must meet
or exceed the threshold registered in the MLflow model tag.

```python
# Checking the threshold programmatically (from ci/evaluate.py).
client = mlflow.tracking.MlflowClient()
threshold = float(client.get_model_version_tag(model_name, version, "accuracy_threshold"))
achieved  = float(client.get_model_version_tag(model_name, version, "test_accuracy"))

if achieved < threshold:
    raise ValueError(f"Accuracy {achieved:.4f} < threshold {threshold:.4f}. Blocked.")
```

### 2. No significant data drift

The dataset drift score reported by `monitoring/evidently/drift_report.py` must
be below 0.3. This check is run in the `drift-check` CI step before promotion.

```bash
# Gate check (from evaluate.yml).
python monitoring/evidently/drift_report.py \
  --reference data/reference/train_features.parquet \
  --current data/current/validation_features.parquet \
  --threshold 0.3
# Script exits with code 1 if drift >= 0.3, blocking the CI step.
```

### 3. Data lineage verification

The DVC data hash recorded on the model run must match the `.dvc` pointer file
in the repository. This ensures the model was trained on the exact data version
claimed in the registry tag.

```python
# From ci/register_model.py.
import subprocess

run_info = client.get_run(run_id)
logged_hash = run_info.data.tags.get("dvc_data_hash")
repo_hash = subprocess.check_output(
    ["dvc", "status", "--json", "data/dataset.dvc"]
).decode()

if logged_hash not in repo_hash:
    raise ValueError(f"Data hash mismatch — model was not trained on the registered data version.")
```

---

## Approval Registry

Approved Production model versions are recorded in `policy/model-approval/approved-versions.yaml`.

Format:

```yaml
approvals:
  - model_name: fraud-detection
    version: "7"
    approved_by: alice@example.com
    approved_at: "2024-06-15T09:00:00Z"
    mlflow_run_id: abc123def456
    dvc_data_hash: "a3f8c1..."
    notes: "Passed all gates. Accuracy 0.943 >= threshold 0.92."
```

Update this file as part of the promotion PR. The PR requires approval from a member
of the `@ml-approvers` GitHub team.

---

## Escalation and Override

A Production deployment may be blocked by the gate in exceptional circumstances
(e.g., urgent fix for a model with a live incident). In this case:

1. Open an override PR manually setting the model to Production stage.
2. The PR must include a written justification in the PR description.
3. Two approvals from `@ml-approvers` are required (instead of the usual one).
4. The override must be recorded in `approved-versions.yaml` with `override: true`.

---

## Related

- `policy/model-approval/approved-versions.yaml` — approval record
- `ci/github-actions/model-evaluation/evaluate.yml` — automated gate implementation
- `docs/golden-paths/model-registry.md` — model promotion workflow
- `monitoring/evidently/drift_report.py` — drift check script
