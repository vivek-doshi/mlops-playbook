# Triton Inference Server

NVIDIA Triton Inference Server is the recommended runtime for classical ML models
(sklearn, XGBoost), ONNX models, and TensorRT-optimised deep learning models.
It supports multiple backends, concurrent model execution, and dynamic batching.

> **Beginner tip**: Triton runs a standardised HTTP/gRPC API. Your model is stored
> in a "model repository" folder structure that Triton scans at startup. Each model
> has a config file (`config.pbtxt`) that tells Triton what backend to use (Python,
> ONNX, TensorRT) and the expected input/output shapes.

---

## Model Repository Layout

Triton expects this directory structure:

```
model_repository/
├── my-sklearn-model/
│   ├── config.pbtxt          ← model configuration (see config.pbtxt.example)
│   └── 1/                    ← version number directory (always start with 1)
│       └── model.py          ← Python backend entry point (for Python backend)
│                             ← OR model.onnx (for ONNX backend)
│                             ← OR model.plan (for TensorRT backend)
└── my-onnx-model/
    ├── config.pbtxt
    └── 1/
        └── model.onnx
```

> **Intermediate note**: Triton supports multiple model versions simultaneously.
> Directory `1/` is version 1, `2/` would be version 2. You configure in
> `config.pbtxt` which version(s) to serve and how to load-balance between them.

---

## config.pbtxt — Minimal Example (Python Backend)

See `serving/triton/config.pbtxt.example` for the full example.

For the Python backend, the entry point is a `TritonPythonModel` class:

```python
# model_repository/my-model/1/model.py
import json
import numpy as np
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    """
    Triton Python backend model class.
    Triton calls initialize() once at startup and execute() for every batch.
    """

    def initialize(self, args):
        """
        Called once when Triton loads the model.
        Load your model weights here to avoid reloading on every request.
        """
        import mlflow
        import os

        # Load from MLflow registry so the model always reflects the Production version.
        model_uri = os.environ.get("MODEL_URI", "artifacts/model")
        self.model = mlflow.pyfunc.load_model(model_uri)

    def execute(self, requests):
        """
        Called for every inference request (or batch of requests).
        Must return a list of pb_utils.InferenceResponse objects.
        """
        responses = []
        for request in requests:
            # Extract the input tensor by name (must match config.pbtxt INPUT0).
            input_tensor = pb_utils.get_input_tensor_by_name(request, "INPUT0")
            input_array = input_tensor.as_numpy()

            # Run model inference.
            output_array = self.model.predict(input_array)

            # Wrap the output in a Triton tensor and add to response.
            output_tensor = pb_utils.Tensor("OUTPUT0", output_array.astype(np.float32))
            responses.append(pb_utils.InferenceResponse(output_tensors=[output_tensor]))

        return responses
```

---

## Kubernetes Deployment Notes

Reference `devops-playbook/cd/kubernetes/_patterns/gpu-inference-deployment.yaml`
for the full Kubernetes Deployment manifest.

Key configuration points:

```yaml
# Deployment spec excerpt.
spec:
  template:
    spec:
      containers:
        - name: triton
          image: nvcr.io/nvidia/tritonserver:24.01-py3
          args:
            - tritonserver
            - --model-repository=/models
            - --log-verbose=1

          # Mount the model repository from an init container or persistent volume.
          volumeMounts:
            - name: model-repo
              mountPath: /models

          # Health probes — Triton takes time to load models at startup.
          readinessProbe:
            httpGet:
              path: /v2/health/ready
              port: 8000
            initialDelaySeconds: 60
            periodSeconds: 10

          resources:
            requests:
              nvidia.com/gpu: "1"
            limits:
              nvidia.com/gpu: "1"   # always set GPU limits (see docs/guides/gpu-cost-governance.md)
```

---

## Local Testing with Docker

```bash
# Start Triton with your model repository.
docker run --rm \
  -p 8000:8000 \   # HTTP endpoint
  -p 8001:8001 \   # gRPC endpoint
  -p 8002:8002 \   # Prometheus metrics
  -v $(pwd)/model_repository:/models \
  nvcr.io/nvidia/tritonserver:24.01-py3 \
  tritonserver --model-repository=/models

# Verify Triton is ready.
curl -X GET http://localhost:8000/v2/health/ready
# Expected response: 200 OK

# Send an inference request (HTTP JSON API).
curl -X POST http://localhost:8000/v2/models/my-model/infer \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [{
      "name": "INPUT0",
      "shape": [1, 10],
      "datatype": "FP32",
      "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    }]
  }'
```

---

## Health and Metrics Endpoints

| Endpoint | Port | Description |
|----------|------|-------------|
| `GET /v2/health/ready` | 8000 | Server ready (all models loaded) |
| `GET /v2/health/live` | 8000 | Server alive (process running) |
| `GET /v2/models/{model}/ready` | 8000 | Specific model loaded |
| `GET /metrics` | 8002 | Prometheus metrics |

---

## Related

- `serving/triton/config.pbtxt.example` — full config example
- `docs/golden-paths/model-serving.md` — end-to-end serving golden path
- `docs/guides/gpu-cost-governance.md` — GPU resource limits
