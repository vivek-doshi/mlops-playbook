# GitHub Copilot Instructions — MLOps Playbook (Phase 3 + Gap Fixes)

## Model Configuration

```json
{
  "github.copilot.chat.models": {
    "default": "claude-sonnet-4-6"
  }
}
```

---

## Repository Identity

This is a **production-oriented MLOps playbook** — an opinionated, copy-paste-ready
reference for building, deploying, and operating ML systems at org scale.

### Phase Completion Status

| Phase | Status | Summary |
|---|---|---|
| Foundation | ✅ Complete | MLflow, DVC, Evidently, CI/CD, three serving runtimes, governance |
| Phase 1 | ✅ Complete | CT pipeline, metadata store, shadow/A/B deploy, feature store (Feast), model cards, serving SLOs |
| Phase 2 | ✅ Complete | Multi-env promotion, fairness/explainability, distributed training (Ray+Kubeflow), pipeline orchestration (Argo), ML cost attribution, batch inference |
| **Phase 3** | 🔄 In progress | Online learning, multi-cloud serving, model optimisation, LLMOps, self-service portal, federated learning |

### Integration Bridge (non-negotiable)

The two repos are not islands. You create a deliberate, documented dependency.

- **Platform layer** (`devops-playbook` / `cicd-reference`): GPU cluster, Kubernetes base
  manifests, secrets management, OIDC federation, Kyverno policies, observability stack,
  cost dashboards, Argo Workflows operator, KubeRay operator.
- **ML lifecycle layer** (this repo): everything ML — experiments, registry, serving,
  monitoring, governance, and all Phase 1 + Phase 2 + Phase 3 additions.

Never move platform concerns into this repo. Never skip the Integration Bridge when
generating deployment or infrastructure code.

---

## SECTION A — Phase 1 and Phase 2 Gaps to Close First

These are items identified as missing or incomplete after reviewing the full
repository state. Close them **before** starting any Phase 3 workstream.

---

### Gap 1: `Makefile` and `Taskfile.yml` — Missing Phase 2 Targets

The `Makefile` and `Taskfile.yml` were not updated when Phase 2 workstreams were
added. They still only reference Foundation-era targets.

**Files to update:**
- `Makefile`
- `Taskfile.yml`

**Add these targets/tasks (follow existing style exactly):**

```
# Makefile additions
tf-validate-azure:        ## Validate Azure ML Terraform module
tf-plan-azure:            ## Plan Azure ML Terraform changes
fairness-check:           ## Run fairness evaluation locally (requires MLFLOW_RUN_ID + MODEL_VERSION)
distributed-train:        ## Submit a distributed Ray training job (requires CONFIG + FRAMEWORK)
batch-run:                ## Run a one-shot batch inference job locally (requires JOB_CONFIG)
batch-validate:           ## Validate batch job config YAML against schema
cost-daily:               ## Run daily cost attribution
cost-weekly:              ## Generate weekly cost report
cost-monthly:             ## Generate monthly chargeback report
promote-dev:              ## Trigger dev promotion workflow via gh CLI
promote-staging:          ## Trigger staging promotion workflow via gh CLI
rollback:                 ## Trigger rollback workflow (requires MODEL_NAME + ENV + REASON)
```

```
# Taskfile.yml additions (mirror Makefile additions)
tf:validate:azure
tf:plan:azure
fairness:check
distributed:train
batch:run
batch:validate
finops:daily
finops:weekly
finops:monthly
promote:dev
promote:staging
rollback
```

**Rules:**
- All new `Makefile` targets must have `## <description>` comment for `make help`.
- All new `Taskfile.yml` tasks must have `desc:` field.
- Azure Terraform targets follow same pattern as `tf-validate-sagemaker` and `tf-validate-vertex`.
- Fairness, batch, and finops targets delegate to the scripts already in the repo.

---

### Gap 2: `dependabot.yml` — Missing Phase 2 Dependencies and Azure ML Module

**File to update:** `.github/dependabot.yml`

**Add these missing ecosystems/directories:**

```yaml
# Azure ML Terraform module
- package-ecosystem: "terraform"
  directory: "/terraform/azure-ml"
  schedule:
    interval: "weekly"
    day: "thursday"
    time: "06:00"
    timezone: "UTC"
  labels: ["dependencies", "terraform", "azure"]
  groups:
    azure-providers:
      patterns: ["hashicorp/azurerm*", "hashicorp/azuread*"]

# Ray cluster Terraform module
- package-ecosystem: "terraform"
  directory: "/terraform/ray-cluster"
  schedule:
    interval: "weekly"
    day: "thursday"
  labels: ["dependencies", "terraform", "ray"]

# Vertex AI Pipelines Terraform module
- package-ecosystem: "terraform"
  directory: "/terraform/vertex-pipelines"
  schedule:
    interval: "weekly"
    day: "thursday"
  labels: ["dependencies", "terraform", "gcp"]

# Phase 2 Python dependencies — shap, fairlearn, ray, azure-ai-ml
# Add to the existing pip entry's groups:
#   fairness:
#     patterns: ["fairlearn*", "shap*"]
#   ray:
#     patterns: ["ray*"]
#   azure-ml:
#     patterns: ["azure-ai-ml*", "azure-identity*", "azure-storage*"]
```

**Rules:**
- Use the same schedule, label, and commit-message conventions as existing entries.
- Group related providers to reduce PR noise.
- Do not remove existing entries — only add.

---

### Gap 3: `GETTING_STARTED.md` — Missing Phase 2 Quick Links

**File to update:** `GETTING_STARTED.md`

**Add to the ML Lifecycle Quick Links table:**

| Task | Guide | Key tool |
|---|---|---|
| Promote model through environments | Multi-env Promotion | `promote-production.yml` |
| Run fairness evaluation | Fairness & Explainability | `fairness/evaluate.py` |
| Run distributed training | Distributed Training | `ray/train_distributed.py` |
| Run batch inference | Batch Inference | `batch/runner/batch_scorer.py` |
| Track ML cost attribution | ML Cost Attribution | `finops/scripts/` |
| Orchestrate ML pipelines | Pipeline Orchestration | `pipelines/training_pipeline.py` |
| Deploy on Azure ML | Model Serving | `terraform/azure-ml/` |

**Also add a Phase 2 "Next Steps" section** at the bottom:

```markdown
## Phase 2 Capabilities

After completing your first experiment, Phase 2 capabilities are available:

| Capability | Start here |
|---|---|
| Multi-environment promotion (dev→staging→prod) | [multi-env-promotion.md](docs/golden-paths/multi-env-promotion.md) |
| Fairness gates and explainability | [fairness-and-explainability.md](docs/golden-paths/fairness-and-explainability.md) |
| Distributed GPU training | [distributed-training.md](docs/golden-paths/distributed-training.md) |
| Batch inference at scale | [batch-inference.md](docs/golden-paths/batch-inference.md) |
| Cost attribution | [ml-cost-attribution.md](docs/golden-paths/ml-cost-attribution.md) |
| Pipeline DAG orchestration | [pipeline-orchestration.md](docs/golden-paths/pipeline-orchestration.md) |
```

**Rules:**
- Match the existing table formatting exactly.
- Do not restructure the document — only add rows and sections.
- Link paths must be relative and must exist in the repo.

---

### Gap 4: `README.md` — Missing Phase 2 Capabilities in "What's Implemented"

**File to update:** `README.md`

The "What's Implemented" section ends at Phase 1. Add a **Phase 2** subsection after
the existing content:

```markdown
### Phase 2 — Production Hardening

- **Multi-environment promotion** — structured dev/staging/production Kubernetes namespaces
  with Kustomize overlays, ResourceQuotas, NetworkPolicies, PodDisruptionBudgets, and
  approval gates: `cd/kubernetes/environments/`, `ci/github-actions/promotion/`
- **Fairness & explainability** — Fairlearn bias metrics, SHAP explainability reports,
  CI fairness gate with configurable per-model thresholds: `fairness/`, `policy/fairness/`
- **ML cost attribution** — pod-level cost labelling, per-model budget files,
  daily/weekly/monthly reports, Grafana dashboard: `finops/`, `monitoring/dashboards/ml-cost-attribution.json`
- **Distributed training** — KubeRay (primary) and Kubeflow PyTorchJob/TFJob (secondary),
  spot node pools, CheckpointCallback, GPU approval gate: `training/`, `cd/kubernetes/training/`
- **Batch inference** — MLflow pyfunc scorer, input validator, output quality gate,
  downstream notifier, Kubernetes Job/CronJob: `batch/`, `cd/kubernetes/batch/`
- **Pipeline orchestration** — Argo Workflows DAGs, reusable Python components,
  drift-triggered retraining pipeline, optional Vertex AI backend:
  `pipelines/`, `cd/argo/`, `terraform/vertex-pipelines/`
- **Architecture Decisions** — ADR-ML-014 through ADR-ML-018 in `docs/decisions/`
```

Also update the **Terraform** section to add Azure ML:

```markdown
- Azure ML Terraform (workspace, compute clusters, online endpoint, ADLS Gen2):
  [`terraform/azure-ml/`](terraform/azure-ml/)
```

---

### Gap 5: ADR Index — `docs/decisions/README.md` Does Not Exist

The `.ai/retrieval/retrieval-rules.md` and architecture overview reference
`docs/decisions/README.md` as the ADR index, but this file does not exist.

**File to create:** `docs/decisions/README.md`

```markdown
# Architecture Decision Records

All ML lifecycle ADRs for the MLOps Playbook. ADRs are numbered ML-NNN and
record the context, decision, alternatives considered, consequences, and review
triggers for each architectural choice.

## Index

| ADR | Title | Status |
|---|---|---|
| [ADR-ML-001](ADR-ML-001-experiment-tracking.md) | MLflow as Experiment Tracking | Accepted |
| [ADR-ML-002](ADR-ML-002-data-versioning.md) | DVC for Data Versioning | Accepted |
| [ADR-ML-003](ADR-ML-003-model-serving.md) | Three-Runtime Serving Strategy | Accepted |
| [ADR-ML-004](ADR-ML-004-drift-monitoring.md) | Evidently AI for Drift Monitoring | Accepted |
| [ADR-ML-005](ADR-ML-005-ci-cd-platform.md) | GitHub Actions as CI/CD Platform | Accepted |
| [ADR-ML-006](ADR-ML-006-infrastructure-terraform.md) | Terraform for Infrastructure | Accepted |
| [ADR-ML-007](ADR-ML-007-dev-container.md) | Dev Containers for Local Development | Accepted |
| [ADR-ML-008](ADR-ML-008-model-approval-policy.md) | Three-Gate Model Approval Policy | Accepted |
| [ADR-ML-009](ADR-ML-009-pre-commit-toolchain.md) | Pre-commit Toolchain | Accepted |
| [ADR-ML-014](ADR-ML-014-multi-env-strategy.md) | Multi-Environment Promotion Strategy | Accepted |
| [ADR-ML-015](ADR-ML-015-fairness-framework.md) | Fairness & Explainability Framework | Accepted |
| [ADR-ML-016](ADR-ML-016-distributed-training.md) | Distributed Training Framework | Accepted |
| [ADR-ML-017](ADR-ML-017-pipeline-orchestration.md) | Pipeline Orchestration | Accepted |
| [ADR-ML-018](ADR-ML-018-batch-inference.md) | Batch Inference Architecture | Accepted |

## Numbering Gaps

ADR-ML-010 through ADR-ML-013 are reserved for Phase 1 items:

| Number | Reserved for |
|---|---|
| ADR-ML-010 | Continuous Training architecture |
| ADR-ML-011 | Feature store tool choice |
| ADR-ML-012 | Shadow deployment routing strategy |
| ADR-ML-013 | ML Metadata Store schema |

## Format

Use `ADR-ML-002-data-versioning.md` as the format template.
Required sections: Context, Decision, Alternatives Considered, Consequences, Review Triggers.

## New ADR Numbers

Phase 3 ADRs start at ADR-ML-019.
```

---

### Gap 6: `monitoring/slos/` — Only Has vLLM SLO; No General Pattern

The `monitoring/slos/` directory has `vllm-serving-slo.yaml` but no defaults
file, no per-model template, and no README. Phase 1 instructions specified
these but they were never generated.

**Files to create:**

```
monitoring/slos/
  _defaults.yaml          # Default SLO thresholds (availability, latency_p99, error_rate)
  README.md               # SLO authoring guide
  slo-template.yaml       # Copy-paste template for new models
```

**`_defaults.yaml` required fields:**

```yaml
# Default SLO thresholds applied when no model-specific file exists.
# Override per model by creating monitoring/slos/<model-name>-slo.yaml
slo_defaults:
  availability:
    window: "30d"
    target: 0.995
  latency_p99_ms:
    window: "5m"
    threshold: 500
  latency_p50_ms:
    window: "5m"
    threshold: 100
  error_rate_pct:
    window: "5m"
    threshold: 1.0
  burn_rate_critical:
    window: "1h"
    multiplier: 14.4   # 1-hour fast burn
  burn_rate_warning:
    window: "6h"
    multiplier: 6.0    # 6-hour slow burn
```

**Rules:**
- Follow the PrometheusRule format used in `monitoring/slos/vllm-serving-slo.yaml`.
- The README must explain how to create a per-model SLO file.
- The template must reference `_defaults.yaml` thresholds, not hardcode them.

---

### Gap 7: `scripts/generate_model_card.py` and Model Card Template — Never Created

Phase 1 specified these files but they were not created. The model card
format exists in `docs/model-cards/fraud-detection-model-card.md` but
there is no generator.

**Files to create:**

```
scripts/
  generate_model_card.py        # CLI model card generator
  model-card-template.md.j2     # Jinja2 template
```

**`generate_model_card.py` required CLI:**

```
python scripts/generate_model_card.py \
    --model-name <name> \
    --model-version <version> \
    --output-dir docs/model-cards/
```

**Required sections the generator must output (matches fraud-detection-model-card.md format):**
1. Model details (name, version, type, framework, owner, serving runtime)
2. Intended use and out-of-scope uses
3. Training data (DVC hash, classification level, row count via MLflow tag)
4. Evaluation results (accuracy, F1, drift score from MLflow run metrics)
5. Fairness considerations (from `policy/fairness/<model-name>-fairness.yaml` if exists)
6. Serving SLOs (from `monitoring/slos/<model-name>-slo.yaml` if exists)
7. Ethical and operational limitations
8. Approval and governance (from `policy/model-approval/approved-versions.yaml`)

**Rules:**
- Use Jinja2 for templating. Read model metadata from MLflow via SDK v2.
- If a required MLflow tag is missing, insert `[NOT SET — set tag <tag_name> on training run]`.
- Exit 0 on success, exit 1 if model is not found in MLflow registry.
- Output to `docs/model-cards/<model-name>/v<version>.md`.
- Add `generate-model-card` as a target in `Makefile` and `Taskfile.yml`.
- Module-level docstring with `Purpose`, `Usage`, `Dependencies`, `Exit codes`.

---

### Gap 8: `ci/github-actions/model-cards/generate-card.yml` — Never Created

**File to create:** `ci/github-actions/model-cards/generate-card.yml`

Reusable workflow (`workflow_call`) triggered by `evaluate.yml` when a model
is promoted to Staging. Inputs: `model_name`, `model_version`. Steps:

1. Checkout
2. Setup Python 3.11
3. Install `mlflow jinja2 pyyaml`
4. Run `python scripts/generate_model_card.py`
5. Upload generated card as workflow artifact (90-day retention)
6. Open PR to `docs/model-cards/` via `peter-evans/create-pull-request@v7`
   with label `model-card` and auto-merge label

**Rules:**
- PR auto-merges (informational, no human approval required).
- Card generation failure is `continue-on-error: true` — it must not block model promotion.
- Commit message: `chore: generate model card for <model-name> v<version> [skip ci]`.

---

## SECTION B — Phase 3 Implementation Mandate

Phase 3 is the **advanced operations** phase. Six workstreams implement capabilities
that distinguish a mature, org-scale ML platform from a well-functioning single-team system.

---

### 1. Online Learning

**Goal**: Support incremental model updates from streaming data without a full retrain cycle.
Models update on a schedule or event basis, consuming recent data from a stream,
while the production model continues serving.

**Key files to read before generating code:**
- `ci/github-actions/model-training/continuous-training.yml` — CT trigger pattern to extend
- `ci/github-actions/model-monitoring/drift-check.yml` — drift trigger source
- `monitoring/evidently/drift_report.py` — drift score source
- `pipelines/retraining_pipeline.py` — retraining pipeline to extend
- `mlflow/metadata-store/client.py` — lineage recording pattern
- `docs/golden-paths/model-monitoring.md` — monitoring architecture

**Architecture:**

```
Streaming source (Kafka / Kinesis / Pub/Sub)
        ↓
online_learning/consumer.py   # reads mini-batches from stream
        ↓
online_learning/updater.py    # calls model.partial_fit() or fine-tune step
        ↓
online_learning/validator.py  # validates updated model on holdout window
        ↓
Gate: accuracy delta < -2%?   → rollback to last stable checkpoint
      accuracy delta >= -2%?  → promote updated model to Staging
        ↓
MLflow: log update run with trigger_reason = "online_update"
```

**Rules:**
- Online learning uses `partial_fit()` for sklearn models and a single-epoch
  gradient step for PyTorch/TF. Never update on a single record — minimum
  mini-batch size is `online_learning.min_batch_size` (default 500).
- Updated models are logged as new MLflow runs with tag `online_update: true`.
- The same three evaluation gates as offline training must pass before the
  online-updated model reaches Production. Do not bypass gates for online updates.
- Kafka is the default stream source. Kinesis and Pub/Sub are alternatives
  documented in `online_learning/consumers/` as separate files.
- Rollback triggers automatically if the updated model's accuracy drops more than
  2% below the current Production baseline on the holdout window.
- Online update frequency: minimum 30 minutes between updates (cooldown).
  Implement via a timestamp check in `online_learning/updater.py`.
- Log `update_batch_size`, `update_mini_batch_count`, and `stream_lag_seconds`
  as MLflow metrics on every online learning run.

**New files to create:**
```
online_learning/
  consumer.py               # Kafka/Kinesis/Pub/Sub stream consumer
  updater.py                # partial_fit / fine-tune step
  validator.py              # holdout accuracy gate
  rollback.py               # automatic rollback on accuracy drop
  consumers/
    kafka_consumer.py       # Kafka-specific consumer
    kinesis_consumer.py     # Kinesis-specific consumer
    pubsub_consumer.py      # GCP Pub/Sub-specific consumer
  README.md
ci/github-actions/online-learning/
  online-update.yml         # scheduled / event-triggered online update job
  online-rollback.yml       # automatic rollback workflow
monitoring/online-learning/
  online-learning-alerts.yaml  # Prometheus alerts for accuracy drift post-update
docs/golden-paths/
  online-learning.md        # golden path doc
docs/decisions/
  ADR-ML-019-online-learning.md   # required before merge
```

---

### 2. Multi-Cloud Serving

**Goal**: Deploy model endpoints across AWS (SageMaker), GCP (Vertex AI), and Azure (Azure ML)
with a unified traffic routing layer, automatic failover, and cross-cloud health monitoring.
A single model version can be live on all three clouds simultaneously.

**Key files to read before generating code:**
- `terraform/aws-sagemaker/main.tf` — AWS serving infrastructure
- `terraform/gcp-vertex-ai/main.tf` — GCP serving infrastructure
- `terraform/azure-ml/main.tf` — Azure serving infrastructure
- `ci/github-actions/model-deployment/deploy.yml` — single-cloud deploy pattern
- `serving/README.md` — serving runtime selection guide
- `docs/golden-paths/model-serving.md` — current serving golden path
- `monitoring/slos/vllm-serving-slo.yaml` — SLO format to extend

**Architecture:**

```
Global load balancer (cloud-agnostic, e.g. Cloudflare or AWS Global Accelerator)
        ↓
Traffic router (multi_cloud_serving/router.py)
  ├── weight: AWS endpoint     (e.g. 40%)
  ├── weight: GCP endpoint     (e.g. 40%)
  └── weight: Azure endpoint   (e.g. 20%)
        ↓
Failover: if an endpoint's error_rate > 5% for 2 min:
  → shift its traffic to healthy endpoints proportionally
  → fire CrossCloudFailoverTriggered Prometheus alert
        ↓
Health check: all endpoints sampled every 30s
```

**Rules:**
- Traffic weights are defined in `multi_cloud_serving/routing-config/<model-name>.yaml`.
  Do not hardcode weights in code.
- Endpoint registration is via `multi_cloud_serving/registry.py` which reads from
  the three Terraform output files and maintains a live endpoint catalog.
- Health checks call the runtime-specific health endpoint:
  - SageMaker: `GET /ping` on the endpoint
  - Vertex AI: `GET /v1/endpoints/<id>` status via GCP API
  - Azure ML: `GET /score` managed endpoint health
- Cross-cloud failover must be logged as an MLflow tag on the active serving run:
  `multi_cloud_failover_at: <ISO timestamp>`.
- SLOs are defined per endpoint, not per model. Each cloud endpoint gets its own
  SLO file in `monitoring/slos/`.
- Cost normalisation: multi-cloud serving costs are normalised to USD per 1000
  predictions using the rates in `finops/data/instance-rates.yaml`. Add
  `sagemaker_cost_per_1k`, `vertex_cost_per_1k`, `azure_cost_per_1k` to the
  instance rates file.

**New files to create:**
```
multi_cloud_serving/
  router.py                 # traffic weight routing + failover logic
  registry.py               # endpoint catalog from Terraform outputs
  health_check.py           # per-cloud health probe implementations
  routing-config/
    _config-schema.yaml     # routing config schema
    README.md
  README.md
ci/github-actions/multi-cloud/
  deploy-multicloud.yml     # deploy to all three clouds in parallel
  failover-test.yml         # chaos test: disable one cloud, verify failover
monitoring/multi-cloud/
  cross-cloud-alerts.yaml   # Prometheus alerts for failover events
docs/golden-paths/
  multi-cloud-serving.md    # golden path doc
docs/decisions/
  ADR-ML-020-multi-cloud-serving.md  # required before merge
```

---

### 3. Model Optimisation

**Goal**: Reduce serving latency and cost by applying post-training optimisation —
quantisation (INT8/FP16), pruning, and knowledge distillation — before production
deployment. Every optimised model is benchmarked and compared against the baseline.

**Key files to read before generating code:**
- `serving/triton/README.md` — Triton TensorRT backend
- `serving/vllm/README.md` — vLLM quantisation options
- `ci/github-actions/model-evaluation/evaluate.yml` — evaluation gate to extend
- `docs/golden-paths/model-serving.md` — serving golden path
- `finops/data/instance-rates.yaml` — cost per inference to benchmark
- `monitoring/slos/vllm-serving-slo.yaml` — latency SLO to validate against

**Optimisation pipeline:**

```
Trained model (Production stage in MLflow)
        ↓
model_optimization/pipeline.py
  ├── Step 1: quantise (INT8 via ONNX Runtime or TensorRT)
  ├── Step 2: benchmark latency (p50, p99) and throughput on target hardware
  ├── Step 3: validate accuracy delta (must be < 0.5% vs baseline)
  └── Step 4: compare cost per 1000 predictions
        ↓
Gate: accuracy_delta > 0.5%? → reject optimisation, keep baseline
      latency_p99 > baseline? → reject (optimisation made it slower)
      else                    → register optimised model with suffix -opt-<method>
        ↓
MLflow: log optimised model as new version with tags:
  optimization_method: quantisation|pruning|distillation
  baseline_version: <version>
  accuracy_delta_pct: <value>
  latency_p99_reduction_pct: <value>
  cost_reduction_pct: <value>
```

**Rules:**
- Default optimisation method is INT8 quantisation via ONNX Runtime. TensorRT is
  the alternative for NVIDIA GPU serving. Document both.
- The optimised model is registered with name `<model-name>-opt` in MLflow, not
  as a version of the original. This prevents optimised models from overwriting
  production baseline models.
- Benchmarking runs 1000 warmup requests then 5000 measurement requests using
  `model_optimization/benchmark.py`. Do not use a fixed sleep as a warmup.
- Knowledge distillation requires a teacher model and a student model. The teacher
  is always a Production-stage model. The student is a smaller architecture defined
  in `model_optimization/distillation/student_configs/`.
- Hardware targets are declared per model in `model_optimization/targets/`:
  `cpu`, `cuda-a100`, `cuda-h100`, `triton-onnx`, `triton-trt`. Each has
  its own benchmark parameters.
- Never optimise a model that has not first been in Production stage.

**New files to create:**
```
model_optimization/
  pipeline.py               # end-to-end optimisation pipeline
  quantisation.py           # ONNX Runtime + TensorRT INT8/FP16
  pruning.py                # structured and unstructured pruning
  benchmark.py              # latency/throughput benchmarking harness
  distillation/
    trainer.py              # knowledge distillation training loop
    student_configs/
      README.md
  targets/
    cpu.yaml
    cuda-a100.yaml
    cuda-h100.yaml
    triton-onnx.yaml
    triton-trt.yaml
  README.md
ci/github-actions/model-optimization/
  optimize.yml              # optimisation pipeline CI workflow
  benchmark.yml             # reusable benchmark workflow
docs/golden-paths/
  model-optimization.md     # golden path doc
docs/decisions/
  ADR-ML-021-model-optimization.md  # required before merge
```

---

### 4. LLMOps

**Goal**: A complete operational path for large language models — from fine-tuning
to evaluation harness to RLHF pipeline to prompt versioning and production monitoring.
LLM workloads are structurally different from classical ML and need dedicated tooling.

**Key files to read before generating code:**
- `serving/vllm/` — current vLLM serving (extend, don't replace)
- `training/ray/train_distributed.py` — distributed training to extend for LLM fine-tuning
- `training/ray/checkpoint_callback.py` — checkpoint pattern to reuse
- `ci/github-actions/model-training/train.yml` — base training workflow to extend
- `pipelines/training_pipeline.py` — pipeline pattern to follow
- `mlflow/metadata-store/client.py` — lineage recording to extend with LLM-specific fields
- `fairness/explainability.py` — explainability pattern for LLM output attribution
- `docs/decisions/ADR-ML-016-distributed-training.md` — distributed training decisions

**LLMOps sub-domains:**

#### 4a. Fine-tuning (LoRA / QLoRA / full fine-tune)
```
llmops/
  fine_tuning/
    lora_trainer.py         # LoRA fine-tuning via PEFT + Transformers
    qlora_trainer.py        # QLoRA 4-bit fine-tuning (fits on 12GB RTX 5070)
    full_fine_tune.py       # full fine-tuning for teams with H100 budget
    trainer_config.py       # shared config dataclass
```

Fine-tuning rules:
- Use `peft` and `transformers` libraries. Never implement LoRA from scratch.
- QLora default: `BitsAndBytesConfig(load_in_4bit=True)` with NF4 quantisation.
- Fine-tuned adapters are stored in MLflow as artifacts under `adapters/<run-id>/`.
- Training uses the same `CheckpointCallback` as classical distributed training.
- Log `perplexity`, `validation_loss`, and `tokens_per_second` as MLflow metrics.

#### 4b. LLM Evaluation Harness
```
llmops/
  evaluation/
    harness.py              # evaluation runner (wraps lm-evaluation-harness or promptfoo)
    benchmarks/             # task-specific benchmark configs
      summarisation.yaml
      classification.yaml
      qa.yaml
    golden_dataset/
      README.md             # how to curate a golden dataset
```

Evaluation rules:
- Every LLM promotion must pass evaluation on a golden dataset before Staging.
- Metrics: ROUGE-L (summarisation), F1 (classification), exact match (QA), custom
  business metrics where defined.
- LLM evaluation gate is Gate 5 in `evaluate.yml`, after existing gates 1–4.
- Do not use the same data for fine-tuning and golden dataset evaluation.

#### 4c. Prompt Versioning
```
llmops/
  prompts/
    registry.py             # prompt version store backed by MLflow
    schema.yaml             # prompt schema (name, version, template, variables)
    <model-name>/           # per-model prompt files
      system.v1.txt
      user.v1.txt
  README.md
```

Prompt rules:
- Prompts are versioned files in `llmops/prompts/<model-name>/`.
- Prompt changes require a PR — treat prompts as code.
- Prompt version and hash are logged as MLflow tags on every inference run:
  `prompt_name`, `prompt_version`, `prompt_sha256`.
- Never interpolate user input directly into prompts — use named variables only.

#### 4d. RLHF Pipeline (basic)
```
llmops/
  rlhf/
    reward_model.py         # reward model training (Bradley-Terry pair ranking)
    ppo_trainer.py          # PPO fine-tuning loop (TRL library)
    preference_dataset.py   # human preference data collector / formatter
    README.md
```

RLHF rules:
- Use TRL (`trl` library) for PPO. Do not implement PPO from scratch.
- Reward model and policy model are registered as separate MLflow models.
- RLHF training runs are tagged `rlhf_step: reward_model` or `rlhf_step: ppo`.

**LLMOps CI:**
```
ci/github-actions/llmops/
  fine-tune.yml             # LoRA/QLoRA fine-tuning CI workflow
  evaluate-llm.yml          # LLM evaluation harness CI workflow
  prompt-validate.yml       # validate prompt schema on PR
  rlhf-train.yml            # RLHF training workflow
```

**New MLflow experiment naming for LLMOps:**
- Fine-tuning runs: `<model-name>-llm-finetune`
- RLHF reward model: `<model-name>-llm-reward`
- RLHF policy: `<model-name>-llm-ppo`
- LLM evaluation: `<model-name>-llm-eval`

**New files to create:**
```
llmops/
  fine_tuning/
  evaluation/
  prompts/
  rlhf/
  README.md
ci/github-actions/llmops/
docs/golden-paths/
  llmops.md                 # golden path doc covering all four sub-domains
docs/decisions/
  ADR-ML-022-llmops.md      # required before merge
```

---

### 5. Self-Service Portal

**Goal**: A lightweight internal web UI that lets engineering teams register, deploy,
and monitor ML models without opening a terminal or reading documentation.
Reduces the time from "model trained" to "endpoint live" from hours to minutes.

**Key files to read before generating code:**
- `catalog/` — service catalog pattern to follow for team/model registration
- `policy/model-approval/approved-versions.yaml` — approval registry as backend data
- `finops/budgets/` — budget config pattern exposed in the UI
- `monitoring/dashboards/model-health.json` — Grafana dashboard to link from UI
- `ci/github-actions/promotion/` — workflows triggered by the portal
- `docs/golden-paths/multi-env-promotion.md` — promotion flow the UI wraps
- `.ai/context/repo-summary.md` — repo structure the portal exposes

**Portal architecture:**

```
portal/
  backend/
    api/                    # FastAPI REST API
      models.py             # model registration, listing, promotion
      deployments.py        # deployment status, logs, health
      budgets.py            # budget config CRUD
      notifications.py      # Slack/email alert config
    github_client.py        # triggers GitHub Actions workflows via REST API
    mlflow_client.py        # reads MLflow registry
    k8s_client.py           # reads Kubernetes deployment status
  frontend/
    src/                    # React (TypeScript) SPA
      pages/
        ModelList.tsx       # list all registered models with status
        ModelDetail.tsx     # model detail: metrics, lineage, SLOs, costs
        Deploy.tsx          # trigger promotion workflow from UI
        Budgets.tsx         # budget management
        CostDashboard.tsx   # embedded Grafana or cost summary
```

**Portal rules:**
- The portal is a **read-and-trigger** interface, not a write interface. It cannot
  create or modify training data, models, or CI pipelines directly. All mutations
  go through GitHub Actions workflows (triggered via `gh` REST API).
- Authentication: use GitHub OAuth (via the portal's GitHub App registration).
  Only users with write access to the repo can trigger deployments.
- The portal is deployed as a Kubernetes Deployment in the `mlops-portal` namespace.
  It consumes existing MLflow, Kubernetes, and GitHub APIs — no new data stores.
- All portal pod specs must carry the four cost labels: `cost-center`, `team`,
  `model-name: portal`, `environment`.
- The portal's GitHub client uses a GitHub App installation token, not a PAT.
  Never store PATs in the portal config.

**New files to create:**
```
portal/
  backend/
    api/
      models.py
      deployments.py
      budgets.py
      notifications.py
    github_client.py
    mlflow_client.py
    k8s_client.py
    main.py                 # FastAPI app entrypoint
    requirements.txt
  frontend/
    src/
      pages/
      components/
      App.tsx
    package.json
    tsconfig.json
  Dockerfile                # multi-stage: frontend build → backend serve
  README.md
cd/kubernetes/portal/
  deployment.yaml           # portal Kubernetes Deployment
  service.yaml              # portal Kubernetes Service
  ingress.yaml              # ingress (path: /mlops-portal)
  network-policy.yaml       # allow egress to GitHub API, MLflow, k8s API
terraform/portal/
  main.tf                   # optional: GitHub App registration via Terraform
docs/golden-paths/
  self-service-portal.md    # golden path doc (onboarding and usage)
docs/decisions/
  ADR-ML-023-self-service-portal.md  # required before merge
```

---

### 6. Federated Learning

**Goal**: Enable privacy-preserving model training across data silos where raw data
cannot leave its jurisdiction. Each party trains on local data; only model gradients
or parameters are shared for aggregation.

**Key files to read before generating code:**
- `training/ray/train_distributed.py` — distributed training pattern to adapt
- `training/ray/checkpoint_callback.py` — checkpoint pattern to reuse
- `mlflow/metadata-store/client.py` — lineage pattern for federated rounds
- `policy/data-governance/README.md` — data classification rules (critical for federated)
- `ci/github-actions/distributed-training/gpu-approval-gate.yml` — approval gate pattern
- `docs/decisions/ADR-ML-016-distributed-training.md` — distributed training ADR

**Federated learning architecture:**

```
Federated Coordinator (federated_learning/coordinator.py)
  ├── Maintains global model state
  ├── Schedules training rounds
  └── Applies FedAvg (or FedProx) aggregation

        ↓ distributes global model weights
        ↑ receives local gradients / model deltas

Party A (federated_learning/party.py)        Party B             Party N
  ├── Trains on local data only              ├── Trains locally  ...
  ├── Computes model delta                   └── Sends delta
  └── Optionally: applies differential privacy noise before sending
```

**Rules:**
- FedAvg is the default aggregation algorithm. FedProx is the alternative for
  heterogeneous data distributions. Document both.
- Raw data NEVER leaves the party's environment. Only model weights or gradients
  are transmitted. Violating this is a hard policy violation — add a comment in
  `policy/data-governance/README.md` explicitly stating this.
- Differential privacy (DP) is optional but recommended for high-sensitivity data.
  Use `opacus` library for PyTorch DP. Log `epsilon` and `delta` as MLflow tags
  on every federated round: `dp_epsilon`, `dp_delta`.
- Each federated round is a separate MLflow run tagged `federated_round: <N>` and
  `federated_party_count: <N>`.
- The global model after aggregation is registered as a new MLflow model version.
  Federated models use experiment name `<model-name>-federated`.
- All parties must use the same model architecture and the same MLflow tracking server.
  Cross-jurisdiction deployments require the tracking server to be accessible to
  all parties (e.g. via private link or VPN — not public internet).
- Federated learning is a hard-gate candidate: no Production promotion without
  validation on a held-out global test set at the coordinator.

**New files to create:**
```
federated_learning/
  coordinator.py            # round orchestrator and FedAvg aggregator
  party.py                  # local training + gradient computation
  aggregation/
    fedavg.py               # Federated Averaging
    fedprox.py              # FedProx (heterogeneous data)
  privacy/
    dp_wrapper.py           # Differential privacy via opacus
  README.md
ci/github-actions/federated/
  federated-train.yml       # coordinator workflow: dispatch rounds to parties
  federated-eval.yml        # global model evaluation after aggregation
docs/golden-paths/
  federated-learning.md     # golden path doc
docs/decisions/
  ADR-ML-024-federated-learning.md   # required before merge
```

---

## SECTION C — Invariant Rules (All Phases Active Simultaneously)

These rules apply to every file generated during Phase 3. Phase 1 and Phase 2
invariant rules remain fully active — all three sets apply simultaneously.

### Phase 3 architecture principles

- **Data never leaves its boundary.** This is absolute for federated learning
  and applies wherever data governance policy is `confidential` or `restricted`.
- **Optimised models are versioned separately.** Never replace the Production
  baseline with an optimised variant until the accuracy gate passes.
- **LLM prompts are code.** Version them, review them, and track them in MLflow.
- **The portal triggers, never writes.** The self-service portal fires GitHub
  Actions workflows for every mutation — it never calls MLflow or Kubernetes
  directly to make changes.
- **Online updates go through the same gates as offline training.** There is no
  fast-path promotion for online-updated models.

### Coding standards (carried from all previous phases)

- Python: Black, isort, Ruff, Bandit — no exceptions.
- File names: `lowercase-kebab-case` for infrastructure, `snake_case.py` for Python modules.
- Every new Python module: docstring with `Purpose`, `Usage`, `Dependencies`.
- Every new CI workflow: block comment with `Trigger`, `Inputs`, `Outputs`, `Beginner note`.
- YAML: 2-space indent, no tabs, `check-yaml` enforced by pre-commit.
- Terraform: `terraform fmt`, pinned provider versions, remote state with locking.

### Security rules (Phase 3 additions)

- LLM prompts must be stored as files, never interpolated from environment variables.
- Federated learning gradient transmission must be encrypted in transit (TLS 1.3 minimum).
- The self-service portal must never expose raw MLflow run tags that contain PII.
- Online learning consumers must authenticate to the stream source using short-lived
  credentials (OIDC or IAM role — never long-lived API keys).
- Model optimisation artifacts are subject to the same data classification rules
  as their source models. A `confidential` model produces a `confidential` optimised model.

### New MLflow conventions for Phase 3

- Online learning runs: `trigger_reason = online_update`, `online_update = true`
- Multi-cloud serving runs: `serving_cloud = aws|gcp|azure`, `multi_cloud = true`
- Optimised model versions: `optimization_method`, `baseline_version`, `accuracy_delta_pct`
- LLM runs: `llm_task = finetune|rlhf_reward|rlhf_ppo|eval`, `base_model`
- Federated runs: `federated_round`, `federated_party_count`, `dp_epsilon` (if DP used)

### New Kubernetes rules for Phase 3

- Portal Deployment: must have liveness and readiness probes on the FastAPI `/health` endpoint.
- Federated coordinator: runs as a Kubernetes Job per round, not a Deployment.
- Online learning consumer: runs as a Kubernetes Deployment with HPA scaling on
  stream lag metric (consumer group lag > 10000 messages → scale out).

---

## SECTION D — Phase 3 ADR Requirements

All six workstreams and their ADR numbers:

| Workstream | ADR | Key decision to document |
|---|---|---|
| Online learning | ADR-ML-019 | Stream source choice, mini-batch minimum, gate bypass policy |
| Multi-cloud serving | ADR-ML-020 | Traffic routing algorithm, failover policy, cost normalisation |
| Model optimisation | ADR-ML-021 | Quantisation method, accuracy tolerance, benchmark harness |
| LLMOps | ADR-ML-022 | Fine-tuning library (PEFT), evaluation harness choice, RLHF scope |
| Self-service portal | ADR-ML-023 | Portal architecture (SPA + API), GitHub App vs PAT, auth model |
| Federated learning | ADR-ML-024 | Aggregation algorithm (FedAvg vs FedProx), DP requirement, topology |

All ADRs are hard merge gates.

---

## SECTION E — Implementation Order

Phase 3 workstreams can be implemented in parallel except for the dependency below:

```
Week 1–4:  LLMOps (independent; highest strategic value)
           Model Optimisation (independent; reduces serving cost immediately)

Week 4–8:  Online Learning (builds on existing CT pipeline from Phase 1)
           Multi-Cloud Serving (builds on all three Terraform modules)

Week 8–14: Self-Service Portal (wraps everything — implement last)
           Federated Learning (independent; can be parallel with portal)
```

---

## SECTION F — File Routing Quick Reference (Phase 3 Additions)

| Task | Primary path |
|---|---|
| Online learning consumer scripts | `online_learning/consumers/` |
| Online learning CI workflows | `ci/github-actions/online-learning/` |
| Multi-cloud routing configs | `multi_cloud_serving/routing-config/` |
| Multi-cloud CI workflows | `ci/github-actions/multi-cloud/` |
| Model optimisation scripts | `model_optimization/` |
| Model optimisation CI workflows | `ci/github-actions/model-optimization/` |
| LLMOps fine-tuning scripts | `llmops/fine_tuning/` |
| LLMOps prompt files | `llmops/prompts/<model-name>/` |
| LLMOps RLHF scripts | `llmops/rlhf/` |
| LLMOps CI workflows | `ci/github-actions/llmops/` |
| Portal backend | `portal/backend/` |
| Portal frontend | `portal/frontend/` |
| Portal Kubernetes manifests | `cd/kubernetes/portal/` |
| Federated learning scripts | `federated_learning/` |
| Federated learning CI workflows | `ci/github-actions/federated/` |
| Phase 3 ADRs | `docs/decisions/ADR-ML-019` through `ADR-ML-024` |

---

## Session Recording

Record every Phase 3 session in `.ai/session/` as `YYYY-MM-DD-phase3-<slug>.md`.

Minimum required content:
- Objective
- Phase (3) and workstream(s) addressed
- Gap fixes completed (from Section A)
- Files created and files modified
- ADR filed (or pending)
- Validation performed
- Open blockers

---

## Quick-Start Prompts

### Section A — Gap Fixes

```
@workspace Add missing Phase 2 targets to Makefile and Taskfile.yml following the Gap 1 rules

@workspace Add missing Dependabot entries for Azure ML, Ray cluster, Vertex Pipelines, and Phase 2 Python deps following Gap 2 rules

@workspace Update GETTING_STARTED.md with Phase 2 quick links and capabilities section following Gap 3 rules

@workspace Update README.md with Phase 2 capabilities and Azure ML Terraform following Gap 4 rules

@workspace Create docs/decisions/README.md as the ADR index following Gap 5 rules

@workspace Create monitoring/slos/_defaults.yaml, slo-template.yaml, and README.md following Gap 6 rules

@workspace Create scripts/generate_model_card.py and model-card-template.md.j2 following Gap 7 rules

@workspace Create ci/github-actions/model-cards/generate-card.yml following Gap 8 rules
```

### Section B — Phase 3 Workstreams

```
@workspace Implement the online learning streaming update pipeline following Phase 3 online learning rules

@workspace Build multi-cloud serving with traffic routing and failover across AWS, GCP, and Azure following Phase 3 multi-cloud rules

@workspace Create the model optimisation pipeline with INT8 quantisation and benchmarking following Phase 3 model optimisation rules

@workspace Implement the full LLMOps stack (fine-tuning, evaluation, prompt versioning, RLHF) following Phase 3 LLMOps rules

@workspace Build the self-service portal (FastAPI backend + React frontend) following Phase 3 portal rules

@workspace Implement federated learning with FedAvg aggregation and optional differential privacy following Phase 3 federated learning rules
```
