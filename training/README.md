# Distributed Training Module

## Overview

This module provides distributed ML training support using three frameworks:

| Framework | CRD | Best for |
|---|---|---|
| **Ray** | `RayJob` (KubeRay) | Flexible, Python-first, RL, hyperparameter search |
| **PyTorch** | `PyTorchJob` (Kubeflow) | DDP fine-tuning, LLM training |
| **TensorFlow** | `TFJob` (Kubeflow) | TF ecosystem, multi-worker mirrored |

---

## Quick Start

### 1. Create a training config

```yaml
# training/config/my-model.yaml
model_name:          my-model
experiment_name:     my-model-dev
data_path:           data/features_train.parquet
checkpoint_dir:      /checkpoints
mlflow_tracking_uri: http://mlflow.mlflow.svc.cluster.local:5000
epochs:              20
batch_size:          512
learning_rate:       0.001
num_workers:         4
use_gpu:             true
```

### 2. Submit via GitHub Actions

```bash
gh workflow run distributed-training \
  --field model_name=my-model \
  --field framework=ray \
  --field num_workers=4 \
  --field use_gpu=true \
  --field environment=dev
```

### 3. Run locally (Ray)

```bash
ray start --head
python training/ray/train_distributed.py --config training/config/my-model.yaml
ray stop
```

---

## Framework Selection Guide

- **Use Ray** when you need flexibility (custom training loops, RL, HPO with Ray Tune).
- **Use PyTorch** (Kubeflow) when using Hugging Face Trainer or standard DDP.
- **Use TensorFlow** (Kubeflow) when using Keras `fit()` with multi-worker mirrored strategy.

---

## Checkpointing

All training scripts write checkpoints to `/checkpoints` via the shared PVC
(`checkpointing-pvc.yaml`).  The `CheckpointCallback` class in
`training/ray/checkpoint_callback.py` handles:

- Epoch-level checkpoint save
- `keep_last_n` pruning (default 3)
- `best/` symlink tracking
- Automatic Ray Train reporting

---

## Cost Controls

- GPU jobs always run through `gpu-approval-gate.yml`.
- Spot instances are used in dev; on-demand in production.
- All pods carry required cost labels for attribution.
- See `finops/budgets/` for per-model budget configuration.

---

## Security

- All containers run as non-root (UID 1000).
- `readOnlyRootFilesystem: false` is required for Ray/PyTorch because they write to `/tmp`.
  A dedicated `emptyDir` is mounted at `/tmp` for each pod.
- No container has `allowPrivilegeEscalation: true`.

---

## File Index

| Path | Description |
|---|---|
| `training/ray/train_distributed.py` | Ray Train distributed training entry-point |
| `training/ray/checkpoint_callback.py` | Checkpoint save/restore callback |
| `training/kubeflow/train_pytorch.py` | Kubeflow PyTorch DDP training script |
| `training/kubeflow/train_tf.py` | Kubeflow TFJob training script |
| `cd/kubernetes/training/ray-job.yaml` | KubeRay RayJob manifest |
| `cd/kubernetes/training/pytorch-job.yaml` | Kubeflow PyTorchJob manifest |
| `cd/kubernetes/training/tf-job.yaml` | Kubeflow TFJob manifest |
| `cd/kubernetes/training/checkpointing-pvc.yaml` | Shared checkpoint PVC |
| `ci/github-actions/distributed-training/distributed-train.yml` | CI workflow |
| `ci/github-actions/distributed-training/gpu-approval-gate.yml` | GPU approval gate |
| `terraform/ray-cluster/` | KubeRay operator Terraform module |
