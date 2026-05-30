"""
Purpose:
    LoRA fine-tuning trainer for large language models using the PEFT library.
    Applies Low-Rank Adaptation (LoRA) adapters on top of a pre-trained base model,
    enabling efficient fine-tuning with a fraction of the parameters.

    Fine-tuned adapters are stored in MLflow as artifacts under adapters/<run-id>/.
    Training metrics (perplexity, validation_loss, tokens_per_second) are logged
    as MLflow metrics.

Usage:
    python llmops/fine_tuning/lora_trainer.py \\
        --config llmops/fine_tuning/configs/lora-config.yaml

Dependencies:
    transformers>=4.40
    peft>=0.10
    torch>=2.2
    datasets>=2.18
    mlflow>=2.11
    accelerate>=0.28
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path
from typing import Any

import yaml

try:
    import mlflow
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainerCallback,
        TrainerControl,
        TrainerState,
        TrainingArguments,
    )
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install transformers peft torch datasets mlflow accelerate",
        file=sys.stderr,
    )
    sys.exit(1)

from llmops.fine_tuning.trainer_config import LLMTrainerConfig


# ──────────────────────────────────────────────────────────────────────────────
# MLflow callback
# ──────────────────────────────────────────────────────────────────────────────

class _MLflowLoggingCallback(TrainerCallback):
    """Log Trainer metrics to the active MLflow run after each evaluation step."""

    def __init__(self, start_time: float) -> None:
        self._start_time = start_time
        self._token_count = 0

    def on_log(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        logs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if not logs:
            return
        step = state.global_step
        for key, value in logs.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value, step=step)

        # Derived: perplexity from eval_loss
        if "eval_loss" in logs:
            try:
                perplexity = math.exp(logs["eval_loss"])
                mlflow.log_metric("perplexity", perplexity, step=step)
            except OverflowError:
                mlflow.log_metric("perplexity", float("inf"), step=step)

        # tokens_per_second estimate based on elapsed wall-clock time
        elapsed = time.time() - self._start_time
        if elapsed > 0 and "train_samples_per_second" in logs:
            # Approximate: samples/s × avg_seq_len gives token throughput
            mlflow.log_metric(
                "tokens_per_second",
                logs["train_samples_per_second"] * args.max_steps,
                step=step,
            )


# ──────────────────────────────────────────────────────────────────────────────
# LoRA trainer
# ──────────────────────────────────────────────────────────────────────────────

def run_lora_fine_tuning(config: LLMTrainerConfig) -> None:
    """Execute LoRA fine-tuning and log adapters + metrics to MLflow."""
    experiment_name = f"{config.model_name}-llm-finetune"
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(tags={"llm_task": "finetune", "base_model": config.base_model}) as run:
        mlflow.log_params(
            {
                "base_model": config.base_model,
                "lora_r": config.lora_r,
                "lora_alpha": config.lora_alpha,
                "lora_dropout": config.lora_dropout,
                "learning_rate": config.learning_rate,
                "num_epochs": config.num_epochs,
                "batch_size": config.batch_size,
                "max_seq_length": config.max_seq_length,
            }
        )

        # ── Load tokenizer and base model ─────────────────────────────────
        tokenizer = AutoTokenizer.from_pretrained(config.base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            config.base_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )

        # ── Apply LoRA adapters ───────────────────────────────────────────
        lora_cfg = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=config.lora_target_modules or ["q_proj", "v_proj"],
            bias="none",
        )
        model = get_peft_model(base_model, lora_cfg)
        model.print_trainable_parameters()

        # ── Load dataset ──────────────────────────────────────────────────
        dataset = load_dataset(config.dataset_path, split="train")
        if config.eval_dataset_path:
            eval_dataset = load_dataset(config.eval_dataset_path, split="validation")
        else:
            split = dataset.train_test_split(test_size=0.05, seed=42)
            dataset, eval_dataset = split["train"], split["test"]

        def tokenize(batch: dict[str, Any]) -> dict[str, Any]:
            return tokenizer(
                batch[config.text_column],
                truncation=True,
                max_length=config.max_seq_length,
                padding=False,
            )

        dataset = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)
        eval_dataset = eval_dataset.map(
            tokenize, batched=True, remove_columns=eval_dataset.column_names
        )

        # ── Training arguments ────────────────────────────────────────────
        training_args = TrainingArguments(
            output_dir=str(Path(config.output_dir) / run.info.run_id),
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            fp16=torch.cuda.is_available(),
            report_to="none",  # MLflow callback handles logging
            logging_steps=50,
        )

        start_time = time.time()
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            eval_dataset=eval_dataset,
            data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
            callbacks=[_MLflowLoggingCallback(start_time)],
        )

        trainer.train()

        # ── Save and log adapter ──────────────────────────────────────────
        adapter_dir = Path(config.output_dir) / "adapters" / run.info.run_id
        adapter_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))

        mlflow.log_artifacts(str(adapter_dir), artifact_path=f"adapters/{run.info.run_id}")
        mlflow.log_metric(
            "training_wall_seconds", time.time() - start_time
        )

        print(f"✓ LoRA fine-tuning complete. Run ID: {run.info.run_id}")
        print(f"  Adapters saved to MLflow artifacts: adapters/{run.info.run_id}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LoRA fine-tuning for an LLM.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML trainer config (LLMTrainerConfig).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config_data = yaml.safe_load(Path(args.config).read_text())
    config = LLMTrainerConfig(**config_data)
    run_lora_fine_tuning(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
