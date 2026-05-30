# ADR-ML-022 — LLMOps Framework

| Field       | Value                                                |
|-------------|------------------------------------------------------|
| ID          | ADR-ML-022                                           |
| Status      | Accepted                                             |
| Date        | 2025-05-30                                           |
| Deciders    | ML Platform, Applied Research, MLOps Engineering     |

---

## Context

The MLOps Playbook supports general machine learning pipelines but previously
had no opinionated toolchain for Large Language Model (LLM) workflows.  As the
organisation adopts LLMs for production use cases, the following gap areas
required explicit decisions:

1. How to fine-tune LLMs cost-effectively with limited GPU resources.
2. How to align models with human preferences (RLHF).
3. How to version and validate prompt templates used in inference pipelines.
4. How to evaluate LLM quality in a benchmark-driven, reproducible way.
5. How to integrate all of the above into existing CI/CD infrastructure.

---

## Decision

### Fine-tuning Strategy — PEFT (Parameter-Efficient Fine-Tuning)

**Chosen**: `peft` library with LoRA / QLoRA adapters as the default path;
full fine-tuning retained for models where full weight updates are required.

**Rationale**:
- LoRA reduces trainable parameters by 99%+ while preserving task performance.
- QLoRA adds 4-bit NF4 quantisation to LoRA, enabling 7B+ models on a single
  consumer GPU.
- Adapters are stored as MLflow artifacts, not full model checkpoints, reducing
  storage by an order of magnitude.
- Full fine-tuning remains available for research use cases.

**Rejected alternatives**:
- Prefix-tuning: less flexible adapter architecture.
- Adapter layers (Houlsby): lower performance vs LoRA in recent benchmarks.

### RLHF Toolchain — TRL

**Chosen**: Hugging Face `trl` library for both reward model training
(`RewardTrainer`) and PPO-based policy fine-tuning (`PPOTrainer`).

**Rationale**:
- TRL provides production-ready RLHF primitives with active maintenance.
- `RewardTrainer` abstracts the Bradley-Terry preference loss over
  (chosen, rejected) pairs.
- `PPOTrainer` integrates with any HuggingFace model and supports reference
  KL-divergence penalty out of the box.

**Rejected alternatives**:
- Custom PPO implementation: high maintenance burden.
- OpenRLHF: requires multi-GPU infrastructure not universally available.

### Prompt Versioning — MLflow Artifacts

**Chosen**: Prompt templates stored as versioned YAML files in
`llmops/prompts/`, validated against `schema.yaml` (JSON Schema draft-07),
and registered as MLflow run artifacts with content-based SHA256 deduplication.

**Rationale**:
- Reuses existing MLflow infrastructure.
- Prompt YAML format is human-readable and git-diffable.
- Content hashing prevents redundant registrations.

**Rejected alternatives**:
- Dedicated prompt management SaaS (PromptLayer, LangSmith): external
  dependency and vendor lock-in.
- Plain git tags: loses MLflow traceability and experiment linkage.

### Evaluation Harness

**Chosen**: Lightweight Python harness (`llmops/evaluation/harness.py`) that
loads YAML-defined benchmark datasets and calls a standard HTTP model endpoint.
Supported metrics: `exact_match`, `f1`, `rouge_l`.

**Rationale**:
- Simple YAML format allows researchers to add benchmarks without writing code.
- HTTP-based evaluation is compatible with any serving stack (vLLM, TorchServe,
  Triton, custom FastAPI).
- Results logged to MLflow enable trend tracking and regression detection.

**Rejected alternatives**:
- EleutherAI `lm-evaluation-harness`: full-weight inference required; not
  compatible with serving-layer evaluation.
- Manual evaluation notebooks: non-reproducible.

### Integration

All four capabilities are wired into GitHub Actions:

| Workflow | File |
|---|---|
| Fine-tune (LoRA / QLoRA / full) | `ci/github-actions/llmops/fine-tune.yml` |
| LLM benchmark evaluation | `ci/github-actions/llmops/evaluate-llm.yml` |
| Prompt validate + register | `ci/github-actions/llmops/prompt-validate.yml` |
| RLHF reward + PPO train | `ci/github-actions/llmops/rlhf-train.yml` |

---

## Consequences

**Positive**:
- Uniform LLM lifecycle managed through MLflow, consistent with existing ML
  pipelines.
- LoRA/QLoRA unlocks fine-tuning for teams with single-GPU infrastructure.
- Prompt versioning prevents silent regressions caused by ad-hoc template edits.

**Negative / Risks**:
- PEFT adapter compatibility is tied to the `transformers` version; upgrades
  must be tested across all fine-tuned adapters.
- TRL API changes between major versions; pin `trl>=0.8` in requirements.
- PPO training is sensitive to reward model quality; poor preference datasets
  produce reward hacking.

---

## Related Decisions

- [ADR-ML-003](ADR-ML-003-model-serving.md) — Model Serving (vLLM)
- [ADR-ML-016](ADR-ML-016-distributed-training.md) — Distributed Training
- [ADR-ML-017](ADR-ML-017-pipeline-orchestration.md) — Pipeline Orchestration
