# GPU Cost Governance Guide

## Purpose and Scope

Control GPU spend across training and serving workloads using FinOps controls.
GPU instances are the largest cost driver in ML workloads — an untagged or
unconstrained GPU job can exhaust a monthly budget in hours.

This guide covers tagging requirements, Kubernetes resource limits, approval gates,
auto-scaling, and reserved capacity decisions.

> **Beginner tip**: A single NVIDIA A100 GPU can cost $3–$10 per hour depending on
> cloud provider and region. A training job that runs longer than expected, or a
> serving deployment that never scales to zero, can produce a surprise bill.
> FinOps (Financial Operations) practices make GPU costs predictable and
> attributable to specific teams and models.

---

## 1. GPU Cost Tagging Requirements

Every GPU workload — training jobs, batch inference, and serving deployments —
**must** carry the following labels. This is enforced by the Kyverno policy in
`devops-playbook/policy/kyverno/require-resource-limits.yaml`.

| Label | Purpose | Example value |
|-------|---------|---------------|
| `cost-center` | Billing attribution to a business unit | `ml-platform` |
| `team` | Owning team for alerts and cost reports | `recommendations` |
| `model-name` | Model being trained or served | `fraud-detection-v2` |
| `environment` | Prevents production costs hidden under dev spend | `production` |

### Apply labels to Kubernetes workloads

```yaml
# In your Kubernetes Deployment or Job manifest.
metadata:
  name: fraud-detection-training
  labels:
    cost-center: "ml-platform"
    team: "recommendations"
    model-name: "fraud-detection-v2"
    environment: "dev"
```

### Apply labels to cloud training jobs

For AWS SageMaker (`terraform/aws-sagemaker/`):

```hcl
# terraform/aws-sagemaker/main.tf
resource "aws_sagemaker_training_job" "training" {
  # ...
  tags = {
    cost-center  = var.cost_center
    team         = var.team
    model-name   = var.model_name
    environment  = var.environment
  }
}
```

---

## 2. Kubernetes GPU Resource Limits

All GPU workloads on Kubernetes **must** declare both requests and limits for
`nvidia.com/gpu`. Deploying without limits means the container can consume all
GPUs on the node.

```yaml
# In your Kubernetes container spec.
resources:
  requests:
    # Requests are used for scheduling — the pod will only be placed on nodes
    # with at least this many GPUs available.
    cpu: "8"
    memory: "32Gi"
    nvidia.com/gpu: "1"
  limits:
    # Limits are the hard ceiling — the container cannot use more than this.
    # Always match GPU limits to GPU requests for GPUs (fractional GPU is not
    # natively supported by most runtimes).
    cpu: "16"
    memory: "64Gi"
    nvidia.com/gpu: "1"
```

> **Intermediate note**: Unlike CPU and memory, Kubernetes does not support
> fractional GPU allocation natively. Each GPU is allocated whole to one container.
> Tools like NVIDIA MPS or MIG (Multi-Instance GPU) allow sharing a single GPU
> between multiple workloads but require additional configuration.

The Kyverno policy that enforces these limits is maintained in:
`devops-playbook/policy/kyverno/require-resource-limits.yaml`.

---

## 3. GPU Approval Gate Pattern

Any workload requesting more than **2 GPUs** requires explicit approval before
deployment. This prevents accidentally launching expensive large-scale training
runs.

The approval gate policy file is at:
`devops-playbook/finops/policies/gpu-approval-gate.yaml`

### How the gate works

1. A developer opens a PR adding a GPU training job or serving deployment.
2. The CI pipeline checks `nvidia.com/gpu` resource requests in the manifests.
3. If the request exceeds 2 GPUs, the workflow requires approval from
   the `gpu-approvers` team before continuing.

```yaml
# ci/github-actions/_shared/reusable-mlops-scan.yml includes this check.
# Example gate logic:
- name: Check GPU approval requirement
  run: |
    python - << 'PY'
    import yaml, sys, glob

    MAX_GPUS_WITHOUT_APPROVAL = 2
    manifests = glob.glob("kubernetes/**/*.yaml", recursive=True)

    for path in manifests:
        with open(path) as f:
            doc = yaml.safe_load(f)
        # Traverse containers looking for GPU limits.
        containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        for container in containers:
            gpu_limit = int(
                container.get("resources", {}).get("limits", {}).get("nvidia.com/gpu", 0)
            )
            if gpu_limit > MAX_GPUS_WITHOUT_APPROVAL:
                print(f"BLOCKED: {path} requests {gpu_limit} GPUs. Approval required.")
                sys.exit(1)
    print("GPU limit check passed.")
    PY
```

---

## 4. Auto-Scaling and Scale-to-Zero for Inference

Serving workloads that receive no traffic should scale to zero to avoid paying
for idle GPU capacity. This is especially important in development and staging
environments.

Reference the scale-to-zero pattern from:
`devops-playbook/cd/kubernetes/_patterns/dev-scale-to-zero.yaml`

### KEDA-based scale-to-zero for serving

```yaml
# ScaledObject tells KEDA to scale the deployment based on Prometheus metrics.
# When prediction request rate drops to 0, the deployment scales to 0 replicas.
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: model-server-scaler
spec:
  scaleTargetRef:
    name: model-server
  minReplicaCount: 0        # scale to zero when idle
  maxReplicaCount: 4        # maximum replicas under load
  cooldownPeriod: 300       # wait 5 minutes before scaling down (model warm-up time)
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: http_requests_per_second
        threshold: "1"
        query: rate(serving_requests_total[2m])
```

> **Beginner tip**: Scale-to-zero means the serving deployment runs 0 pods when
> there are no requests. The first request after a period of inactivity will be
> slow (cold start) because Kubernetes needs to schedule a new pod and load the
> model. For user-facing APIs this is unacceptable, but for batch inference or
> internal APIs it saves significant cost.

### Minimum replicas per environment

| Environment | Min replicas | Rationale |
|-------------|-------------|-----------|
| dev | 0 | Scale to zero; cold start acceptable |
| staging | 1 | Always warm for integration tests |
| production | 2 | High availability; no cold start |

---

## 5. Spot / Preemptible Instances for Training

Training jobs are interruptible — if a spot instance is reclaimed, the job
can resume from a checkpoint. Use spot instances for all training workloads
unless you need a guaranteed completion time.

### AWS SageMaker Spot Training

```hcl
# terraform/aws-sagemaker/main.tf
resource "aws_sagemaker_training_job" "training" {
  # ...
  enable_managed_spot_training = true
  stopping_condition {
    max_run              = 86400   # 24 hour max wall clock
    max_wait_time_in_seconds = 172800  # 48 hour total wait (includes queuing)
  }
  # SageMaker handles checkpoint save/restore automatically with managed spot.
  checkpoint_config {
    s3_uri = "s3://${var.artifact_bucket}/checkpoints/"
  }
}
```

### Kubernetes Spot Node Pool

Add a spot node taint to your GPU training job:

```yaml
# In your Kubernetes Job or Pod spec.
tolerations:
  - key: "cloud.google.com/gke-spot"    # adjust for your cloud
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
nodeSelector:
  cloud.google.com/gke-spot: "true"
```

**Cost savings**: Spot/preemptible instances typically cost 60–90% less than
on-demand GPU instances. Always checkpoint model weights every epoch.

---

## 6. Reserved Capacity for Sustained Inference Workloads

For production serving workloads that run 24/7 with predictable load, reserved
capacity (1-year or 3-year commitment) significantly reduces costs.

Reference the reserved capacity advisor script:
`devops-playbook/finops/scripts/reserved-capacity-advisor.py`

### Decision framework

| Workload pattern | Recommendation |
|-----------------|----------------|
| Always-on production serving, stable load | Reserved instance (1-year) |
| Production serving with variable load | Mix: reserved for baseline, spot for burst |
| Training jobs, batch inference | Spot instances only |
| Development and experimentation | On-demand spot (no commitment) |

### Estimated savings (indicative, verify with current cloud pricing)

| Commitment | Discount vs on-demand |
|------------|----------------------|
| 1-year reserved | ~35% |
| 3-year reserved | ~55% |
| Spot instance | ~60–90% (variable, interruptible) |

---

## 7. GPU Cost Anomaly Alerts

Configure Prometheus alerts to catch unexpected GPU spend early.
The Prometheus configuration for the observability stack is in
`devops-playbook/finops/prometheus/`.

### Recommended alert rules

```yaml
# Add these rules to your Prometheus alert rules configuration.
groups:
  - name: gpu-cost-anomaly
    rules:
      # Alert if a GPU pod has been running for more than 8 hours.
      # Training jobs should complete; long-running jobs may be stuck.
      - alert: GPUJobRunningTooLong
        expr: |
          (time() - kube_pod_start_time{label_team!=""})
          * on(pod) group_left() kube_pod_container_resource_limits{resource="nvidia_com_gpu"}
          > 28800
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GPU pod {{ $labels.pod }} has been running for over 8 hours"
          description: "Team: {{ $labels.label_team }}. Check if the job is stuck."

      # Alert if GPU utilisation drops below 20% for a sustained period.
      # Low utilisation on a reserved GPU indicates wasted capacity.
      - alert: LowGPUUtilisation
        expr: |
          avg by (pod) (
            DCGM_FI_DEV_GPU_UTIL{kubernetes_pod_name!=""}
          ) < 20
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low GPU utilisation on {{ $labels.pod }}"
          description: "GPU utilisation below 20% for 30 minutes. Consider scaling down."
```

---

## Related

- `devops-playbook/policy/kyverno/require-resource-limits.yaml` — enforced GPU limits
- `devops-playbook/finops/policies/gpu-approval-gate.yaml` — large GPU approval
- `devops-playbook/cd/kubernetes/_patterns/dev-scale-to-zero.yaml` — scale-to-zero
- `devops-playbook/finops/scripts/reserved-capacity-advisor.py` — reserved capacity tool
- `devops-playbook/finops/prometheus/` — cost alert configuration
- `terraform/aws-sagemaker/` — SageMaker Terraform with spot configuration
- `terraform/gcp-vertex-ai/` — Vertex AI Terraform
