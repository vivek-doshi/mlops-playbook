# Local Setup Guide

This guide walks you through setting up the MLOps Playbook on a local Windows machine with an **NVIDIA RTX 5070 (12 GB VRAM, Blackwell)** and testing everything inside the Dev Container.

Two paths are documented side by side:

| Path | Best for |
|------|---------|
| **Dev Container** (recommended) | Consistent environment, GPU-accelerated vLLM/Triton, all tools pre-installed |
| **Bare-metal** | Faster cold start, no Docker overhead, simpler debugging |

---

## Hardware & OS Assumptions

| Component | Spec |
|-----------|------|
| GPU | NVIDIA GeForce RTX 5070 (Blackwell GB205, 12 GB GDDR7) |
| VRAM | 12 GB |
| CUDA compute capability | SM\_120 (Blackwell) |
| OS | Windows 11 22H2+ with WSL 2 |
| RAM | 32 GB+ recommended |
| Storage | 50 GB free (models + datasets + Docker layers) |

---

## Part 1 — Host Prerequisites

### 1.1 NVIDIA Driver

The RTX 5000 series (Blackwell) requires **driver ≥ 572.x** and **CUDA 12.8+**.

1. Open [https://www.nvidia.com/drivers](https://www.nvidia.com/drivers).
2. Select: **Product Type** = GeForce, **Series** = GeForce RTX 50 Series, **Product** = RTX 5070.
3. Download and install the Game Ready or Studio driver.
4. Verify after install:

```powershell
nvidia-smi
```

Expected output excerpt:

```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 572.xx    Driver Version: 572.xx    CUDA Version: 12.8                      |
+-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
|   0  NVIDIA GeForce RTX 5070  |   ...                | N/A                  |
+-------------------------------+----------------------+----------------------+
```

### 1.2 WSL 2

GPU passthrough into Docker containers requires WSL 2 (not WSL 1).

```powershell
# Install or upgrade WSL 2 (run as Administrator)
wsl --install
wsl --set-default-version 2

# Verify kernel version — must be 5.15+
wsl --version
```

### 1.3 Docker Desktop with GPU Support

1. Download **Docker Desktop ≥ 4.28** from [https://docker.com](https://docker.com).
2. In Docker Desktop → Settings → Resources → WSL Integration: enable your WSL distro.
3. In Settings → Docker Engine, confirm the default runtime is `runc`.

> **No manual NVIDIA Container Toolkit install needed on Windows.**
> Docker Desktop for Windows bundles the NVIDIA Container Toolkit automatically when the host driver supports CUDA 12.x.

Verify GPU access from Docker:

```powershell
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

You should see your RTX 5070 listed.

### 1.4 VS Code + Dev Containers Extension

```powershell
# Install VS Code (if not already installed)
winget install Microsoft.VisualStudioCode

# Install the Dev Containers extension
code --install-extension ms-vscode-remote.remote-containers
```

### 1.5 Git

```powershell
winget install Git.Git
git config --global core.autocrlf input   # keep LF line endings inside WSL/container
```

---

## Part 2 — Clone the Repository

```powershell
git clone https://github.com/your-org/mlops-playbook.git
cd mlops-playbook
```

> **Windows path tip:** Clone into a short path like `D:\projects\mlops-playbook` to avoid `MAX_PATH` issues with Python virtual environments.

---

## Part 3 — Dev Container Setup (Recommended)

The Dev Container gives you Python 3.11, DVC, MLflow, Terraform, kubectl, the GitHub CLI, and GPU-accelerated inference — all pre-installed and pre-configured.

### 3.1 GPU Support in the Dev Container

The `.devcontainer/devcontainer.json` is already configured to pass through your GPU using `--gpus all`. Verify the relevant section:

```json
"runArgs": ["--gpus", "all"]
```

> The container uses the host NVIDIA driver via the NVIDIA Container Toolkit. You do **not** install CUDA drivers inside the container — only the CUDA runtime libraries (already present in the base image features).

### 3.2 Open in Dev Container

1. Open VS Code in the project root:

   ```powershell
   code .
   ```

2. VS Code detects `.devcontainer/devcontainer.json` and shows a notification: **"Reopen in Container"**. Click it.

   Alternatively: `Ctrl+Shift+P` → **Dev Containers: Reopen in Container**.

3. The first build takes **3–5 minutes** as Docker pulls the base image and installs features. Subsequent opens take ~10 seconds.

4. Once inside the container, open the integrated terminal (`Ctrl+`` `).

### 3.3 Install Python Dependencies

```bash
task setup:dev
# or: make setup-dev
```

This installs MLflow 2.14.2, DVC, Evidently, pre-commit hooks, Black, Ruff, pytest, and pip-audit.

### 3.4 Verify GPU Inside the Container

```bash
# Should show RTX 5070 with 12 GB
nvidia-smi

# Verify PyTorch can see the GPU
python - <<'EOF'
import torch
print(f"CUDA available : {torch.cuda.is_available()}")
print(f"Device name    : {torch.cuda.get_device_name(0)}")
print(f"VRAM           : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
EOF
```

Expected output:

```
CUDA available : True
Device name    : NVIDIA GeForce RTX 5070
VRAM           : 12.0 GB
```

---

## Part 4 — MLflow Tracking Stack

### 4.1 Configure Environment Variables

```bash
cp mlflow/tracking-server/.env.example mlflow/tracking-server/.env
```

Edit `mlflow/tracking-server/.env`:

```dotenv
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=change-me-local
POSTGRES_DB=mlflow

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change-me-local
```

> Use strong passwords even locally — MLflow basic-auth is enabled and these credentials protect your experiment data.

### 4.2 Start the Stack

```bash
task mlflow:up
# or: make mlflow-up
```

Verify all three services are running:

```bash
task mlflow:ps
```

| Service | URL | Credential |
|---------|-----|-----------|
| MLflow UI | http://localhost:5000 | admin / (set in `.env`) |
| MinIO Console | http://localhost:9001 | minioadmin / (set in `.env`) |
| PostgreSQL | localhost:5432 | mlflow / (set in `.env`) |

### 4.3 Create the MinIO Bucket

MLflow needs an `mlflow` bucket to store artifacts. Create it once:

```bash
docker run --rm \
  --network mlops-playbook_default \
  -e MC_HOST_minio=http://minioadmin:change-me-local@minio:9000 \
  minio/mc:latest \
  mc mb minio/mlflow --ignore-existing
```

Or use the MinIO Console at http://localhost:9001 → **Buckets** → **Create Bucket** → name it `mlflow`.

---

## Part 5 — DVC Local Remote

For local development you do not need an S3 bucket. Configure a local filesystem remote:

```bash
# Inside the Dev Container or bare-metal
dvc remote add -d local /tmp/dvc-remote
dvc remote modify local url /tmp/dvc-remote

# Commit the config (the remote URL is safe to commit for local dev)
git add .dvc/config
git commit -m "chore(dvc): add local remote for dev"
```

---

## Part 6 — Run the Training Pipeline

```bash
# Pull data (no-op if using local remote with no data yet)
dvc pull --remote local || echo "No remote data yet — skipping pull"

# Reproduce the full pipeline
dvc repro

# View the run in MLflow
echo "Open http://localhost:5000 → experiment: model-training"
```

---

## Part 7 — GPU-Accelerated Inference (RTX 5070)

### 7.1 vLLM — Local LLM Serving

The RTX 5070 has 12 GB VRAM. Suitable models:

| Model | VRAM required | Command |
|-------|--------------|---------|
| Mistral-7B-Instruct (4-bit GPTQ) | ~6 GB | see below |
| Phi-3-mini-4k (fp16) | ~8 GB | see below |
| Llama-3.1-8B (4-bit AWQ) | ~5 GB | see below |

> **12 GB VRAM constraint**: Full fp16 7B models require ~14 GB. Use quantised (GPTQ/AWQ/GGUF) variants to fit within 12 GB.

```bash
cd serving/vllm

# Copy the env file and set your model + HuggingFace token
cp .env.example .env
# Edit .env:
#   MODEL_NAME=TheBloke/Mistral-7B-Instruct-v0.2-GPTQ
#   HF_TOKEN=hf_...
#   MAX_MODEL_LEN=4096
#   GPU_MEMORY_UTILISATION=0.85   # leave 15% headroom for RTX 5070

docker compose up
```

Smoke test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/models

curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ",
    "messages": [{"role": "user", "content": "What is MLOps?"}],
    "max_tokens": 200
  }' | python -m json.tool
```

### 7.2 Triton — Classical Model Serving

```bash
cd serving/triton

# Pull the Triton image (CUDA 12.8 compatible)
docker pull nvcr.io/nvidia/tritonserver:24.05-py3

# Start Triton with GPU
docker run --gpus all --rm -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  -v $(pwd)/model_repository:/models \
  nvcr.io/nvidia/tritonserver:24.05-py3 \
  tritonserver --model-repository=/models
```

Health check:

```bash
curl http://localhost:8000/v2/health/ready
# → {"ready":true}
```

### 7.3 GPU Memory Management

The RTX 5070 has unified 12 GB GDDR7. When running multiple services simultaneously:

| Service | Approximate VRAM |
|---------|-----------------|
| vLLM (Mistral-7B-GPTQ) | ~6 GB |
| Triton (ONNX ResNet-50) | ~0.5 GB |
| PyTorch training run | ~4–10 GB |
| OS / display | ~0.5 GB |

**Recommendation**: Do not run vLLM and a training job simultaneously on a 12 GB GPU. Stop vLLM before running `dvc repro train` if the model uses GPU.

```bash
# Check current VRAM usage
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
```

---

## Part 8 — Drift Monitoring (Local)

```bash
# Generate synthetic reference and current data for testing
python - <<'EOF'
import pandas as pd
import numpy as np

np.random.seed(42)
n = 1000
ref = pd.DataFrame({"feature_1": np.random.normal(0, 1, n), "feature_2": np.random.normal(5, 2, n)})
cur = pd.DataFrame({"feature_1": np.random.normal(0.5, 1.2, n), "feature_2": np.random.normal(5, 2, n)})

import os; os.makedirs("data/reference", exist_ok=True); os.makedirs("data/current", exist_ok=True)
ref.to_parquet("data/reference/train_features.parquet", index=False)
cur.to_parquet("data/current/today_features.parquet", index=False)
print("Sample data written.")
EOF

# Run the drift check
task drift-check
# or: make drift-check

# Open the HTML report
start reports/drift_report.html   # Windows
# xdg-open reports/drift_report.html  # Linux inside WSL
```

---

## Part 9 — Pre-commit Hooks

```bash
# Run all hooks against all files to verify the environment
task pre-commit:all
# or: make pre-commit
```

Expected output (first run downloads hooks — ~30 seconds):

```
trim trailing whitespace.......................Passed
fix end of files...............................Passed
check yaml.....................................Passed
black..........................................Passed
isort..........................................Passed
ruff...........................................Passed
...
```

---

## Part 10 — Bare-Metal Setup (No Docker)

Use this path if you cannot use Docker or want faster iteration without container overhead.

```powershell
# Windows PowerShell
.\scripts\bootstrap.ps1

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Start MLflow with SQLite backend (no PostgreSQL needed)
mlflow server `
  --host 127.0.0.1 `
  --port 5000 `
  --backend-store-uri sqlite:///mlflow.db `
  --default-artifact-root ./mlruns

# In another terminal: run the pipeline
dvc repro
```

> **Limitations of bare-metal path:**
> - No MinIO — artifacts stored locally in `mlruns/`.
> - No basic-auth — MLflow UI is unauthenticated.
> - No containerised serving — Triton/vLLM must be started separately.

---

## Troubleshooting

### `nvidia-smi` not found inside container

The Dev Container uses `--gpus all` to pass through the GPU. If `nvidia-smi` is missing:

1. Confirm Docker Desktop has GPU support enabled: Settings → General → "Use the WSL 2 based engine" must be checked.
2. Restart Docker Desktop after installing a new NVIDIA driver.
3. Run `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi` from PowerShell (outside the container) to verify host-level GPU access first.

### `CUDA out of memory` during training

```bash
# Check what is consuming VRAM
nvidia-smi

# Stop vLLM if running
task mlflow:down    # stops compose stack; vLLM runs separately
docker ps | grep vllm
docker stop <container-id>
```

### `dvc pull` fails with "remote not configured"

```bash
dvc remote list        # shows configured remotes
dvc remote add -d local /tmp/dvc-remote   # add local remote
```

### MLflow UI returns 401 Unauthorised

The stack runs with `--app-name basic-auth`. The default admin credentials must be set in the auth config volume. Check `mlflow/tracking-server/docker-compose.yml` for the volume mount path and ensure `basic_auth.ini` is present.

### Port conflicts (5000 already in use)

```powershell
# Find and kill the process using port 5000 on Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```

---

## Reference

| Resource | Link |
|---------|------|
| NVIDIA Blackwell driver downloads | https://www.nvidia.com/drivers |
| NVIDIA Container Toolkit (WSL) | https://docs.nvidia.com/cuda/wsl-user-guide |
| Docker Desktop GPU docs | https://docs.docker.com/desktop/gpu/ |
| Dev Containers spec | https://containers.dev |
| vLLM quantisation guide | https://docs.vllm.ai/en/latest/quantization/index.html |
| MLflow auth docs | https://mlflow.org/docs/latest/auth/index.html |
| DVC remote storage | https://dvc.org/doc/user-guide/data-management/remote-storage |
