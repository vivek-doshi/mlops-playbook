# Model Serving Golden Path

## Purpose and Scope

Deploy a Production-stage model from the MLflow registry to a serving runtime,
following the platform deployment patterns. This guide covers the full path from
a registered model to a live HTTP endpoint.

> **Beginner tip**: "Serving" means making your trained model available as an API
> so other systems can send data and receive predictions. Instead of running a
> Jupyter notebook each time, you package the model into a container and deploy it
> to a Kubernetes cluster. The serving runtime (Triton, TorchServe, or vLLM) handles
> batching, GPU management, and scaling.

---

## Prerequisites

| Requirement | Where to configure |
|-------------|-------------------|
| Model in Production stage | `docs/golden-paths/model-registry.md` |
| Platform Kubernetes cluster running | `devops-playbook/docs/golden-paths/mlops-workflow.md` |
| Container registry credentials | GitHub Actions secrets: `REGISTRY_URL`, `REGISTRY_USERNAME`, `REGISTRY_TOKEN` |
| Serving runtime chosen | See runtime selection table below |

---

## Runtime Selection Guide

Choose the runtime based on your model type. All three runtimes have starter
configurations in the `serving/` directory.

| Use case | Runtime | Config location |
|----------|---------|----------------|
| Classical ML, tabular, sklearn, XGBoost, ONNX, TensorRT | Triton | `serving/triton/` |
| PyTorch models with custom pre/post-processing handlers | TorchServe | `serving/torchserve/` |
| LLMs, generative inference, OpenAI-compatible API | vLLM | `serving/vllm/` |

> **Intermediate note**: If you are unsure, start with Triton. Its Python backend
> supports almost any Python-based model and can be upgraded to ONNX or TensorRT
> later for performance without changing the API contract.

---

## Step-by-Step Implementation

### Step 1 — Confirm model is in Production stage

```python
import mlflow

# -----------------------------------------------------------------------
# Always verify the model stage before deploying.
# Deploying a Staging model to production is a common mistake.
# -----------------------------------------------------------------------
client = mlflow.tracking.MlflowClient()
versions = client.get_latest_versions("my-model", stages=["Production"])

if not versions:
    raise RuntimeError("No model in Production stage. Complete the approval process first.")

prod_version = versions[0]
print(f"Deploying my-model v{prod_version.version}")
print(f"  git_sha: {prod_version.tags.get('git_sha')}")
print(f"  accuracy: {prod_version.tags.get('eval_accuracy')}")
```

---

### Step 2 — Set environment variables for the serving container

```bash
# These two variables are required by the serving container at startup.
# They tell the container where to find the model in the MLflow registry.
export MODEL_URI="models:/my-model/Production"
export MLFLOW_TRACKING_URI="http://mlflow-server:5000"
```

In your Kubernetes Deployment manifest:

```yaml
env:
  - name: MODEL_URI
    value: "models:/my-model/Production"
  - name: MLFLOW_TRACKING_URI
    valueFrom:
      secretKeyRef:
        name: mlflow-secrets
        key: tracking_uri
```

---

### Step 3 — Build the serving container image

Reference `ci/github-actions/model-deployment/deploy.yml` for the full CI workflow.

The general pattern is:

```bash
# The serving image must include your serving runtime and the code
# to download/bake the model from the MLflow registry.
docker build \
  --build-arg MODEL_URI="models:/my-model/Production" \
  -t my-registry/my-model-server:${GIT_SHA} \
  serving/<runtime>/

docker push my-registry/my-model-server:${GIT_SHA}
```

---

### Step 4 — Apply Kubernetes manifests

```bash
# Apply the base serving workload from the platform repo pattern.
# The platform repo (devops-playbook) owns the base Kubernetes primitives.
kubectl apply -f kubernetes/serving/deployment.yaml
kubectl apply -f kubernetes/serving/service.yaml
kubectl apply -f kubernetes/serving/ingress.yaml
```

For GPU inference, add a GPU node selector to your deployment:

```yaml
# Add this to your Kubernetes Deployment spec.template.spec
nodeSelector:
  # This label is set on GPU nodes by the cluster provisioning in devops-playbook.
  nvidia.com/gpu: "true"

containers:
  - name: model-server
    resources:
      requests:
        nvidia.com/gpu: "1"
      limits:
        # Always set GPU limits — unbounded GPU use is a significant cost risk.
        # Reference: docs/guides/gpu-cost-governance.md
        nvidia.com/gpu: "1"
```

---

### Step 5 — Configure health probes

Health probes prevent traffic from being sent to a container that is still loading
the model (which can take minutes for large models).

```yaml
# Add to your Kubernetes container spec.
readinessProbe:
  httpGet:
    path: /v2/health/ready   # Triton endpoint; adjust for other runtimes
    port: 8000
  initialDelaySeconds: 60    # large models need time to load
  periodSeconds: 10
  failureThreshold: 6

livenessProbe:
  httpGet:
    path: /v2/health/live
    port: 8000
  initialDelaySeconds: 120
  periodSeconds: 30
```

Health endpoint per runtime:

| Runtime | Health endpoint |
|---------|----------------|
| Triton | `GET /v2/health/ready` |
| TorchServe | `GET /ping` |
| vLLM | `GET /health` |

---

## Serving Runtime Quick Reference

### Triton

See `serving/triton/README.md` for full setup. Key files:
- `serving/triton/config.pbtxt.example` — model config
- Model repository layout: `model_repository/<model-name>/1/model.<ext>`

### TorchServe

See `serving/torchserve/README.md` for full setup. Key files:
- `serving/torchserve/config.properties` — server config
- MAR package: `torch-model-archiver --model-name my-model --version 1.0 --handler handler.py`

### vLLM

See `serving/vllm/README.md` for full setup. Key files:
- `serving/vllm/docker-compose.yml` — local quickstart
- OpenAI-compatible endpoint: `POST /v1/completions`

---

## Rollback Procedure

```bash
# 1. Re-run the deployment workflow with the previous image tag.
#    In GitHub Actions, use workflow_dispatch and specify the old image tag.

# 2. Archive the bad model version in MLflow registry (see model-registry.md).

# 3. Verify the old serving endpoint is healthy.
curl -X GET http://your-serving-endpoint/v2/health/ready
```

---

## Validation

```bash
# Test the serving endpoint with a sample payload (Triton HTTP API example).
curl -X POST http://your-serving-endpoint/v2/models/my-model/infer \
  -H "Content-Type: application/json" \
  -d '{"inputs": [{"name": "INPUT0", "shape": [1, 10], "datatype": "FP32",
                   "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]}]}'

# vLLM OpenAI-compatible endpoint example.
curl http://your-serving-endpoint/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "my-llm", "prompt": "Hello, world!", "max_tokens": 50}'
```

---

## Related

- `serving/triton/README.md` — Triton server setup
- `serving/torchserve/README.md` — TorchServe setup
- `serving/vllm/README.md` — vLLM setup
- `docs/golden-paths/model-registry.md` — confirm Production stage before deploy
- `docs/golden-paths/model-monitoring.md` — monitor the deployed model
- `ci/github-actions/model-deployment/deploy.yml` — CI deployment workflow
- `docs/decisions/ADR-ML-003-model-serving.md` — why three runtimes
