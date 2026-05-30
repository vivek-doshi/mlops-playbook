# Routing Config Directory

Place per-model traffic routing config files here.  Each file controls the traffic
split across AWS SageMaker, GCP Vertex AI, and Azure ML endpoints for one model.

## File Naming

Use `<model-name>.yaml` where `model-name` is the MLflow registered model name.

## Example

```yaml
# routing-config/my-classifier.yaml
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
    url: https://my-endpoint.eastus.inference.ml.azure.com/score
    weight: 0.20
    region: eastus
    runtime: azure-ml
```

## Schema

See `_config-schema.yaml` for the full JSON Schema.

## Rules

- Weights do not need to sum to exactly 1.0; the router normalises them.
- A weight of `0.0` disables a cloud without removing it from the config.
- Automatic failover temporarily zeroes out any cloud whose rolling 2-minute error
  rate exceeds 5%.  When the cloud recovers, restore its weight by redeploying the config.
