# Kubernetes - Kubernetes Patterns for MLOps

## Purpose and Scope

This folder contains Kubernetes resource definitions and patterns for MLOps workloads, including:

- **Batch Inference**: Offline scoring jobs and cronjobs
- **Training**: Distributed training resources (RayJob, PyTorchJob, TFJob)
- **Portal**: Portal deployment, service, ingress, and network policies
- **Environments**: Environment overlays for progressive promotion

## Folder Structure

- `batch/`: Kubernetes `Job` and `CronJob` manifests for offline scoring
- `training/`: Distributed training resources (RayJob, PyTorchJob, TFJob, checkpoint PVC)
- `portal/`: Portal deployment, service, ingress, and network policy manifests
- `environments/`: Environment overlays (`dev`, `staging`, `production`) for progressive promotion
- `_base/`: Common Kubernetes base resources used by overlays

## How to Use This as an Individual Component

1. **Choose a target workload** (`batch`, `training`, or `portal`)
2. **Render/apply manifests to a cluster**:
   - Base resources: `kubectl apply -k cd/kubernetes/_base`
   - Workload resources: `kubectl apply -f cd/kubernetes/<workload>/`
   - Optional env overlay: `kubectl apply -k cd/kubernetes/environments/<env>`
3. **For Argo-based execution, submit a workflow**:
   - `argo submit cd/argo/pipelines/training-workflow.yaml`
   - `argo submit cd/argo/pipelines/batch-inference-workflow.yaml`
4. **Validate rollout health**:
   - `kubectl get pods -A`
   - `kubectl get jobs,cronjobs -A`
   - `kubectl get ingress -A`

## Inputs and Outputs

- **Inputs**: Container images, model artifacts, environment-specific configuration
- **Outputs**: Deployed workloads, scheduled jobs, and production-ready runtime endpoints

## Related Resources

- Golden paths: See [docs/golden-paths/](../docs/golden-paths/)
- CI workflows: See [ci/github-actions/](../ci/github-actions/)
- CD workflows: See [cd/argo/pipelines/](../cd/argo/pipelines/)
