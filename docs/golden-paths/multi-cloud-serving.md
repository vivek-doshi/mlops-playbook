# Golden Path — Multi-Cloud Model Serving

Deploy a model to AWS SageMaker, GCP Vertex AI, and Azure ML simultaneously,
with weighted traffic routing and automatic failover.

---

## Prerequisites

- Model in **Production** stage in the MLflow Model Registry.
- Terraform applied for all three cloud modules:
  - `terraform/aws-sagemaker/`
  - `terraform/gcp-vertex-ai/`
  - `terraform/azure-ml/`
- Cloud credentials configured (see below).

---

## Step 1 — Deploy to All Three Clouds

```bash
# Via GitHub Actions
gh workflow run multi-cloud/deploy-multicloud.yml \
  -f model_name=my-classifier \
  -f model_version=3 \
  -f clouds=aws,gcp,azure
```

Or deploy manually to each cloud using the cloud-specific deploy scripts:

```bash
python ci/scripts/deploy_sagemaker.py --model-name my-classifier --model-version 3
python ci/scripts/deploy_vertex.py    --model-name my-classifier --model-version 3
python ci/scripts/deploy_azure_ml.py  --model-name my-classifier --model-version 3
```

---

## Step 2 — Create a Routing Config

```bash
cat > multi_cloud_serving/routing-config/my-classifier.yaml <<'EOF'
model_name: my-classifier
timeout_seconds: 30
endpoints:
  aws:
    url: https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/my-classifier/invocations
    weight: 0.40
    region: us-east-1
    runtime: sagemaker
  gcp:
    url: https://us-central1-aiplatform.googleapis.com/v1/.../predict
    weight: 0.40
    region: us-central1
    runtime: vertex-ai
  azure:
    url: https://my-classifier.eastus.inference.ml.azure.com/score
    weight: 0.20
    region: eastus
    runtime: azure-ml
EOF
```

Weights do not need to sum to 1.0 — the router normalises them.

---

## Step 3 — Route Predictions

```python
from multi_cloud_serving.router import MultiCloudRouter

router = MultiCloudRouter(model_name="my-classifier")
result = router.predict({"instances": [{"feature_1": 1.5, "feature_2": 0.3}]})
print(result)
# {'prediction': 1, '_serving_cloud': 'aws'}
```

---

## Step 4 — Monitor Health

```python
from multi_cloud_serving.registry import EndpointRegistry
from multi_cloud_serving.health_check import HealthChecker

registry = EndpointRegistry()
registry.refresh()

checker = HealthChecker(registry)
for status in checker.check_all():
    print(f"{status.cloud}: healthy={status.is_healthy}, latency={status.latency_ms}ms")
```

---

## Step 5 — Verify Failover with a Chaos Test

```bash
gh workflow run multi-cloud/failover-test.yml \
  -f model_name=my-classifier \
  -f disable_cloud=aws
```

The workflow will:
1. Set AWS weight to 0.
2. Send 100 requests.
3. Verify zero requests hit AWS.
4. Restore original weights.

---

## Step 6 — Shift Traffic (Canary / Cost Optimisation)

To shift traffic for cost optimisation, update the routing config weights and
commit the change.  The router picks up the new config on restart.

```yaml
# Reduce Azure weight to save cost (Azure more expensive for this workload)
endpoints:
  aws:   { weight: 0.50 }
  gcp:   { weight: 0.45 }
  azure: { weight: 0.05 }
```

---

## Step 7 — SLO Monitoring

Each cloud endpoint has its own SLO file:

```bash
# Add per-cloud SLO files
cp monitoring/slos/slo-template.yaml monitoring/slos/my-classifier-aws-slo.yaml
cp monitoring/slos/slo-template.yaml monitoring/slos/my-classifier-gcp-slo.yaml
cp monitoring/slos/slo-template.yaml monitoring/slos/my-classifier-azure-slo.yaml
```

Prometheus alerts for cross-cloud failover events are in
`monitoring/multi-cloud/cross-cloud-alerts.yaml`.

---

## Related Resources

- [ADR-ML-020 — Multi-Cloud Serving Strategy](../decisions/ADR-ML-020-multi-cloud-serving.md)
- [multi_cloud_serving/README.md](../../multi_cloud_serving/README.md)
- [ADR-ML-003 — Model Serving](../decisions/ADR-ML-003-model-serving.md)
