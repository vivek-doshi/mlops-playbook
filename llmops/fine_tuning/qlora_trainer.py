"""
Purpose:
    QLoRA fine-tuning trainer.  Extends LoRA training with 4-bit NF4 quantisation
    (BitsAndBytesConfig) to fit large base models on a single consumer GPU.
    Adapters and metrics are logged to MLflow identically to the LoRA trainer.

Usage:
    python llmops/fine_tuning/qlora_trainer.py \\
        --config llmops/fine_tuning/configs/qlora-config.yaml

Dependencies:
    transformers>=4.40
    peft>=0.10
    bitsandbytes>=0.43
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
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install transformers peft bitsandbytes torch datasets mlflow accelerate",
        file=sys.stderr,
    )
    sys.exit(1)

from llmops.fine_tuning.trainer_config import LLMTrainerConfig


def run_qlora_fine_tuning(config: LLMTrainerConfig) -> None:
    """Execute QLoRA (4-bit) fine-tuning and log adapters + metrics to MLflow."""
    experiment_name = f"{config.model_name}-llm-finetune"
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(
        tags={"llm_task": "finetune", "base_model": config.base_model, "quantisation": "4bit-nf4"}
    ) as run:
        mlflow.log_params(
            {
                "base_model": config.base_model,
                "quantisation": "4bit-nf4",
                "lora_r": config.lora_r,
                "lora_alpha": config.lora_alpha,
                "lora_dropout": config.lora_dropout,
                "learning_rate": config.learning_rate,
                "num_epochs": config.num_epochs,
                "batch_size": config.batch_size,
                "max_seq_length": config.max_seq_length,
            }
        )

        # ── BitsAndBytes 4-bit quantisation config ────────────────────────
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        tokenizer = AutoTokenizer.from_pretrained(config.base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            config.base_model,
            quantization_config=bnb_config,
            device_map="auto",
        )
        base_model = prepare_model_for_kbit_training(base_model)

        # ── LoRA adapters on quantised model ──────────────────────────────
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

        # ── Dataset ───────────────────────────────────────────────────────
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

        # ── Training ──────────────────────────────────────────────────────
        training_args = TrainingArguments(
            output_dir=str(Path(config.output_dir) / run.info.run_id),
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            bf16=True,
            report_to="none",
            logging_steps=50,
            gradient_checkpointing=True,
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

        # Log eval metrics
        eval_results = trainer.evaluate()
        for k, v in eval_results.items():
            if isinstance(v, float):
                mlflow.log_metric(k, v)
        if "eval_loss" in eval_results:
            try:
                mlflow.log_metric("perplexity", math.exp(eval_results["eval_loss"]))
            except OverflowError:
                mlflow.log_metric("perplexity", float("inf"))

        # ── Save adapters ─────────────────────────────────────────────────
        adapter_dir = Path(config.output_dir) / "adapters" / run.info.run_id
        adapter_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))

        mlflow.log_artifacts(str(adapter_dir), artifact_path=f"adapters/{run.info.run_id}")
        mlflow.log_metric("training_wall_seconds", time.time() - start_time)

        print(f"✓ QLoRA fine-tuning complete. Run ID: {run.info.run_id}")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run QLoRA (4-bit) fine-tuning for an LLM.")
    parser.add_argument("--config", required=True, help="Path to YAML trainer config.")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    config_data = yaml.safe_load(Path(args.config).read_text())
    config = LLMTrainerConfig(**config_data)
    run_qlora_fine_tuning(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
