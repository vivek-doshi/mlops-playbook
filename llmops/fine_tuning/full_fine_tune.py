"""
Purpose:
    Full-parameter fine-tuning of an LLM (no adapters).  Used when the model
    is small enough to fine-tune end-to-end or when an adapter approach does
    not satisfy the target quality threshold.  Gradient checkpointing is
    enabled by default to reduce GPU memory requirements.

Usage:
    python llmops/fine_tuning/full_fine_tune.py \\
        --config llmops/fine_tuning/configs/full-finetune-config.yaml

Dependencies:
    transformers>=4.40
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

import yaml

try:
    import mlflow
    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install transformers torch datasets mlflow accelerate",
        file=sys.stderr,
    )
    sys.exit(1)

from llmops.fine_tuning.trainer_config import LLMTrainerConfig


def run_full_fine_tune(config: LLMTrainerConfig) -> None:
    """Execute full-parameter fine-tuning and log model + metrics to MLflow."""
    experiment_name = f"{config.model_name}-llm-finetune"
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(
        tags={"llm_task": "finetune", "base_model": config.base_model, "mode": "full"}
    ) as run:
        mlflow.log_params(
            {
                "base_model": config.base_model,
                "mode": "full",
                "learning_rate": config.learning_rate,
                "num_epochs": config.num_epochs,
                "batch_size": config.batch_size,
                "max_seq_length": config.max_seq_length,
            }
        )

        tokenizer = AutoTokenizer.from_pretrained(config.base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            config.base_model,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )

        dataset = load_dataset(config.dataset_path, split="train")
        if config.eval_dataset_path:
            eval_dataset = load_dataset(config.eval_dataset_path, split="validation")
        else:
            split = dataset.train_test_split(test_size=0.05, seed=42)
            dataset, eval_dataset = split["train"], split["test"]

        def tokenize(batch):
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

        training_args = TrainingArguments(
            output_dir=str(Path(config.output_dir) / run.info.run_id),
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            bf16=torch.cuda.is_available(),
            gradient_checkpointing=True,
            report_to="none",
            logging_steps=50,
        )

        start_time = time.time()
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            eval_dataset=eval_dataset,
            data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        )

        trainer.train()

        eval_results = trainer.evaluate()
        for k, v in eval_results.items():
            if isinstance(v, float):
                mlflow.log_metric(k, v)
        if "eval_loss" in eval_results:
            try:
                mlflow.log_metric("perplexity", math.exp(eval_results["eval_loss"]))
            except OverflowError:
                mlflow.log_metric("perplexity", float("inf"))

        # Save full model
        model_dir = Path(config.output_dir) / "model" / run.info.run_id
        model_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(model_dir))
        tokenizer.save_pretrained(str(model_dir))

        mlflow.transformers.log_model(
            transformers_model={"model": model, "tokenizer": tokenizer},
            artifact_path="model",
        )
        mlflow.log_metric("training_wall_seconds", time.time() - start_time)

        print(f"✓ Full fine-tune complete. Run ID: {run.info.run_id}")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run full-parameter LLM fine-tuning.")
    parser.add_argument("--config", required=True, help="Path to YAML trainer config.")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    config_data = yaml.safe_load(Path(args.config).read_text())
    config = LLMTrainerConfig(**config_data)
    run_full_fine_tune(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
