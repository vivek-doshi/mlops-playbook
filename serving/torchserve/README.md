# TorchServe

TorchServe is the recommended runtime for PyTorch models, especially when you
need custom pre/post-processing logic (e.g., image resizing, tokenisation,
output formatting) that cannot be expressed as a simple tensor transformation.

> **Beginner tip**: TorchServe packages your model into a single `.mar` file
> (Model ARchive). This archive contains the model weights, your Python handler
> code, and metadata. You upload the `.mar` file to TorchServe's model store, and
> TorchServe serves it via HTTP. Think of it as a `.zip` file for ML models with
> a built-in web server.

---

## MAR Packaging — Archiving Your Model

Use `torch-model-archiver` to create a `.mar` file:

```bash
# Install the archiver tool.
pip install torch-model-archiver

# Package the model.
# --model-name    : the name the API will use (e.g., POST /predictions/my-model)
# --version       : semantic version of this model release
# --serialized-file: the saved PyTorch model file (.pt or .pth)
# --handler       : custom Python handler (or a built-in: image_classifier, text_classifier, etc.)
# --extra-files   : any additional files your handler needs at runtime
# --export-path   : directory where the .mar file will be saved

torch-model-archiver \
  --model-name my-model \
  --version 1.0 \
  --serialized-file artifacts/model/model.pth \
  --handler handler.py \
  --extra-files "class_index.json,tokenizer.json" \
  --export-path model-store/

# Result: model-store/my-model.mar
```

### Writing a custom handler (handler.py)

```python
# handler.py — custom TorchServe handler.
# TorchServe calls: initialize → preprocess → inference → postprocess.
import json
import torch
from ts.torch_handler.base_handler import BaseHandler

class MyModelHandler(BaseHandler):
    """
    Custom TorchServe handler for my-model.

    The four methods below form the inference pipeline.
    Each method can be overridden independently.
    """

    def initialize(self, context):
        """
        Called once at startup. Load model weights and any supporting files.
        context.manifest contains model name, version, and runtime info.
        """
        super().initialize(context)
        # self.model is loaded by BaseHandler.initialize() from the .mar file.
        # Add custom post-init logic here if needed.

    def preprocess(self, data):
        """
        Transform raw HTTP request body into model input tensors.
        data is a list of dicts with a "body" key.
        """
        inputs = []
        for row in data:
            body = row.get("body") or row.get("data")
            features = json.loads(body) if isinstance(body, (str, bytes)) else body
            inputs.append(torch.tensor(features["features"], dtype=torch.float32))
        return torch.stack(inputs)   # batch dimension first

    def inference(self, data):
        """
        Run the model. data is the output of preprocess().
        """
        with torch.no_grad():
            return self.model(data)

    def postprocess(self, data):
        """
        Transform model output tensors into a JSON-serialisable list.
        """
        return [{"prediction": float(p)} for p in data.squeeze()]
```

---

## config.properties

See `serving/torchserve/config.properties` for the full server configuration file.

Key settings:

```properties
# Bind addresses — use 0.0.0.0 to accept connections from all interfaces.
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082

# Number of worker threads (tune based on CPU cores).
number_of_netty_threads=4

# Model store directory — where .mar files are stored.
model_store=/home/model-server/model-store

# Load all .mar files in model_store at startup.
load_models=all
```

---

## Docker Run Command

```bash
# Pull the official TorchServe image.
# Tags: latest-cpu (no GPU), latest-gpu (CUDA support)
docker run --rm \
  -p 8080:8080 \      # inference API
  -p 8081:8081 \      # management API
  -p 8082:8082 \      # Prometheus metrics
  -v $(pwd)/model-store:/home/model-server/model-store \
  -v $(pwd)/serving/torchserve/config.properties:/home/model-server/config.properties \
  pytorch/torchserve:latest-cpu \
  torchserve --start \
    --model-store /home/model-server/model-store \
    --ts-config /home/model-server/config.properties

# Check server health.
curl http://localhost:8080/ping
# Expected: { "status": "Healthy" }

# Send an inference request.
curl -X POST http://localhost:8080/predictions/my-model \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0, 4.0, 5.0]}'
```

---

## Kubernetes Deployment Notes

```yaml
# Kubernetes Deployment excerpt for TorchServe.
spec:
  template:
    spec:
      initContainers:
        # Init container downloads .mar files from object storage before
        # the main container starts. This avoids baking large models into images.
        - name: model-downloader
          image: amazon/aws-cli:latest
          command:
            - aws
            - s3
            - cp
            - s3://my-model-bucket/model-store/
            - /model-store/
            - --recursive
          volumeMounts:
            - name: model-store
              mountPath: /model-store

      containers:
        - name: torchserve
          image: pytorch/torchserve:latest-gpu
          ports:
            - containerPort: 8080
            - containerPort: 8082

          readinessProbe:
            httpGet:
              path: /ping
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10

          resources:
            requests:
              nvidia.com/gpu: "1"
            limits:
              nvidia.com/gpu: "1"
```

---

## Health and Metrics Endpoints

| Endpoint | Port | Description |
|----------|------|-------------|
| `GET /ping` | 8080 | Server health |
| `GET /metrics` | 8082 | Prometheus metrics |
| `GET /models` | 8081 | List loaded models |
| `POST /predictions/{model}` | 8080 | Run inference |

---

## Related

- `serving/torchserve/config.properties` — server configuration
- `docs/golden-paths/model-serving.md` — end-to-end deployment golden path
- `docs/guides/gpu-cost-governance.md` — GPU resource limits
