# 🤖 instruction-phase2.md — Jules Agent: MLOps Playbook Gap Fixes

## Agent Context

You are **Jules**, an autonomous coding agent powered by Gemini. You are working on the **mlops-playbook** repository — a production-ready MLOps starter template. Phase 1 built the skeleton. **Phase 2 is your responsibility**: fix all critical gaps, broken behaviors, and missing foundational files identified in the gap analysis.

Work through each task below **in order**. Each task is self-contained. Complete one fully before moving to the next. Commit after each task with a conventional commit message.

---

## Ground Rules

- **Never hardcode secrets, URIs, or file paths** — use environment variables or config files
- **Never use `print()` in production code** — use the existing `src/utils/logger.py`
- **All Python must pass flake8** (max line length 127, max complexity 10)
- **Every new function needs a docstring and type hints**
- **Do not modify `tests/test_core.py`** — add new test files for new functionality
- **Prefer editing existing files over creating new ones** where the change belongs there
- If you are unsure about a design decision, **choose the simpler option** and add a `# TODO:` comment

---

## Task 1 — Pin all dependencies in `requirements.txt`

**Why:** Unpinned deps are a reproducibility risk — the core antipattern this playbook exists to prevent.

**What to do:**

1. In the repo root, run a fresh `pip install` of the existing `requirements.txt` inside a clean virtualenv.
2. Run `pip freeze` to capture the full resolved dependency tree.
3. Replace the contents of `requirements.txt` with pinned versions for **direct dependencies only** (not the full transitive tree). Use `==` for all packages.
4. Add a comment block at the top of `requirements.txt`:

```
# Direct dependencies — pinned for reproducibility.
# To upgrade: edit versions here, then run: pip install -r requirements.txt
# Last pinned: <date>
```

5. Verify the existing CI workflow (`ci.yml`) still installs cleanly with the pinned file.

**Packages to pin (find the correct current stable versions):**
`pandas`, `scikit-learn`, `pydantic`, `mlflow`, `fastapi`, `uvicorn`, `pytest`, `pyyaml`, `httpx`, `hydra-core`, `flake8`, `joblib`, `omegaconf`, `optuna`

---

## Task 2 — Fix the inference cold-start crash

**File:** `src/inference/api.py`

**Why:** The current code loads models at module import time. If `models/model.pkl` does not exist (fresh clone, no training run yet), the app crashes with an unhandled exception and leaves `model`/`feature_pipeline` as undefined names. Any subsequent call to `/predict` raises a `NameError`, not a clean HTTP error.

**What to do:**

1. Replace the bare top-level `joblib.load()` calls with a FastAPI **lifespan** context manager using `asynccontextmanager`. Store the loaded model and pipeline in `app.state`.

2. Add a module-level `MODEL_LOADED: bool = False` flag that is set to `True` only when both artifacts load successfully.

3. Update `/predict` to check `app.state` for the model. If `MODEL_LOADED` is `False`, raise `HTTPException(status_code=503, detail="Model not loaded. Run the training pipeline first.")`.

4. Update `/health` to return model load status:
```json
{"status": "ok", "model_loaded": true}
```

5. Add a new **`/readiness`** endpoint that returns `200` only if `MODEL_LOADED` is `True`, otherwise `503`. This is the endpoint a K8s `readinessProbe` should use.

**Target structure:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # load model and pipeline into app.state here
    yield
    # cleanup if needed

app = FastAPI(title="MLOps Playbook Inference API", version="1.0", lifespan=lifespan)
```

6. Add tests for the `503` case to a new file `tests/test_api_resilience.py`. Mock the model load to fail and assert that `/predict` returns 503, not 500 or a crash.

---

## Task 3 — Multi-stage Dockerfile

**File:** `Dockerfile`

**Why:** The current single-stage Dockerfile ships pip, build tools, and compiler artifacts into the production image. This contradicts the `instructions.md` requirement for a multi-stage build.

**What to do:**

Replace the existing `Dockerfile` with a two-stage build:

**Stage 1 — builder:**
- Base: `python:3.12-slim`
- Install all dependencies from `requirements.txt` into `/install`
- Use `pip install --no-cache-dir --prefix=/install`

**Stage 2 — runtime:**
- Base: `python:3.12-slim` (fresh, no pip cache)
- Copy only `/install` from the builder stage
- Copy `src/` and `models/` (models dir as empty — populated at runtime via volume)
- Set `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
- Create a non-root user `appuser` and run as that user
- `EXPOSE 8000`
- `CMD ["uvicorn", "src.inference.api:app", "--host", "0.0.0.0", "--port", "8000"]`

Add a `.dockerignore` file to the repo root if it does not already exist, excluding:
```
.git
.venv
__pycache__
*.pyc
*.pyo
mlruns/
mlruns.db
data/raw/*
data/processed/*
notebooks/
tests/
```

---

## Task 4 — Fix CI: decouple training from PR checks

**File:** `.github/workflows/ci.yml`

**Why:** Running a full training pipeline on every push and PR is slow, wasteful, and a bad pattern to teach. The training step should be conditional.

**What to do:**

1. Split the single workflow into **two jobs**:

   - **`lint-and-test`** — runs on every push and PR to `main`. Contains: checkout, Python setup, dependency install, flake8, data ingestion, unit tests. Does **not** run training.

   - **`train-and-build`** — runs only on **push to `main`** (not PRs) OR on manual `workflow_dispatch`. Contains: checkout, Python setup, dependency install, training pipeline, Docker build.

2. The training step in `train-and-build` should have a `continue-on-error: false` and a timeout:
```yaml
timeout-minutes: 10
```

3. Add `workflow_dispatch` as a trigger at the top level so the training job can be triggered manually from the GitHub UI.

4. Add a step to `train-and-build` that uploads the trained model artifacts as a GitHub Actions artifact (so they can be inspected without Docker):
```yaml
- name: Upload model artifacts
  uses: actions/upload-artifact@v4
  with:
    name: model-artifacts
    path: models/
    retention-days: 7
```

5. Add the `PYTHONPATH: .` env var at the **job level** (not per-step) in both jobs to reduce repetition.

**Final trigger matrix:**
| Event | lint-and-test | train-and-build |
|---|---|---|
| PR to main | ✅ | ❌ |
| Push to main | ✅ | ✅ |
| workflow_dispatch | ❌ | ✅ |

---

## Task 5 — Add `.env.example` and environment variable documentation

**Why:** There is no documented record of what environment variables the project uses. Anyone cloning this has to grep the codebase.

**What to do:**

1. Create `.env.example` in the repo root:

```bash
# ─── MLOps Playbook — Environment Variables ───────────────────────────────────
# Copy this file to .env and fill in your values.
# .env is gitignored. Never commit real secrets.

# ── Inference API ──────────────────────────────────────────────────────────────
MODEL_PATH=models/model.pkl
PIPELINE_PATH=models/feature_pipeline.pkl

# ── MLflow ─────────────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI=sqlite:///mlruns.db
MLFLOW_EXPERIMENT_NAME=churn_prediction

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
LOG_FILE=mlops.log

# ── Optional: Remote MLflow (uncomment for production) ────────────────────────
# MLFLOW_TRACKING_URI=http://mlflow-server:5000
# MLFLOW_S3_ENDPOINT_URL=https://s3.amazonaws.com
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
```

2. Update `src/inference/api.py` and `pipelines/training_pipeline.py` to read `MLFLOW_TRACKING_URI` and `MLFLOW_EXPERIMENT_NAME` from environment variables as fallbacks (the config file values take precedence if provided; env vars are the default):

```python
import os
tracking_uri = config.get("mlflow", {}).get("tracking_uri") or os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db")
```

3. Ensure `.env` (not `.env.example`) is in `.gitignore`. It likely already is — verify and add if missing.

---

## Task 6 — Add `Makefile`

**Why:** A Makefile is the single highest-leverage developer experience improvement. It replaces reading the README for every common operation.

**Create `Makefile` in the repo root:**

```makefile
.PHONY: help install ingest train serve test lint docker-build docker-up clean

PYTHON := python
PIP    := pip
CONFIG := configs/config.yaml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	$(PIP) install -r requirements.txt

ingest: ## Run data ingestion pipeline
	PYTHONPATH=. $(PYTHON) pipelines/data_ingestion.py

train: ## Run training pipeline
	PYTHONPATH=. $(PYTHON) pipelines/training_pipeline.py --config $(CONFIG)

train-hydra: ## Run training pipeline with Hydra config
	PYTHONPATH=. $(PYTHON) pipelines/training_pipeline_hydra.py

serve: ## Start the inference API (requires trained model)
	PYTHONPATH=. uvicorn src.inference.api:app --reload --host 0.0.0.0 --port 8000

test: ## Run all tests
	PYTHONPATH=. pytest tests/ -v

lint: ## Run flake8 linter
	flake8 src/ pipelines/ tests/ monitoring/ \
		--count --max-complexity=10 --max-line-length=127 --statistics

docker-build: ## Build the Docker image
	docker build -t mlops-inference:latest .

docker-up: ## Start all services via docker-compose
	docker-compose up --build

docker-down: ## Stop all docker-compose services
	docker-compose down

clean: ## Remove generated artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f mlops.log app.log
	rm -f mlruns.db

clean-models: ## Remove trained model artifacts (forces retrain)
	rm -f models/*.pkl models/*.joblib
	@echo "Model artifacts removed. Run 'make train' to regenerate."

run-all: ingest train ## Run full pipeline end-to-end (ingest → train)
```

---

## Task 7 — Add pre-commit configuration

**Why:** CI catches lint errors after the fact. Pre-commit catches them before commit, which is faster and teaches better habits.

**Create `.pre-commit-config.yaml` in the repo root:**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.12
        args: ['--line-length=127']

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=127']

  - repo: https://github.com/PyCQA/flake8
    rev: 7.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=127', '--max-complexity=10']
        additional_dependencies: [flake8-bugbear]
```

Add `pre-commit` to `requirements.txt`.

Add a `Makefile` target:
```makefile
pre-commit-install: ## Install pre-commit hooks into git
	pre-commit install
```

Add a note in the README `Getting Started` section:
```bash
# Install pre-commit hooks (one-time setup)
make pre-commit-install
```

---

## Task 8 — Add `notebooks/` directory with EDA stub

**Why:** The README references `notebooks/` as the exploration directory but it does not exist.

**What to do:**

1. Create `notebooks/` directory with a `README.md`:

```markdown
# Notebooks

Exploratory notebooks for the MLOps Playbook reference dataset.

| Notebook | Purpose |
|---|---|
| `01_eda.ipynb` | Exploratory data analysis on the synthetic churn dataset |
| `02_feature_engineering.ipynb` | Feature importance and engineering experiments |
| `03_model_comparison.ipynb` | Compare RandomForest vs baseline models |

> These notebooks are for exploration only. Production logic lives in `src/` and `pipelines/`.
```

2. Create `notebooks/01_eda.ipynb` as a valid Jupyter notebook (JSON format). The notebook should contain:

- **Cell 1 (markdown):** Title and description — "EDA: Synthetic Churn Dataset"
- **Cell 2 (code):** Imports — `pandas`, `matplotlib`, `seaborn`, `sys`, `os`; set `PYTHONPATH` via `sys.path.insert`
- **Cell 3 (code):** Load data using `generate_synthetic_data` from `src.data.make_dataset`; display `df.head()` and `df.describe()`
- **Cell 4 (code):** Class balance plot — `df['target'].value_counts().plot(kind='bar')`
- **Cell 5 (code):** Feature correlation heatmap using seaborn
- **Cell 6 (markdown):** Observations placeholder — "## Key Observations\n\n- TODO: fill in after running"

3. Add `jupyter` and `seaborn` to `requirements.txt`.

4. Add to `.gitignore`:
```
# Jupyter outputs (keep notebooks, ignore outputs)
notebooks/.ipynb_checkpoints/
```

---

## Task 9 — Add `MODEL_CARD.md` template

**Why:** A Model Card is a standard MLOps artifact with no equivalent in DevOps playbooks. Including a template teaches the practice and makes this playbook distinctive.

**Create `MODEL_CARD.md` in the repo root:**

```markdown
# Model Card — [Model Name]

> Fill this in after training. Commit one MODEL_CARD.md per registered model version.
> Reference: [Mitchell et al. 2019](https://arxiv.org/abs/1810.03993)

---

## Model Details

| Field | Value |
|---|---|
| Model type | RandomForestClassifier (sklearn) |
| Version | 1.0.0 |
| Training date | YYYY-MM-DD |
| Framework | scikit-learn |
| MLflow run ID | (paste run ID from mlflow ui) |

## Intended Use

- **Primary use:** Binary classification — predicting customer churn
- **Intended users:** Data scientists, ML engineers
- **Out-of-scope uses:** Real-time fraud detection, medical decisions, any high-stakes automated decision-making without human review

## Training Data

| Field | Value |
|---|---|
| Dataset | Synthetic churn dataset (sklearn `make_classification`) |
| Size | 1,000 samples |
| Features | 10 numeric features (5 informative, 2 redundant) |
| Target | Binary (0 = retained, 1 = churned) |
| Class balance | ~50/50 (configurable) |
| Data version | See `data/raw/.gitkeep` — use DVC in production |

## Evaluation Metrics

| Metric | Value |
|---|---|
| Accuracy | |
| Precision | |
| Recall | |
| F1 | |
| ROC-AUC | |

> Fill in after running `make train`. Values logged to MLflow.

## Ethical Considerations

- This model is trained on **synthetic data** and should not be used for real decisions without retraining on validated real-world data
- No demographic features are present in the training data
- Feature importance should be reviewed before production deployment to check for proxy discrimination

## Caveats and Recommendations

- Retrain on real customer data before any production use
- Establish a drift detection baseline using `monitoring/drift_detection.py`
- Set a performance threshold below which the model triggers a retraining alert
- Validate that training distribution matches inference distribution (train/serve skew)
```

---

## Task 10 — Add `CONTRIBUTING.md`

**Create `CONTRIBUTING.md` in the repo root:**

```markdown
# Contributing to MLOps Playbook

Thank you for contributing. This is a starter template — contributions should make it
**clearer, more correct, or more useful for engineers building production ML systems**.

---

## Setup

```bash
git clone https://github.com/vivek-doshi/mlops-playbook
cd mlops-playbook
python -m venv .venv && source .venv/bin/activate
make install
make pre-commit-install
```

## Workflow

1. Fork the repo and create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes (see coding standards below)
3. Run `make lint` and `make test` — both must pass
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new functionality
   - `fix:` bug fixes
   - `docs:` documentation only
   - `refactor:` code change with no behaviour change
   - `test:` test additions or fixes
   - `chore:` tooling, deps, config
5. Open a PR against `main` with a clear description of what and why

## Coding Standards

- Python 3.12+, type hints on all functions
- PEP8, max line length 127
- `logging` not `print`
- Config-driven — no hardcoded paths or values
- Every new module needs at least one unit test
- Pre-commit hooks must pass before pushing

## What Makes a Good Contribution

- Adds a **new MLOps pattern** (e.g. feature store integration, online learning, canary deployment)
- Fixes a **documented gap** (see `instruction-phase2.md`)
- Improves **developer experience** (Makefile targets, docs, examples)
- Keeps it **simple** — this is a learning template, not a framework

## What to Avoid

- Framework lock-in without a clear alternative documented
- Adding dependencies that don't have a strong reason
- Monolithic scripts
- Skipping tests
```

---

## Commit Strategy

After completing each task, commit with:

```
fix(task-N): <short description>
```

Examples:
```
fix(task-1): pin all direct dependencies in requirements.txt
fix(task-2): fix inference cold-start crash with lifespan handler
fix(task-3): replace single-stage dockerfile with multi-stage build
fix(task-4): decouple training from pr checks in ci workflow
chore(task-5): add .env.example and document all env variables
chore(task-6): add Makefile with standard dev targets
chore(task-7): add pre-commit config with black, isort, flake8
docs(task-8): add notebooks directory with eda stub
docs(task-9): add MODEL_CARD.md template
docs(task-10): add CONTRIBUTING.md
```

After all tasks are complete, open a single PR titled:

```
feat: phase 2 — fix critical gaps and missing foundational files
```

---

## Verification Checklist

Before marking Phase 2 complete, verify:

- [ ] `pip install -r requirements.txt` succeeds with no version conflicts
- [ ] `make run-all` completes end-to-end without errors
- [ ] `make serve` starts without crashing even if `models/` is empty
- [ ] `GET /health` returns `{"status": "ok", "model_loaded": false}` on cold start
- [ ] `POST /predict` returns `503` (not crash) when model is not loaded
- [ ] `GET /readiness` returns `503` on cold start, `200` after training
- [ ] `make test` passes all tests including new resilience tests
- [ ] `make lint` passes with zero errors
- [ ] Docker image builds successfully with `make docker-build`
- [ ] CI workflow triggers correctly: lint+test on PR, train+build on main push only
- [ ] `.env.example` covers all env vars used in the codebase
- [ ] `notebooks/01_eda.ipynb` runs top-to-bottom without errors
- [ ] `MODEL_CARD.md` and `CONTRIBUTING.md` are present at repo root
- [ ] Pre-commit hooks install and pass on a test commit

---

## Out of Scope for Phase 2

The following are **not** part of this phase. They will be addressed in Phase 3:

- Optuna hyperparameter tuning integration
- Evidently drift detection (replacing the stub)
- Prometheus + Grafana monitoring stack
- MLflow model registry promotion step
- GitHub Container Registry image push in CI
- HorizontalPodAutoscaler in K8s manifest
- Batch prediction endpoint
```
