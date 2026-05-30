# Golden Path — LLMOps End-to-End

This walkthrough takes you from a base LLM to an RLHF-aligned, evaluated, and
production-deployed model using the MLOps Playbook LLMOps workstream.

## Prerequisites

```bash
pip install transformers peft bitsandbytes trl datasets mlflow accelerate \
            torch rouge-score pyyaml jsonschema jinja2
```

Ensure `MLFLOW_TRACKING_URI` is set in your environment or `.env` file.

---

## Step 1 — Prepare Your Dataset

Your training dataset must be a plain text file or HuggingFace `Dataset` with
a text column.

```bash
# Example: convert a CSV to HuggingFace Parquet format
python - <<'EOF'
from datasets import Dataset
import pandas as pd
df = pd.read_csv("data/my_corpus.csv")
ds = Dataset.from_pandas(df)
ds.save_to_disk("data/my_corpus_hf/")
EOF
```

---

## Step 2 — Choose a Fine-Tuning Strategy

| Need | Strategy | Script |
|---|---|---|
| Single GPU, large model (7B+) | QLoRA (4-bit) | `llmops/fine_tuning/qlora_trainer.py` |
| Multi-GPU, mid-size model (≤3B) | LoRA | `llmops/fine_tuning/lora_trainer.py` |
| Small model, full fine-tune budget | Full | `llmops/fine_tuning/full_fine_tune.py` |

Create a trainer config:

```yaml
# my-lora-config.yaml
model_name: my-llm
base_model: gpt2
dataset_path: data/my_corpus_hf/
text_column: text
learning_rate: 3e-4
num_epochs: 3
batch_size: 4
max_seq_length: 512
lora_r: 8
lora_alpha: 32
lora_dropout: 0.1
output_dir: outputs/my-llm/
```

```bash
python llmops/fine_tuning/lora_trainer.py --config my-lora-config.yaml
```

MLflow records the run under experiment `my-llm-llm-finetune`.

---

## Step 3 — Evaluate Against Benchmarks

Deploy the adapter to a local endpoint (e.g. vLLM) or use the test runner:

```bash
python llmops/evaluation/harness.py \
  --model-name    my-llm \
  --model-version 1 \
  --endpoint-url  http://localhost:8080/predict \
  --benchmarks-dir llmops/evaluation/benchmarks/
```

Results are logged to MLflow experiment `my-llm-llm-eval`.  Add custom
benchmarks by creating new YAML files in `llmops/evaluation/benchmarks/`:

```yaml
name: my_custom_benchmark
metric: exact_match
examples:
  - prompt: "What is the capital of France?"
    reference: "Paris"
```

---

## Step 4 — Register in MLflow Model Registry

```bash
mlflow models register \
  --model-uri "runs:/<run-id>/adapters" \
  --name my-llm
```

Transition to **Staging** after passing evaluation gates.

---

## Step 5 — Version Your Prompt Templates

Create a prompt YAML:

```yaml
# llmops/prompts/my-llm-v1.yaml
name: my-llm-classification
version: "1.0"
template: "Classify the following text into {categories}:\n\n{text}\n\nLabel:"
variables:
  - categories
  - text
metadata:
  model_name: my-llm
  author: your-name
  description: Text classification prompt for my-llm
```

Validate and register via CI:

```bash
# Locally:
python - <<'EOF'
from pathlib import Path
from llmops.prompts.registry import PromptRegistry
registry = PromptRegistry()
run_id = registry.register(model_name="my-llm", prompt_file=Path("llmops/prompts/my-llm-v1.yaml"))
print(f"Registered: {run_id}")
EOF

# Or open a PR — the prompt-validate.yml workflow validates automatically.
```

---

## Step 6 — Deploy with vLLM

See [serving/vllm/README.md](../../serving/vllm/) for the full serving setup.
For LoRA adapters, mount the adapter directory and set `LORA_MODULES`:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model gpt2 \
  --enable-lora \
  --lora-modules my-llm=outputs/my-llm/<run-id>/adapter_model/
```

---

## Step 7 — Collect Human Feedback and Run RLHF

Once the model is in production and receiving traffic, collect preference
annotations in JSONL format:

```jsonl
{"prompt": "Summarise this article...", "chosen": "A great summary.", "rejected": "A poor summary."}
```

Build the preference dataset:

```bash
python llmops/rlhf/preference_dataset.py \
  --input-path  data/annotations.jsonl \
  --output-path data/pref_dataset/
```

Train the reward model:

```bash
python llmops/rlhf/reward_model.py \
  --model-name   my-llm \
  --base-model   gpt2 \
  --dataset-path data/pref_dataset/
```

Run PPO fine-tuning:

```bash
python llmops/rlhf/ppo_trainer.py \
  --model-name       my-llm \
  --policy-model     gpt2 \
  --reward-model-uri outputs/reward_model/<run-id>/reward_model \
  --dataset-path     data/pref_dataset/ \
  --num-steps        1000
```

Or trigger the full RLHF pipeline via CI:

```
Actions → LLMOps — RLHF Training → Run workflow
```

---

## Step 8 — Generate a Model Card

After promoting to Production, generate the model card:

```bash
python scripts/generate_model_card.py \
  --model-name    my-llm \
  --model-version 1 \
  --tracking-uri  $MLFLOW_TRACKING_URI
```

The card is written to `docs/model-cards/my-llm/v1.md` and auto-committed
via the `generate-card.yml` CI workflow.

---

## CI Workflows Summary

| Stage | Workflow to trigger |
|---|---|
| Fine-tune | `ci/github-actions/llmops/fine-tune.yml` |
| Evaluate | `ci/github-actions/llmops/evaluate-llm.yml` |
| Prompt validate / register | `ci/github-actions/llmops/prompt-validate.yml` (auto on PR) |
| RLHF training | `ci/github-actions/llmops/rlhf-train.yml` |
| Model card | `ci/github-actions/model-cards/generate-card.yml` (auto on promotion) |

---

## Key Links

- [ADR-ML-022 — LLMOps Framework](../decisions/ADR-ML-022-llmops.md)
- [llmops/README.md](../../llmops/README.md)
- [serving/vllm/](../../serving/vllm/)
- [monitoring/slos/](../../monitoring/slos/)
