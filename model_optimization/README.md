# Model Optimization

Post-training optimisation toolchain: reduce serving latency and cost by applying
quantisation, pruning, or knowledge distillation before production deployment.

## When to Use

| Method | Use case |
|---|---|
| **Quantisation** (INT8/FP16) | Reduce memory footprint; typically 2–4× size reduction with minimal accuracy loss |
| **Pruning** | Remove redundant weights; effective for sparse inference on CPU |
| **Knowledge Distillation** | Train a smaller student model from a larger teacher; largest latency gains |

## Directory Map

```
model_optimization/
  pipeline.py               ← End-to-end optimisation pipeline
  quantisation.py           ← ONNX Runtime + TensorRT INT8/FP16
  pruning.py                ← Structured and unstructured magnitude pruning
  benchmark.py              ← Latency/throughput benchmarking harness
  distillation/
    trainer.py              ← Knowledge distillation training loop
    student_configs/
      README.md             ← How to write a student config YAML
  targets/
    cpu.yaml                ← x86-64 CPU latency/throughput thresholds
    cuda-a100.yaml          ← NVIDIA A100 thresholds
    cuda-h100.yaml          ← NVIDIA H100 thresholds
    triton-onnx.yaml        ← Triton ONNX Runtime backend thresholds
    triton-trt.yaml         ← Triton TensorRT backend thresholds
  README.md                 ← This file
```

## Quick Start

### INT8 Quantisation (CPU)

```bash
python model_optimization/pipeline.py \
  --model-name     my-model \
  --model-version  3 \
  --method         quantisation \
  --target         cpu
```

### FP16 Quantisation (A100)

```bash
python model_optimization/pipeline.py \
  --model-name     my-model \
  --model-version  3 \
  --method         quantisation \
  --target         cuda-a100
```

### Structured Pruning

```bash
python model_optimization/pruning.py \
  --model-uri   models:/my-model/3 \
  --output-dir  outputs/pruned/ \
  --sparsity    0.3 \
  --method      structured
```

### Knowledge Distillation

```bash
python model_optimization/distillation/trainer.py \
  --teacher-model-uri  models:/my-model/3 \
  --student-config     model_optimization/distillation/student_configs/small.yaml \
  --dataset-path       data/train_hf/ \
  --model-name         my-model-distilled \
  --num-epochs         5
```

## Gates

The pipeline enforces two hard gates before registering any optimised model:

1. **Accuracy gate**: accuracy delta must be < 0.5% vs baseline.
2. **Latency gate**: p99 latency of the optimised model must not exceed the baseline.

If either gate fails, the baseline model is kept and no registration occurs.

## MLflow Registration

Optimised models are registered under `<model-name>-opt` — never as a new version
of the original.  This prevents an optimised model from overwriting the production
baseline.

Tags applied to the registered model:
- `optimization_method`: `quantisation` | `pruning` | `distillation`
- `baseline_version`: original model version number
- `accuracy_delta_pct`: measured accuracy change
- `latency_p99_reduction_pct`: measured latency improvement

## CI Integration

| Workflow | File |
|---|---|
| Full optimisation pipeline | `ci/github-actions/model-optimization/optimize.yml` |
| Standalone benchmark | `ci/github-actions/model-optimization/benchmark.yml` |

## Decision Record

See [ADR-ML-021](../docs/decisions/ADR-ML-021-model-optimization.md).
