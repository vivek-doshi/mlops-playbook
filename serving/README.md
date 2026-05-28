# Model Serving

Three runtime patterns are supported. Choose based on your model type.

| Runtime | Best for | Directory |
|---------|----------|-----------|
| Triton Inference Server | Classical ML, tabular, multi-model, ONNX, TensorRT | `serving/triton/` |
| TorchServe | PyTorch models, custom pre/post-processing handlers | `serving/torchserve/` |
| vLLM | LLMs, generative inference, OpenAI-compatible API | `serving/vllm/` |

All serving workloads must be deployed through the platform Kubernetes base manifests
from `devops-playbook/cd/kubernetes/_base/`. See `docs/golden-paths/model-serving.md`
for the full deployment golden path.

## Quick Decision Guide

```
Is your model a large language model (> 1B parameters)?
  ├── YES → vLLM (serving/vllm/)
  └── NO
       Is your model a PyTorch model with custom Python logic?
         ├── YES → TorchServe (serving/torchserve/)
         └── NO  → Triton (serving/triton/) — supports Python, ONNX, TensorRT
```

## Common Prerequisites

- Model in `Production` stage in MLflow registry (see `docs/golden-paths/model-registry.md`)
- Kubernetes cluster with GPU nodes provisioned (see `devops-playbook/`)
- Container registry credentials configured
- `MODEL_URI` and `MLFLOW_TRACKING_URI` secrets available

## GPU Resource Requirements

All GPU serving pods must declare explicit resource limits.
Reference `docs/guides/gpu-cost-governance.md` for limit requirements and
cost tagging rules.

## Monitoring

After deployment, enable drift monitoring for the live endpoint.
See `docs/golden-paths/model-monitoring.md`.
