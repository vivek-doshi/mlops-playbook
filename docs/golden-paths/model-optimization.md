# Golden Path — Model Optimisation

End-to-end walkthrough: take a Production-stage model, optimise it for your
serving target, verify quality gates, and register the result.

---

## Prerequisites

- A model in **Production** stage in the MLflow Model Registry.
- Python 3.11 with `mlflow`, `onnxruntime`, `optimum`, `torch` installed.
- For GPU targets: access to a runner with an NVIDIA GPU and `trtexec` on PATH.

---

## Step 1 — Confirm the Baseline Model

```bash
# Check the model is in Production stage
python - <<'EOF'
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
client = mlflow.MlflowClient()
versions = client.get_latest_versions("my-model", stages=["Production"])
for v in versions:
    print(f"  version={v.version}  run_id={v.run_id}  stage={v.current_stage}")
EOF
```

Identify the `model_version` you will optimise.

---

## Step 2 — Choose an Optimisation Method

| Situation | Recommended method |
|---|---|
| CPU serving, size matters | `quantisation --target cpu` |
| A100/H100 GPU serving | `quantisation --target cuda-a100` |
| Dense model, want fewer weights | `pruning --sparsity 0.3` |
| Need a fundamentally smaller model | `distillation` |

---

## Step 3 — Dry-Run to Preview Gates

```bash
python model_optimization/pipeline.py \
  --model-name    my-model \
  --model-version 3 \
  --method        quantisation \
  --target        cpu \
  --dry-run
```

Output shows projected accuracy delta and expected latency p99.  No model
is written or registered in dry-run mode.

---

## Step 4 — Run the Optimisation Pipeline

```bash
python model_optimization/pipeline.py \
  --model-name    my-model \
  --model-version 3 \
  --method        quantisation \
  --target        cpu
```

The pipeline:
1. Downloads the Production model from MLflow.
2. Applies quantisation (ONNX INT8 for CPU).
3. Runs baseline benchmark (`BenchmarkHarness.run_baseline`).
4. Runs optimised benchmark (`BenchmarkHarness.run`).
5. Evaluates accuracy delta against baseline.
6. Enforces gates: accuracy delta < 0.5%, p99 latency ≤ baseline.
7. If gates pass: registers `my-model-opt` in MLflow.
8. If gates fail: exits cleanly, baseline untouched.

---

## Step 5 — Distillation (Optional)

If you need a fundamentally smaller model, run knowledge distillation first:

```bash
# 1. Write a student config
cat > model_optimization/distillation/student_configs/small.yaml <<'EOF'
architecture: distilbert-base-uncased
tokenizer: distilbert-base-uncased
text_column: text
label_column: label
EOF

# 2. Run distillation
python model_optimization/distillation/trainer.py \
  --teacher-model-uri  models:/my-model/3 \
  --student-config     model_optimization/distillation/student_configs/small.yaml \
  --dataset-path       data/train_hf/ \
  --model-name         my-model-distilled \
  --num-epochs         5

# 3. Then quantise the student
python model_optimization/pipeline.py \
  --model-name    my-model-distilled \
  --model-version 1 \
  --method        quantisation \
  --target        cpu
```

---

## Step 6 — Review MLflow Results

Open the MLflow UI and navigate to the `my-model-optimisation` experiment.  Review:
- `accuracy_delta_pct` — how much accuracy was lost
- `latency_p50_ms` / `latency_p99_ms` — latency improvement
- `throughput_rps` — throughput improvement

The run tags record whether each gate passed.

---

## Step 7 — CI Automation

Trigger via GitHub Actions:

```bash
# Via GitHub CLI
gh workflow run model-optimization/optimize.yml \
  -f model_name=my-model \
  -f model_version=3 \
  -f method=quantisation \
  -f target=cpu
```

Or add the `optimize` workflow as a downstream step in your promotion pipeline:

```yaml
# In your promotion workflow
jobs:
  optimise:
    uses: ./.github/workflows/model-optimization/optimize.yml
    with:
      model_name: my-model
      model_version: ${{ needs.promote.outputs.version }}
      method: quantisation
      target: cpu
```

---

## Step 8 — Update the Model Card

After a successful optimisation, update the model card to reflect the change:

```bash
python scripts/generate_model_card.py \
  --model-name     my-model-opt \
  --model-version  1 \
  --output-dir     docs/model-cards/
```

Add a note in the `post_training_notes` section of the card describing the
optimisation method, accuracy delta, and latency improvement achieved.

---

## Related Resources

- [ADR-ML-021 — Model Optimisation Framework](../decisions/ADR-ML-021-model-optimization.md)
- [model_optimization/README.md](../../model_optimization/README.md)
- [ADR-ML-003 — Model Serving](../decisions/ADR-ML-003-model-serving.md)
