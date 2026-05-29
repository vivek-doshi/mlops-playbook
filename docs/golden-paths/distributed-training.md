# Distributed Training Golden Path

## Purpose and Scope

This golden path describes how to run distributed ML training on Kubernetes using
Ray Train (default), PyTorchJob, or TFJob.

> **Beginner tip**: Distributed training splits model training across multiple
> GPU workers. It's faster for large models/datasets but costs more. Always
> test on a single node first and only scale when you hit a wall.

---

## Prerequisites

| Requirement | How to verify |
|---|---|
| KubeRay operator installed | `kubectl get pods -n kuberay-operator` |
| Kubeflow Training Operator (PyTorch/TF) | `kubectl get pods -n kubeflow` |
| Shared PVC available | `kubectl get pvc ml-training-checkpoints -n <namespace>` |
| Budget file exists | `ls finops/budgets/<model-name>.yaml` |

---

## Step 1: Create a Training Config

```bash
# Copy an example config.
cp training/config/example.yaml training/config/<model-name>.yaml
```

Edit the config:

```yaml
model_name:          fraud-detection
experiment_name:     fraud-detection-dev
data_path:           data/fraud_train.parquet
checkpoint_dir:      /checkpoints
mlflow_tracking_uri: http://mlflow.mlflow.svc.cluster.local:5000
epochs:              20
batch_size:          512
learning_rate:       0.001
num_workers:         4     # number of GPU workers
use_gpu:             true
```

---

## Step 2: Choose a Framework

| Workload type | Framework | CI input |
|---|---|---|
| New workloads, HPO, RL | Ray Train | `framework: ray` |
| Hugging Face Trainer, LLM fine-tuning | PyTorchJob | `framework: pytorch` |
| TensorFlow Keras `fit()` | TFJob | `framework: tensorflow` |

---

## Step 3: Submit via GitHub Actions

```bash
gh workflow run distributed-training \
  --field model_name=fraud-detection \
  --field framework=ray \
  --field num_workers=4 \
  --field use_gpu=true \
  --field environment=dev
```

For staging/production GPU jobs, you will be prompted for `@platform-infra-team`
approval. The CI step will pause at the `gpu-approval` environment gate.

---

## Step 4: Monitor Training

Watch pod status:

```bash
kubectl get pods -n fraud-detection-dev -w
```

Tail logs from a worker:

```bash
kubectl logs -n fraud-detection-dev -l model-name=fraud-detection -f
```

Check MLflow for metrics:

```
http://mlflow.mlflow.svc.cluster.local:5000/#/experiments/<ID>
```

---

## Step 5: Checkpoints

Training scripts save checkpoints to the shared PVC at `/checkpoints/epoch-NNNNN/`.
The `best/` symlink always points to the best checkpoint (by validation loss).

To restore from a checkpoint in a new run:

```python
from training.ray.checkpoint_callback import CheckpointCallback

callback = CheckpointCallback(checkpoint_dir="/checkpoints")
last_epoch = callback.restore(model, optimiser)
# Training continues from last_epoch + 1
```

---

## Step 6: Register the Model

After training completes, register the model in MLflow:

```python
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
result = mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="fraud-detection",
)
```

The promotion-gates workflow will then pick up the new version for evaluation.

---

## Cost Checklist

- [ ] Budget file exists at `finops/budgets/<model-name>.yaml`
- [ ] `num_workers` is the minimum needed (don't over-provision)
- [ ] Using spot nodes in dev (default)
- [ ] GPU approval gate acknowledged for staging/production

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Pod stuck in `Pending` | No GPU nodes available | Check `kubectl describe pod ...`; may need to scale up node pool |
| `NCCL error` | Network policy blocking worker-to-worker | Check `NetworkPolicy` in namespace |
| OOM in worker | `batch_size` too large | Halve `batch_size` |
| Ray head unreachable | Port 6379 blocked | Check `NetworkPolicy` allows Ray ports |
| Checkpoint dir not found | PVC not bound | `kubectl get pvc ml-training-checkpoints -n <ns>` |

---

## Further Reading

- `training/README.md` — module index and quick start
- `docs/decisions/ADR-ML-016-distributed-training.md` — framework selection rationale
- `docs/guides/gpu-cost-governance.md` — GPU cost controls
- `finops/` — budget files and cost attribution
