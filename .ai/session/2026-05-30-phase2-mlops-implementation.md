# Session: Phase 2 MLOps Playbook — Full Implementation
Date: 2026-05-30

## Objective
Implement all Phase 2 workstreams from `.github/phase2-copilot-instructions.md`:
WS1 Multi-Environment Promotion, WS2 Fairness & Explainability, WS3 ML Cost Attribution,
WS4 Distributed Training, WS5 Batch Inference, WS6 Pipeline Orchestration.
This session completed WS3 (remaining), WS4 (all), WS5 (all), WS6 (all), and the outstanding WS3 Grafana dashboard.

---

## Workstream 3 — ML Cost Attribution (outstanding file)

| File | Purpose |
|------|---------|
| `finops/dashboards/ml-cost-attribution.json` | Grafana dashboard: total daily cost, cost by model, cost by team, cost by environment, GPU utilisation, untagged pods |

Prometheus metrics used: `ml_pod_cost_dollars_total`, `DCGM_FI_DEV_GPU_UTIL`, `kube_pod_labels`.

---

## Workstream 4 — Distributed Training (all 15 files)

| File | Purpose |
|------|---------|
| `cd/kubernetes/training/ray-job.yaml` | KubeRay RayJob manifest |
| `cd/kubernetes/training/pytorch-job.yaml` | Kubeflow PyTorchJob (DDP) |
| `cd/kubernetes/training/tf-job.yaml` | Kubeflow TFJob (MultiWorkerMirroredStrategy) |
| `cd/kubernetes/training/checkpointing-pvc.yaml` | PVC for checkpoint storage |
| `ci/github-actions/distributed-training/distributed-train.yml` | CI workflow for distributed training |
| `ci/github-actions/distributed-training/gpu-approval-gate.yml` | Manual approval gate for GPU spend |
| `training/ray/train_distributed.py` | Ray Train script with CheckpointCallback |
| `training/ray/checkpoint_callback.py` | Saves .pt + meta.json; keeps_last_n=3; best/ symlink |
| `training/kubeflow/train_pytorch.py` | PyTorchJob training script (DDP) |
| `training/kubeflow/train_tf.py` | TFJob training script |
| `training/README.md` | Distributed training module docs |
| `terraform/ray-cluster/main.tf` | Ray cluster Terraform (spot + on-demand node pools) |
| `terraform/ray-cluster/variables.tf` | Ray cluster variables |
| `docs/decisions/ADR-ML-016-distributed-training.md` | Hard merge gate ADR; KubeRay primary, Kubeflow secondary |
| `docs/golden-paths/distributed-training.md` | Step-by-step distributed training guide |

Key decisions:
- KubeRay (RayJob CRD) is primary; Kubeflow Training Operator is secondary.
- Spot nodes in dev/staging; on-demand in production.
- CheckpointCallback: keep_last_n=3, best/ symlink, Ray Train report integration.
- GPU approval gate required before any production GPU spend.

---

## Workstream 5 — Batch Inference (15 files)

| File | Purpose |
|------|---------|
| `batch/runner/batch_scorer.py` | Core scoring engine; MLflow pyfunc; chunk-based (10k rows default) |
| `batch/runner/input_validator.py` | Pre-score: schema, null rates, value ranges, row count |
| `batch/runner/output_quality_gate.py` | Post-score: prediction coverage, class distribution, score distribution |
| `batch/runner/downstream_notifier.py` | Slack / HTTP callback / Azure Event Grid notifications |
| `batch/jobs/_job-schema.yaml` | Job config schema template with inline docs |
| `batch/jobs/README.md` | Guide for creating batch job configs |
| `batch/README.md` | Batch inference module docs + architecture diagram |
| `cd/kubernetes/batch/batch-job.yaml` | K8s Job: one-shot batch run |
| `cd/kubernetes/batch/batch-cronjob.yaml` | K8s CronJob: scheduled daily 02:00 UTC |
| `ci/github-actions/batch/trigger-batch-job.yml` | Workflow: submit one-shot batch job |
| `ci/github-actions/batch/scheduled-batch.yml` | Workflow: scheduled wrapper |
| `ci/github-actions/batch/batch-quality-check.yml` | Reusable quality gate for CI |
| `monitoring/batch/batch-alerts.yaml` | Prometheus alerts: failed, stuck, missed schedule, high failure rate |
| `docs/golden-paths/batch-inference.md` | Step-by-step batch inference guide |
| `docs/decisions/ADR-ML-018-batch-inference.md` | Hard merge gate ADR; Python scripts on K8s Jobs |

Key decisions:
- MLflow pyfunc loading decouples runner from model framework.
- Chunk-based scoring (default 10k rows) limits peak memory.
- Pipeline: validate → score → quality-gate → notify.
- Batch pods: non-root, readOnlyRootFilesystem: false, emptyDir at /tmp.

---

## Workstream 6 — Pipeline Orchestration (18 files)

| File | Purpose |
|------|---------|
| `pipelines/components/data_ingestion/component.py` | Step 1: raw data download (S3/GCS/local); writes parquet |
| `pipelines/components/preprocessing/component.py` | Step 2: feature engineering, splits, StandardScaler |
| `pipelines/components/training/component.py` | Step 3: train sklearn model, log to MLflow |
| `pipelines/components/evaluation/component.py` | Step 4: test-split metrics (accuracy, F1, AUC, precision, recall) |
| `pipelines/components/registration/component.py` | Step 5: threshold gate + promote to Staging |
| `pipelines/components/deployment/component.py` | Step 6: promote to Production + optional kubectl rollout |
| `pipelines/training_pipeline.py` | End-to-end training pipeline (local mode) |
| `pipelines/batch_inference_pipeline.py` | Batch inference pipeline (local mode) |
| `pipelines/retraining_pipeline.py` | Drift-triggered conditional retraining with auto-promote |
| `pipelines/README.md` | Pipeline module docs + config template |
| `cd/argo/pipelines/training-workflow.yaml` | Argo Workflows DAG for training pipeline |
| `cd/argo/pipelines/batch-inference-workflow.yaml` | Argo Workflows DAG for batch inference |
| `ci/github-actions/pipelines/trigger-training-pipeline.yml` | CI: submit training pipeline via Argo |
| `ci/github-actions/pipelines/trigger-batch-inference.yml` | CI: submit batch inference pipeline via Argo (scheduled + manual) |
| `terraform/vertex-pipelines/main.tf` | Vertex AI Pipelines GCP resources (optional cloud backend) |
| `terraform/vertex-pipelines/variables.tf` | Vertex AI variables |
| `docs/golden-paths/pipeline-orchestration.md` | Step-by-step orchestration guide |
| `docs/decisions/ADR-ML-017-pipeline-orchestration.md` | Hard merge gate ADR; Argo Workflows primary |

Key decisions:
- Argo Workflows on Kubernetes is the primary production backend.
- GitHub Actions wraps Argo for CI-triggered runs.
- `--mode local` runs all components in-process for fast iteration.
- Vertex AI Pipelines (GCP) is an optional cloud backend.
- All components share identical interface: Python function + argparse CLI.
- Artifact passing via shared PVC (`/workspace/`).

---

## Invariants Maintained Throughout

- Every pod spec carries 4 cost labels: `cost-center`, `team`, `model-name`, `environment`.
- All workloads: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`.
- Pods that write /tmp: `readOnlyRootFilesystem: false` + emptyDir at /tmp.
- Every ADR is a hard merge gate — required before workstream PRs merge.
- Spot by default in dev/staging, on-demand in production.

---

## ADRs Added This Session

| ADR | Title |
|-----|-------|
| ADR-ML-016 | Distributed Training Framework (KubeRay primary) |
| ADR-ML-017 | Pipeline Orchestration (Argo Workflows primary) |
| ADR-ML-018 | Batch Inference Architecture (K8s Jobs + MLflow pyfunc) |
