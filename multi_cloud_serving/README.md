# Multi-Cloud Serving

Route prediction traffic across AWS SageMaker, GCP Vertex AI, and Azure ML
with automatic failover, health monitoring, and cost normalisation.

## Architecture

```
Client request
      ↓
MultiCloudRouter (router.py)
  ├── reads per-model routing config from routing-config/<model>.yaml
  ├── selects cloud endpoint by weighted random choice
  ├── calls cloud endpoint
  ├── on error: records in rolling error-rate window
  └── triggers failover: shifts traffic from unhealthy endpoint proportionally

HealthChecker (health_check.py) — runs every 30 s
  ├── SageMaker:  GET /ping → 200
  ├── Vertex AI:  GET /v1/endpoints/<id> with GCP ADC
  └── Azure ML:   POST /score with Azure DefaultCredential

EndpointRegistry (registry.py) — reads Terraform outputs
  ├── terraform/aws-sagemaker/outputs.json
  ├── terraform/gcp-vertex-ai/outputs.json
  └── terraform/azure-ml/outputs.json
```

## Directory Map

```
multi_cloud_serving/
  router.py               ← Traffic routing + automatic failover
  registry.py             ← Endpoint catalog from Terraform outputs
  health_check.py         ← Per-cloud health probes
  routing-config/
    _config-schema.yaml   ← Schema for routing config files
    README.md
    <model-name>.yaml     ← Per-model traffic weights
  README.md
```

## Quick Start

### 1. Add a routing config

```bash
cat > multi_cloud_serving/routing-config/my-model.yaml <<'EOF'
model_name: my-model
timeout_seconds: 30
endpoints:
  aws:
    url: https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/my-model/invocations
    weight: 0.40
    region: us-east-1
    runtime: sagemaker
  gcp:
    url: https://us-central1-aiplatform.googleapis.com/v1/.../predict
    weight: 0.40
    runtime: vertex-ai
  azure:
    url: https://my-endpoint.eastus.inference.ml.azure.com/score
    weight: 0.20
    runtime: azure-ml
EOF
```

### 2. Route a prediction

```python
from multi_cloud_serving.router import MultiCloudRouter

router = MultiCloudRouter(model_name="my-model")
result = router.predict({"instances": [{"feature_1": 1.0}]})
print(result["_serving_cloud"])  # aws | gcp | azure
```

### 3. Check health

```python
from multi_cloud_serving.registry import EndpointRegistry
from multi_cloud_serving.health_check import HealthChecker

registry = EndpointRegistry()
registry.refresh()
checker = HealthChecker(registry)
for status in checker.check_all():
    print(status)
```

## Failover Behaviour

- Error rate is tracked in a rolling 2-minute window per endpoint.
- If a cloud's error rate exceeds **5%**, its traffic weight is set to 0 and
  traffic is redistributed proportionally to healthy endpoints.
- A `CrossCloudFailoverTriggered` Prometheus alert fires (see `monitoring/multi-cloud/`).
- Failover is logged as tag `multi_cloud_failover_at` on the active MLflow serving run.

## CI Integration

| Workflow | File |
|---|---|
| Deploy to all three clouds | `ci/github-actions/multi-cloud/deploy-multicloud.yml` |
| Failover chaos test | `ci/github-actions/multi-cloud/failover-test.yml` |

## Decision Record

See [ADR-ML-020](../docs/decisions/ADR-ML-020-multi-cloud-serving.md).
