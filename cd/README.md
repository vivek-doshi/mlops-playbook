# CD - Continuous Delivery for MLOps

## Purpose and Scope

This folder contains deployment orchestration assets for training, batch inference, and portal workloads.
It defines how artifacts produced in CI are promoted into Kubernetes environments and Argo-managed workflows.

## Folder Structure

- `argo/pipelines/`: Argo workflow definitions for training and batch inference execution
- `kubernetes/_base/`: Common Kubernetes base resources used by overlays
- `kubernetes/batch/`: Kubernetes `Job` and `CronJob` manifests for offline scoring
- `kubernetes/portal/`: Portal deployment, service, ingress, and network policy manifests
- `kubernetes/training/`: Distributed training resources (RayJob, PyTorchJob, TFJob, checkpoint PVC)
- `kubernetes/environments/`: Environment overlays (`dev`, `staging`, `production`) for progressive promotion

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
- Infrastructure: See [terraform/](../terraform/)
