# ADR-ML-016: Distributed Training Framework Strategy

**Status**: Accepted  
**Date**: 2026-01-01  
**Deciders**: ML Platform Team  
**Category**: Hard Merge Gate — required before any distributed training PR merges  

---

## Context

As model complexity grows, single-node training becomes a bottleneck. We need a
distributed training strategy that:

1. Supports PyTorch, TensorFlow, and Ray-based workloads.
2. Runs on Kubernetes alongside existing model serving infrastructure.
3. Provides fault tolerance via checkpointing.
4. Integrates with existing MLflow experiment tracking.
5. Enforces GPU cost controls consistent with ADR-ML-003 (model serving) and the
   finops workstream.

---

## Decision

### Primary: KubeRay (Ray Train) for new workloads

New model training workloads default to **Ray Train** via the **KubeRay operator**
(RayJob CRD). Reasons:

- Python-first API; no YAML template changes for most experiments.
- Integrates natively with Ray Tune for hyperparameter optimisation.
- Elastic training and autoscaling via `minReplicas`/`maxReplicas`.
- Single operator covers training, serving, and batch inference use cases.

### Secondary: Kubeflow Training Operator for framework-specific workloads

**PyTorchJob** and **TFJob** are supported via the Kubeflow Training Operator for:
- Teams using Hugging Face Trainer (PyTorch DDP — standard in LLM fine-tuning).
- Existing TensorFlow pipelines using `tf.distribute.MultiWorkerMirroredStrategy`.

### Not adopted: Horovod standalone, DeepSpeed as a framework

DeepSpeed is supported as a *library* inside PyTorchJob workers (via
`deepspeed` Python package), not as a separate CRD. Horovod was evaluated but
rejected due to MPI dependency complexity on Kubernetes.

---

## Framework Selection Matrix

| Criterion | Ray Train | PyTorchJob | TFJob |
|---|---|---|---|
| Kubernetes operator | KubeRay | Kubeflow Training Op | Kubeflow Training Op |
| Primary framework | Agnostic | PyTorch DDP | TF MultiWorkerMirrored |
| HPO support | Native (Ray Tune) | Manual / Optuna | Manual |
| Fault tolerance | Elastic workers | restartPolicy | restartPolicy |
| Checkpoint API | `ray.train.Checkpoint` | Custom / HF Trainer | Keras callbacks |
| MLflow integration | Rank-0 logging | Rank-0 logging | Chief logging |
| Spot node support | Yes (elastic) | Yes (restartPolicy) | Yes (restartPolicy) |

---

## GPU Cost Controls

- All GPU training jobs run through `gpu-approval-gate.yml`.
- Spot nodes by default in dev/staging; on-demand requires explicit opt-in + approval.
- Estimated GPU cost printed in CI before job submission.
- Monthly GPU cost checked against `finops/budgets/<model-name>.yaml`.

---

## Consequences

### Positive
- Unified operator (KubeRay) reduces operational overhead for most teams.
- Checkpointing standardised via `CheckpointCallback` reduces duplicated code.
- GPU cost gate prevents surprise bills.

### Negative
- Teams must install KubeRay operator; Kubeflow operator for PyTorch/TF workloads.
- Two operators in the cluster increases RBAC complexity (mitigated by Terraform module).
- PyTorchJob and TFJob do not support elastic scaling; fixed replica counts at job submission.

---

## Related Decisions

- ADR-ML-003: Model serving (vLLM/Triton) — same GPU node pool reused for training.
- ADR-ML-006: Terraform for infrastructure — `terraform/ray-cluster/` provisions KubeRay.
- ADR-ML-009: Pre-commit toolchain — `training/*.py` files must pass Black/Ruff/Bandit.
