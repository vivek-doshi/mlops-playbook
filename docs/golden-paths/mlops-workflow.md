# End-to-End MLOps Workflow

> **Golden Path** — This guide is the authoritative walkthrough for taking a raw dataset all the way through to a monitored, production-serving model using the tools in this playbook.

---

## Overview

The MLOps lifecycle consists of seven stages that feed into each other in a loop:

```
Data Versioning (DVC)
       │
       ▼
Experiment Tracking (MLflow)
       │
       ▼
CI Training Pipeline (GitHub Actions)
       │
       ▼
Model Registry & Approval Gate (MLflow + Policy)
       │
       ▼
Serving Deployment (Triton / TorchServe / vLLM)
       │
       ▼
Drift Monitoring (Evidently + Prometheus + Grafana)
       │
       └─── drift detected ──► Retraining Trigger
```

Each stage has its own golden path doc. This document shows how they connect.

---

## Stage 1: Data Versioning (DVC)

**Purpose**: Track every version of your training dataset and the code that produced it.

**Docs**: [`docs/golden-paths/data-versioning.md`](data-versioning.md)

### What to do

```bash
# 1. Add a new dataset version.
dvc add data/raw/features.csv

# 2. Commit the .dvc pointer to Git (not the data).
git add data/raw/features.csv.dvc .gitignore
git commit -m "feat(data): add features v2.3 (n=150000)"

# 3. Push data to remote storage (S3/GCS/Azure Blob).
dvc push
```

### Cross-stage link

The DVC hash written to `.dvc` files is captured by the training CI job and stored as an MLflow tag (`dvc_data_hash`). This creates a bidirectional lineage link: given any MLflow run, you can reconstruct the exact training data.

---

## Stage 2: Experiment Tracking (MLflow)

**Purpose**: Log every training run — parameters, metrics, artifacts — so experiments are reproducible.

**Docs**: [`docs/golden-paths/experiment-tracking.md`](experiment-tracking.md)

### What to do

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("fraud-detection")

with mlflow.start_run():
    mlflow.log_params({"learning_rate": 0.01, "max_depth": 6})
    mlflow.log_metric("accuracy", 0.943)
    mlflow.sklearn.log_model(model, "model")
    # Link to the DVC data used for this run.
    mlflow.set_tag("dvc_data_hash", open("data/raw/features.csv.dvc").read())
```

### Cross-stage link

The MLflow run ID is passed downstream to evaluation CI so metrics can be fetched without re-running training.

---

## Stage 3: CI Training Pipeline (GitHub Actions)

**Purpose**: Automate training so that every code change produces a versioned, logged experiment.

**Docs**: [`docs/golden-paths/model-training-pipeline.md`](model-training-pipeline.md)

**Workflow file**: [`ci/github-actions/model-training/train.yml`](../../ci/github-actions/model-training/train.yml)

### What triggers it

- Push to `main` branch.
- Manual dispatch with `environment` (dev/staging/prod) and `dvc_remote` inputs.

### What it produces

- A completed MLflow run with metrics, parameters, and artifacts.
- The `MLFLOW_RUN_ID` and `DVC_DATA_HASH` exported as GitHub Actions outputs for downstream jobs.

### Optional pre-check

Set input `run_drift_precheck: true` to run Evidently drift analysis on the new data **before** training starts. If drift is critical (>0.6), training is blocked and an alert is raised.

---

## Stage 4: Model Registry & Approval Gate

**Purpose**: Promote models through Staging → Production only after passing evaluation gates.

**Docs**: [`docs/golden-paths/model-registry.md`](model-registry.md), [`policy/model-approval/README.md`](../../policy/model-approval/README.md)

**Workflow file**: [`ci/github-actions/model-evaluation/evaluate.yml`](../../ci/github-actions/model-evaluation/evaluate.yml)

### Three evaluation gates

| Gate | Tool | Pass condition |
|------|------|----------------|
| Accuracy threshold | MLflow + sklearn | `accuracy ≥ threshold` tag from run |
| Drift check | Evidently | Drift score < 0.3 |
| Lineage verification | DVC | `dvc_data_hash` tag matches `.dvc` hash |

If all three pass, the model is promoted to `Staging` in the MLflow Model Registry.

### Production promotion

The deployment workflow ([`ci/github-actions/model-deployment/deploy.yml`](../../ci/github-actions/model-deployment/deploy.yml)) uses a GitHub `environment: production` gate — a designated reviewer must click **Approve** in the GitHub Actions UI before any Kubernetes resources are updated.

### PII models

If the training data contained PII, complete [`policy/data-governance/pii-model-checklist.md`](../../policy/data-governance/pii-model-checklist.md) and obtain DPO sign-off before promoting to Production.

---

## Stage 5: Serving Deployment

**Purpose**: Deploy the approved model to the correct runtime for its architecture.

**Docs**: [`docs/golden-paths/model-serving.md`](model-serving.md), [`serving/README.md`](../../serving/README.md)

**Workflow file**: [`ci/github-actions/model-deployment/deploy.yml`](../../ci/github-actions/model-deployment/deploy.yml)

### Choosing a runtime

```
Is it an LLM / generative model requiring OpenAI-compatible API?
  └── YES → vLLM      (serving/vllm/)
      NO  ↓
Does it use custom PyTorch .pt preprocessing / handlers?
  └── YES → TorchServe (serving/torchserve/)
      NO  ↓
        → Triton       (serving/triton/)     ← default for ONNX, TRT, multi-framework
```

### What the deploy job does

1. Verifies the model is in `Production` stage in MLflow registry.
2. Updates the Kubernetes Deployment image tag (`kubectl set env`).
3. Restarts the serving pod (`kubectl rollout restart`).
4. Waits for rollout to complete, then runs a health probe smoke test.

---

## Stage 6: Drift Monitoring

**Purpose**: Detect when the distribution of production data diverges from training data (data drift) or when model outputs change (target drift).

**Docs**: [`docs/golden-paths/model-monitoring.md`](model-monitoring.md), [`monitoring/README.md`](../../monitoring/README.md)

**Workflow file**: [`ci/github-actions/model-monitoring/drift-check.yml`](../../ci/github-actions/model-monitoring/drift-check.yml)

**Script**: [`monitoring/evidently/drift_report.py`](../../monitoring/evidently/drift_report.py)

### Scheduled daily check

```yaml
# Runs every day at 06:00 UTC.
on:
  schedule:
    - cron: "0 6 * * *"
```

### Thresholds

| Drift score | Action |
|------------|--------|
| < 0.3 | No action |
| 0.3 – 0.6 | Warning notification (Slack) |
| > 0.6 | Critical alert — blocks training pre-check, triggers retraining |

### Alerts

Prometheus alert rules are defined in [`monitoring/alerts/drift-alerts.yaml`](../../monitoring/alerts/drift-alerts.yaml). The Grafana dashboard at [`monitoring/dashboards/model-health.json`](../../monitoring/dashboards/model-health.json) visualises drift score history.

---

## Stage 7: Retraining Trigger

**Purpose**: Close the loop — when drift exceeds the critical threshold, automatically trigger a new training run.

### Automatic trigger

The drift monitoring workflow can dispatch the training workflow:

```yaml
- name: Trigger retraining on critical drift
  if: env.DRIFT_CRITICAL == 'true'
  uses: actions/github-script@v7
  with:
    script: |
      await github.rest.actions.createWorkflowDispatch({
        owner: context.repo.owner,
        repo: context.repo.repo,
        workflow_id: 'train.yml',
        ref: 'main',
        inputs: { run_drift_precheck: 'false' }  // drift already confirmed
      });
```

### What restarts the loop

1. New data arrives in the DVC remote (updated data version).
2. Training CI re-runs against the new dataset.
3. Evaluation gates re-run.
4. If gates pass, the updated model is promoted to Production.
5. Monitoring baseline resets to the new model's training data distribution.

---

## Cross-Repo Dependencies

This playbook depends on infrastructure provided by the platform repository (`devops-playbook` / `cicd-reference`):

| Dependency | Platform provides | This repo consumes |
|-----------|-------------------|--------------------|
| GPU cluster | `terraform/gpu-cluster/` in platform repo | `terraform/gpu-cluster/main.tf` references platform module |
| Kubernetes base manifests | Platform RBAC and namespaces | `kubectl set env` / `rollout restart` in deploy.yml |
| Secrets management | Vault / Kubernetes Secrets | `MLFLOW_TRACKING_URI`, `AWS_ACCESS_KEY_ID` etc. via GitHub Secrets |
| OIDC federation | Platform service accounts | Used by CI jobs to authenticate to cloud provider |
| KEDA scale-to-zero | Platform KEDA install | Serving deployments scale down when idle |

---

## Quick Reference

| Task | Command / File |
|------|----------------|
| Start MLflow stack | `cd mlflow/tracking-server && docker compose up -d` |
| Version dataset | `dvc add data/raw/ && dvc push` |
| Run training pipeline | `dvc repro train` |
| View experiments | `mlflow ui` → http://localhost:5000 |
| Promote model to Staging | Merge PR → evaluate.yml passes gates → auto-promotes |
| Deploy to Production | Trigger deploy.yml → approve GitHub environment gate |
| Check drift | `python monitoring/evidently/drift_report.py` |
| Security scan | Call `ci/github-actions/_shared/reusable-mlops-scan.yml` from your workflow |
