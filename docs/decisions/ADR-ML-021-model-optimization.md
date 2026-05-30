# ADR-ML-021 — Model Optimisation Framework

| Field       | Value                                                |
|-------------|------------------------------------------------------|
| ID          | ADR-ML-021                                           |
| Status      | Accepted                                             |
| Date        | 2025-05-30                                           |
| Deciders    | ML Platform, Serving Engineering, MLOps Engineering  |

---

## Context

Models trained and registered in the MLflow Model Registry are sometimes too large
or too slow to serve within production SLOs defined in `monitoring/slos/`.  As the
organisation scales ML inference, the following pressures require an explicit
optimisation strategy:

1. GPU costs: large models require expensive GPU instances for serving.
2. Latency SLOs: P99 latency targets (e.g. 500ms from `monitoring/slos/_defaults.yaml`)
   cannot always be met with full-precision models on CPU.
3. Memory footprint: serving many model versions simultaneously exhausts GPU memory.

Three complementary techniques were evaluated:
- **Quantisation**: reduce numeric precision from FP32 → INT8 or FP16.
- **Pruning**: zero out or remove low-magnitude weights.
- **Knowledge Distillation**: train a smaller student model to replicate a larger teacher.

---

## Decision

### Quantisation — ONNX Runtime (default) + TensorRT (GPU)

**Chosen**:
- CPU targets: ONNX Runtime `quantize_dynamic` (INT8 weights, FP32 activations).
- GPU targets (A100, H100): TensorRT INT8 or FP16 via `trtexec`.
- Triton targets: ONNX Runtime backend or TensorRT backend depending on hardware.

**Rationale**:
- ONNX Runtime is hardware-agnostic, available in all CI environments without a
  GPU, and supports dynamic quantisation with no calibration dataset.
- TensorRT provides maximum GPU throughput but requires NVIDIA hardware and
  calibration for INT8.
- Optimum (HuggingFace) handles the ONNX export step for Transformer models.

**Rejected alternatives**:
- PyTorch `torch.quantization`: limited INT8 support, not portable to Triton.
- TensorRT-only: blocks CPU serving path.

### Pruning — PyTorch Magnitude Pruning

**Chosen**: `torch.nn.utils.prune` global unstructured L1-norm pruning (default 30%
sparsity) and structured L2-norm channel pruning.

**Rationale**:
- Built into PyTorch; no additional dependencies.
- Structured pruning reduces FLOPS, improving actual latency (not just parameter count).

**Rejected alternatives**:
- SparseML (Neural Magic): additional dependency and commercial licensing concerns.

### Knowledge Distillation — KL-Divergence + Hard-Label Cross-Entropy

**Chosen**: `distillation/trainer.py` using the standard Hinton et al. temperature
distillation loss: `α × KL(T_soft, S_soft) + (1-α) × CE(S, labels)`.

- Teacher: any Production-stage MLflow model.
- Student: smaller HuggingFace architecture defined in `student_configs/`.
- Default temperature: 4.0, default α: 0.7.

**Rationale**:
- Reuses existing Transformers/HuggingFace infrastructure.
- Decoupled from quantisation — can be combined (distill then quantise).

### Quality Gates

All optimised models must pass two gates before registration:

1. **Accuracy gate**: accuracy metric must not drop by more than **0.5%** vs the
   Production baseline (configurable in `pipeline.py`).
2. **Latency gate**: p99 latency of the optimised model must not be higher than
   the baseline (optimisation must not be slower).

### Naming Convention

Optimised models are registered as `<model-name>-opt` — never as a new version of
the original model.  This preserves the baseline model at its original registry
name and prevents silent replacement of production models with degraded variants.

---

## Consequences

**Positive**:
- Clear path to reduce GPU costs by 30–70% for applicable models.
- Quantised models are compatible with both vLLM and Triton serving without changes.
- Gate enforcement prevents accidental regression to slower or less accurate models.

**Negative / Risks**:
- INT8 static quantisation requires a calibration dataset and adds pipeline steps.
- TensorRT engines are not portable across GPU generations (A100 vs H100).
- Pruning dense Transformer models rarely provides wall-clock speedup without
  specialised sparse CUDA kernels.

---

## Related Decisions

- [ADR-ML-003](ADR-ML-003-model-serving.md) — Model Serving (vLLM, Triton, TorchServe)
- [ADR-ML-017](ADR-ML-017-pipeline-orchestration.md) — Pipeline Orchestration
- [ADR-ML-022](ADR-ML-022-llmops.md) — LLMOps (QLoRA reduces need for post-training quantisation)
