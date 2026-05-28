# vLLM

vLLM is the recommended runtime for large language models (LLMs). It provides an
OpenAI-compatible HTTP API, making it a drop-in replacement for the OpenAI API for
locally-hosted or self-managed models.

> **Beginner tip**: vLLM uses a technique called "PagedAttention" that dramatically
> improves GPU memory efficiency for language models. This means you can serve larger
> models or handle more concurrent requests with the same GPU hardware. It exposes
> a `/v1/completions` and `/v1/chat/completions` endpoint that is compatible with
> the OpenAI Python SDK — so existing code that calls OpenAI can switch to vLLM
> with a single URL change.

---

## Local Quickstart with Docker Compose

See `serving/vllm/docker-compose.yml` for the full configuration.

```bash
# Copy and edit the environment file.
cp serving/vllm/.env.example serving/vllm/.env

# Set your model name and HuggingFace token (if using a gated model).
# MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
# HF_TOKEN=hf_...

# Start vLLM locally.
cd serving/vllm
docker compose up

# Test the OpenAI-compatible completions endpoint.
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "prompt": "The capital of France is",
    "max_tokens": 20,
    "temperature": 0.0
  }'

# Test the chat completions endpoint (for instruction-tuned models).
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "What is MLOps?"}],
    "max_tokens": 200
  }'
```

---

## Loading a Model from HuggingFace Hub

```bash
# vLLM downloads the model from HuggingFace Hub on first startup.
# Set HF_TOKEN for gated models (Llama, Gemma, etc.).
export HF_TOKEN=hf_your_token_here
export MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.3

docker run --rm \
  --gpus all \
  -p 8000:8000 \
  -e HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}" \
  -v ~/.cache/huggingface:/root/.cache/huggingface \   # cache downloaded weights
  vllm/vllm-openai:latest \
  --model "${MODEL_NAME}" \
  --port 8000 \
  --dtype auto \
  --max-model-len 4096
```

---

## Loading a Model from MLflow Artifact Store

For models registered and versioned through the MLflow registry:

```python
# scripts/download_model_from_mlflow.py
# Run this in an init container before vLLM starts.
import mlflow
import os

TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]
MODEL_URI = os.environ.get("MODEL_URI", "models:/my-llm/Production")
LOCAL_PATH = "/models/llm"

mlflow.set_tracking_uri(TRACKING_URI)
mlflow.artifacts.download_artifacts(artifact_uri=MODEL_URI, dst_path=LOCAL_PATH)
print(f"Model downloaded to {LOCAL_PATH}")
```

Then start vLLM with the local path:

```bash
vllm serve /models/llm --port 8000
```

---

## Kubernetes Deployment Notes

vLLM requires a GPU node. Add the following to your Deployment manifest:

```yaml
spec:
  template:
    spec:
      # Use an init container to download the model weights before vLLM starts.
      initContainers:
        - name: model-downloader
          image: python:3.11-slim
          command:
            - python
            - /scripts/download_model_from_mlflow.py
          env:
            - name: MLFLOW_TRACKING_URI
              valueFrom:
                secretKeyRef:
                  name: mlflow-secrets
                  key: tracking_uri
            - name: MODEL_URI
              value: "models:/my-llm/Production"
          volumeMounts:
            - name: model-storage
              mountPath: /models

      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          command:
            - vllm
            - serve
            - /models/llm        # path where init container wrote the model
            - --port
            - "8000"
          ports:
            - containerPort: 8000

          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            # LLMs take several minutes to load — give enough time.
            initialDelaySeconds: 180
            periodSeconds: 15
            failureThreshold: 20

          resources:
            requests:
              nvidia.com/gpu: "1"
            limits:
              # vLLM benefits from more GPU memory for larger context windows.
              # Adjust based on your model size and required context length.
              # See docs/guides/gpu-cost-governance.md for cost implications.
              nvidia.com/gpu: "1"
              memory: "32Gi"

          volumeMounts:
            - name: model-storage
              mountPath: /models

      volumes:
        - name: model-storage
          emptyDir:
            medium: Memory   # use RAM-backed volume for faster model loading
```

---

## OpenAI SDK Compatibility

Because vLLM exposes an OpenAI-compatible API, you can use the official
OpenAI Python SDK by changing only the `base_url`:

```python
from openai import OpenAI

# Point the OpenAI client at your vLLM deployment instead of api.openai.com.
client = OpenAI(
    base_url="http://your-vllm-service:8000/v1",
    api_key="not-required",   # vLLM does not require an API key by default
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": "Explain data drift in ML."}],
    max_tokens=300,
)
print(response.choices[0].message.content)
```

---

## Health and API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Server health |
| `GET /v1/models` | List loaded models |
| `POST /v1/completions` | Text completion |
| `POST /v1/chat/completions` | Chat completion (instruction models) |
| `GET /metrics` | Prometheus metrics |

---

## Related

- `serving/vllm/docker-compose.yml` — local quickstart
- `docs/golden-paths/model-serving.md` — end-to-end serving golden path
- `docs/guides/gpu-cost-governance.md` — GPU resource limits for LLMs
