# LLMOps — Large Language Model Operations

This module provides the toolchain for the full LLM lifecycle within the MLOps
Playbook: fine-tuning, evaluation, prompt management, and RLHF-based alignment.

## Module Map

```
llmops/
  fine_tuning/
    trainer_config.py      ← Shared configuration dataclass for all trainers
    lora_trainer.py        ← LoRA adapter fine-tuning (PEFT)
    qlora_trainer.py       ← QLoRA 4-bit fine-tuning (BitsAndBytesConfig)
    full_fine_tune.py      ← Full-parameter fine-tuning
    configs/               ← YAML trainer config examples
  evaluation/
    harness.py             ← Benchmark evaluation harness (exact_match, F1, ROUGE-L)
    benchmarks/            ← YAML benchmark definitions
    golden_dataset/        ← Curated (prompt, reference) pairs per domain
  prompts/
    registry.py            ← MLflow-backed prompt version registry
    schema.yaml            ← JSON Schema for prompt template YAML files
  rlhf/
    preference_dataset.py  ← Build (prompt, chosen, rejected) datasets
    reward_model.py        ← Train reward model from preference data (TRL)
    ppo_trainer.py         ← PPO fine-tuning with reward model feedback (TRL)
  README.md                ← This file
```

## Decision Record

See [ADR-ML-022](../docs/decisions/ADR-ML-022-llmops.md) for the architectural
decisions behind this module.

## Quick Start

### 1. LoRA Fine-tuning

```bash
# Copy and edit a trainer config
cp llmops/fine_tuning/configs/lora-config.yaml my-lora-config.yaml
# Edit my-lora-config.yaml: set base_model, dataset_path, model_name

python llmops/fine_tuning/lora_trainer.py --config my-lora-config.yaml
```

### 2. QLoRA Fine-tuning (4-bit, single GPU)

```bash
python llmops/fine_tuning/qlora_trainer.py --config my-qlora-config.yaml
```

### 3. Run Benchmarks

```bash
python llmops/evaluation/harness.py \\
  --model-name    my-llm \\
  --model-version 1 \\
  --endpoint-url  http://localhost:8080/predict
```

### 4. Register a Prompt

```python
from llmops.prompts.registry import PromptRegistry
registry = PromptRegistry()
registry.register(model_name="my-llm", prompt_file=Path("prompts/v1.yaml"))
```

### 5. RLHF Pipeline

```bash
# Step 1: Build preference dataset
python llmops/rlhf/preference_dataset.py \\
  --input-path data/annotations.jsonl \\
  --output-path data/pref_dataset/

# Step 2: Train reward model
python llmops/rlhf/reward_model.py \\
  --model-name my-llm \\
  --base-model gpt2 \\
  --dataset-path data/pref_dataset/

# Step 3: PPO fine-tuning
python llmops/rlhf/ppo_trainer.py \\
  --model-name my-llm \\
  --policy-model gpt2 \\
  --reward-model-uri outputs/reward_model/<run-id>/reward_model \\
  --dataset-path data/pref_dataset/
```

## CI / CD Integration

| Workflow | File |
|---|---|
| Trigger LoRA/QLoRA fine-tuning | `ci/github-actions/llmops/fine-tune.yml` |
| Evaluate LLM against benchmarks | `ci/github-actions/llmops/evaluate-llm.yml` |
| Validate and register prompt | `ci/github-actions/llmops/prompt-validate.yml` |
| Run RLHF reward + PPO training | `ci/github-actions/llmops/rlhf-train.yml` |

## MLflow Experiments

| Stage | Experiment name pattern |
|---|---|
| Fine-tuning (LoRA, QLoRA, full) | `<model-name>-llm-finetune` |
| Reward model training | `<model-name>-llm-reward` |
| PPO training | `<model-name>-llm-ppo` |
| Benchmark evaluation | `<model-name>-llm-eval` |
| Prompt registry | `<model-name>-prompts` |

## Golden Path

See [docs/golden-paths/llmops.md](../docs/golden-paths/llmops.md) for the
end-to-end walkthrough from base model to RLHF-aligned production deployment.
