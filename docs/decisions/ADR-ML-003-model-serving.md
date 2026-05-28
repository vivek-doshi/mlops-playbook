# ADR-ML-003: Three-Runtime Model Serving Strategy

**Status:** Accepted  
**Date:** 2024-06-01  
**Authors:** ML Platform Team  
**Reviewers:** @ml-approvers

---

## Context

Model serving requirements vary significantly across the team's workloads:

| Workload type | Example | Key requirements |
|--------------|---------|-----------------|
| Multi-framework batch/stream inference | Computer vision, tabular ML | Low latency, multi-model, Python/ONNX/TensorRT |
| PyTorch custom models | NLP classifiers, recommendation | Custom preprocessing, MAR packaging |
| Large Language Models (LLMs) | Chat, summarisation, code completion | Long context, OpenAI-compatible API, continuous batching |

No single serving runtime excels at all three. Using one runtime for everything
forces awkward workarounds (e.g., wrapping an LLM in a Triton Python backend loses
the continuous batching and paged attention optimisations that vLLM provides).

---

## Decision

We will maintain **three serving runtimes** in the platform, each addressing a
distinct workload profile:

| Runtime | Primary workload | Port | Config |
|---------|----------------|------|--------|
| **Triton Inference Server** | Multi-framework (Python, ONNX, TensorRT, PyTorch TorchScript) | HTTP 8000, gRPC 8001, Metrics 8002 | `serving/triton/` |
| **TorchServe** | Custom PyTorch handlers with Python preprocessing/postprocessing | HTTP 8080, Management 8081, Metrics 8082 | `serving/torchserve/` |
| **vLLM** | Large Language Models; OpenAI-compatible API | HTTP 8000 | `serving/vllm/` |

The selection is recorded as a tag on the MLflow registered model:

```python
client.set_model_version_tag(model_name, version, "serving_runtime", "triton")
```

The `ci/github-actions/model-deployment/deploy.yml` workflow reads this tag to
route to the correct runtime at deployment time.

---

## Decision Tree for Runtime Selection

```
Does the model require OpenAI-compatible API (chat/completions)?
  └─ YES → vLLM
  └─ NO → Is the model a .pt file with custom Python preprocessing?
            └─ YES → TorchServe
            └─ NO  → Triton (ONNX, TensorRT, TorchScript, Python backend)
```

See `serving/README.md` for the full decision guide.

---

## Alternatives Considered

### Single runtime: Triton for everything
- **Pros:** Reduced operational surface, single monitoring dashboard.
- **Cons:** Triton's Python backend has limited continuous batching for LLMs.
  No vLLM-style paged attention — LLM throughput is 3–5× worse than vLLM.
  TorchServe custom handlers are awkward to express as Triton Python backends.

### Single runtime: vLLM for everything
- **Pros:** Excellent for LLMs; OpenAI-compatible API is widely supported.
- **Cons:** vLLM is purpose-built for auto-regressive generation.
  Classification and structured prediction tasks have significant overhead
  compared to Triton/TorchServe.

### Single runtime: TorchServe for everything
- **Pros:** Good PyTorch ecosystem integration.
- **Cons:** No native ONNX or TensorRT support. Not designed for LLMs.
  Continuous batching requires custom handler code.

### BentoML as a unifying abstraction layer
- **Pros:** Single Python API across multiple backends.
- **Cons:** Adds an abstraction layer that complicates debugging.
  vLLM and Triton TensorRT optimisations may be partially neutralised.
  Less mature operations tooling (dashboards, Kubernetes operators).

### KServe (KFServing)
- **Pros:** Kubernetes-native, model mesh, canary deployments.
- **Cons:** Requires Knative, Istio, or Kourier — significant Kubernetes dependency.
  The team does not yet operate a service mesh in production.
  Can be layered on top of our three runtimes in a future iteration.

---

## Why Three Runtimes Won

1. **Right tool for the job.** Each runtime is purpose-built and maintained by teams
   with deep expertise in that specific inference pattern.

2. **Performance.** Keeping vLLM for LLMs preserves continuous batching and paged
   attention. Keeping Triton for ONNX/TensorRT models preserves kernel fusion and
   TensorRT optimisation. Using TorchServe for PyTorch preserves the MAR packaging
   workflow the data science team already uses.

3. **Bounded complexity.** Three runtimes is a manageable number. Each has its own
   README and Kubernetes manifest. Adding more runtimes would require additional
   ADR review.

4. **Isolation.** A misconfigured or crashing vLLM pod does not affect Triton
   inference for classification models.

---

## Consequences

### Positive
- Optimal inference performance for each workload type.
- Teams can adopt the runtime that fits their model without platform constraints.

### Negative / Trade-offs
- Three sets of Kubernetes Deployments, ConfigMaps, and monitoring dashboards.
- On-call engineers need familiarity with all three runtimes.
- Adding a new model requires knowing which runtime to target.

### Mitigation
- `serving/README.md` provides a 2-question decision tree.
- MLflow model tag `serving_runtime` makes the choice explicit and machine-readable.
- `ci/github-actions/model-deployment/deploy.yml` automates the routing.

---

## Related

- `serving/README.md` — Runtime selection guide
- `serving/triton/README.md`
- `serving/torchserve/README.md`
- `serving/vllm/README.md`
- `docs/golden-paths/model-serving.md`
- ADR-ML-001-experiment-tracking.md
