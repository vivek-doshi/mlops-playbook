# Getting Started with the MLOps Playbook

Welcome! This guide walks you through your first end-to-end ML experiment — from
cloning the repo to viewing your model in the MLflow UI — in under 30 minutes.

---

## Prerequisites

| Tool | Minimum version | Install guide |
|------|----------------|----------------------|
| Python | 3.11 | https://python.org |
| Git | 2.40 | https://git-scm.com |
| DVC | 3.x | `pip install dvc[all]` |
| MLflow | 2.14 | `pip install mlflow` |
| Docker (for MLflow stack + serving) | 24 | https://docker.com |
| VS Code + Dev Containers extension | latest | https://code.visualstudio.com |
| kubectl (optional, for Kubernetes serving) | 1.28 | https://kubernetes.io/docs/tasks/tools |

> **GPU / RTX 5070 users** → see [docs/local-setup.md](docs/local-setup.md) for NVIDIA driver setup, Docker GPU passthrough, and running vLLM / Triton locally.

You do **not** need a cloud account for the local development path.
DVC will use a local directory as the remote, and MLflow will store artifacts locally.

---

## Recommended Setup: Dev Container

The fastest way to get a fully working environment is to open the repo in the included Dev Container. It ships Python 3.11, DVC, MLflow, Terraform, kubectl, GitHub CLI, and GPU passthrough pre-configured.

1. Install **Docker Desktop** ≥ 4.28 and the **Dev Containers** VS Code extension.
2. Clone the repo and open it in VS Code:

   ```powershell
   git clone https://github.com/your-org/mlops-playbook.git
   code mlops-playbook
   ```

3. VS Code shows: **“Reopen in Container”** — click it (or `Ctrl+Shift+P` → *Dev Containers: Reopen in Container*).
4. After the build completes (~3 min first time), run:

   ```bash
   task setup:dev
   ```

That’s it. Skip to [Step 2 — Pull Training Data](#step-2--pull-training-data) below.

For GPU-specific setup (RTX 5070, CUDA 12.8, vLLM, Triton), see the full guide: [docs/local-setup.md](docs/local-setup.md).

---

## Manual Bootstrap (Bare-Metal Alternative)

Skip this section if you are using the Dev Container (recommended above).

Run the bootstrap script to create the local environment, install dependencies,
and configure DVC and MLflow for local development:

**macOS / Linux:**
```bash
./scripts/bootstrap.sh
```

**Windows PowerShell:**
```powershell
.\scripts\bootstrap.ps1
```

The script creates:
- `.venv/` — Python virtual environment with all dependencies.
- `.dvc/config` — DVC configured with a local remote at `/tmp/dvc-remote`.
- `mlflow.db` — SQLite tracking database (development only).
- `mlruns/` — MLflow local artifact store.

---

## ML Lifecycle Quick Links

Use the table below to jump to the golden path guide for your current task.

| Task | Guide | Key tool |
|------|-------|---------|
| Log an experiment | [Experiment Tracking](docs/golden-paths/experiment-tracking.md) | `mlflow.log_params()` |
| Version a dataset | [Data Versioning](docs/golden-paths/data-versioning.md) | `dvc add`, `dvc push` |
| Build a training pipeline | [Training Pipeline](docs/golden-paths/model-training-pipeline.md) | `dvc repro` |
| Promote a model to production | [Model Registry](docs/golden-paths/model-registry.md) | `mlflow.register_model()` |
| Choose a serving runtime | [Model Serving](docs/golden-paths/model-serving.md) | Triton / TorchServe / vLLM |
| Monitor for data drift | [Model Monitoring](docs/golden-paths/model-monitoring.md) | Evidently AI |
| Promote model through environments | [Multi-env Promotion](docs/golden-paths/multi-env-promotion.md) | `promote-production.yml` |
| Run fairness evaluation | [Fairness & Explainability](docs/golden-paths/fairness-and-explainability.md) | `fairness/evaluate.py` |
| Run distributed training | [Distributed Training](docs/golden-paths/distributed-training.md) | `ray/train_distributed.py` |
| Run batch inference | [Batch Inference](docs/golden-paths/batch-inference.md) | `batch/runner/batch_scorer.py` |
| Track ML cost attribution | [ML Cost Attribution](docs/golden-paths/ml-cost-attribution.md) | `finops/scripts/` |
| Orchestrate ML pipelines | [Pipeline Orchestration](docs/golden-paths/pipeline-orchestration.md) | `pipelines/training_pipeline.py` |
| Deploy on Azure ML | [Model Serving](docs/golden-paths/model-serving.md) | `terraform/azure-ml/` |
| Understand repo concepts and lifecycle | [MLOps Concepts](docs/guides/concepts.md) | `docs/guides/concepts.md` |
| End-to-end overview | [MLOps Workflow](docs/golden-paths/mlops-workflow.md) | All of the above |

---

## Your First Experiment: 5 Steps

### Step 1 — Clone and Bootstrap

```bash
git clone https://github.com/your-org/mlops-playbook.git
cd mlops-playbook
./scripts/bootstrap.sh        # or bootstrap.ps1 on Windows
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
```

### Step 2 — Pull Training Data

The repository contains a small toy dataset pointer in `data/sample.dvc`.
Pull it to restore the actual Parquet file:

```bash
dvc pull data/sample.dvc
```

If you see a "cache miss" error, the DVC remote has not been configured yet.
For local development, initialise a local remote first:

```bash
dvc remote add -d local /tmp/dvc-remote
dvc push data/sample.dvc       # uploads from your working copy
dvc pull data/sample.dvc       # verify round-trip
```

### Step 3 — Run the Training Pipeline

```bash
# Run the full DVC pipeline (data prep → train → evaluate).
dvc repro

# Or run a single stage:
dvc repro train
```

The training script logs parameters and metrics to MLflow automatically.
Look for this in the terminal output:

```
MLflow run ID: abc123...
  logged param: learning_rate = 0.01
  logged metric: accuracy = 0.943
```

### Step 4 — View the Run in MLflow

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Open http://localhost:5000 in your browser.
Navigate to the **model-training** experiment and click the latest run.

You will see:
- **Parameters** tab: hyperparameters logged by the training script.
- **Metrics** tab: accuracy, loss, and any other metrics.
- **Artifacts** tab: the trained model binary.

### Step 5 — Promote the Model

Once you are satisfied with the metrics, register and promote the model to Staging:

```python
import mlflow

mlflow.set_tracking_uri("sqlite:///mlflow.db")
client = mlflow.tracking.MlflowClient()

# Register — creates a new version in the Model Registry.
model_info = mlflow.register_model(
    model_uri="runs:/abc123/model",    # replace with your run ID
    name="my-first-model"
)

# Promote to Staging.
client.transition_model_version_stage(
    name="my-first-model",
    version=model_info.version,
    stage="Staging"
)

print(f"Model v{model_info.version} is now in Staging.")
```

For Production promotion, the model must pass all three approval gates.
See [Model Registry](docs/golden-paths/model-registry.md) for the full flow.

---

## Next Steps

| I want to… | Go to… |
|-----------|-------|
| Add drift monitoring to my deployed model | [Model Monitoring](docs/golden-paths/model-monitoring.md) |
| Set up the local environment with GPU | [Local Setup Guide](docs/local-setup.md) |
| Understand architectural decisions | [docs/decisions/](docs/decisions/) |
| Set up CI for automated training | [ci/github-actions/](ci/github-actions/) |
| Deploy to Kubernetes | [Model Serving](docs/golden-paths/model-serving.md) |
| Understand data governance rules | [policy/data-governance/README.md](policy/data-governance/README.md) |

---

## Phase 2 Capabilities

After completing your first experiment, Phase 2 capabilities are available:

| Capability | Start here |
|---|---|
| Multi-environment promotion (dev→staging→prod) | [multi-env-promotion.md](docs/golden-paths/multi-env-promotion.md) |
| Fairness gates and explainability | [fairness-and-explainability.md](docs/golden-paths/fairness-and-explainability.md) |
| Distributed GPU training | [distributed-training.md](docs/golden-paths/distributed-training.md) |
| Batch inference at scale | [batch-inference.md](docs/golden-paths/batch-inference.md) |
| Cost attribution | [ml-cost-attribution.md](docs/golden-paths/ml-cost-attribution.md) |
| Pipeline DAG orchestration | [pipeline-orchestration.md](docs/golden-paths/pipeline-orchestration.md) |

---

## Getting Help

1. Check the relevant golden path guide in `docs/golden-paths/`.
2. Check the ADRs in `docs/decisions/` for rationale behind platform choices (9 records: ADR-ML-001 – ADR-ML-009).
3. Search the `monitoring/` and `policy/` directories for operational runbooks.
4. For GPU / local setup issues, see [docs/local-setup.md](docs/local-setup.md) § Troubleshooting.
5. Open a GitHub Issue using the issue template (select the appropriate category: bug, feature request, or model quality issue).
