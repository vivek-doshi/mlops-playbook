"""
Purpose:
    Reward model training for RLHF pipelines.  Trains a reward model from a
    dataset of (prompt, chosen_response, rejected_response) preference triples.
    The reward model predicts a scalar reward for (prompt, response) pairs, which
    is then consumed by the PPO trainer.

    Training metrics and the serialised reward model are logged to MLflow under
    the experiment <model_name>-llm-reward.

Usage:
    python llmops/rlhf/reward_model.py \\
        --base-model   <hf-model-id> \\
        --dataset-path <dataset-path> \\
        --model-name   <name> \\
        --num-epochs   3

Dependencies:
    transformers>=4.40
    trl>=0.8
    torch>=2.2
    datasets>=2.18
    mlflow>=2.11
    accelerate>=0.28
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    import mlflow
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from trl import RewardConfig, RewardTrainer
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install transformers trl torch datasets mlflow accelerate",
        file=sys.stderr,
    )
    sys.exit(1)


def train_reward_model(
    model_name: str,
    base_model: str,
    dataset_path: str,
    num_epochs: int = 3,
    learning_rate: float = 1e-5,
    batch_size: int = 4,
    max_seq_length: int = 512,
    output_dir: str = "outputs/reward_model",
) -> None:
    """Train a reward model and log artifacts to MLflow."""
    experiment_name = f"{model_name}-llm-reward"
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(
        tags={"llm_task": "reward_model", "base_model": base_model}
    ) as run:
        mlflow.log_params(
            {
                "base_model": base_model,
                "dataset": dataset_path,
                "num_epochs": num_epochs,
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "max_seq_length": max_seq_length,
            }
        )

        tokenizer = AutoTokenizer.from_pretrained(base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Reward model: sequence classification head (num_labels=1)
        reward_model = AutoModelForSequenceClassification.from_pretrained(
            base_model,
            num_labels=1,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        reward_model.config.pad_token_id = tokenizer.pad_token_id

        dataset = load_dataset(dataset_path, split="train")

        def preprocess(sample: dict) -> dict:
            tokenized_chosen = tokenizer(
                sample["prompt"] + sample["chosen"],
                truncation=True,
                max_length=max_seq_length,
            )
            tokenized_rejected = tokenizer(
                sample["prompt"] + sample["rejected"],
                truncation=True,
                max_length=max_seq_length,
            )
            return {
                "input_ids_chosen": tokenized_chosen["input_ids"],
                "attention_mask_chosen": tokenized_chosen["attention_mask"],
                "input_ids_rejected": tokenized_rejected["input_ids"],
                "attention_mask_rejected": tokenized_rejected["attention_mask"],
            }

        dataset = dataset.map(preprocess, remove_columns=dataset.column_names)

        run_output_dir = str(Path(output_dir) / run.info.run_id)
        reward_config = RewardConfig(
            output_dir=run_output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            report_to="none",
            logging_steps=50,
            max_length=max_seq_length,
        )

        start_time = time.time()
        trainer = RewardTrainer(
            model=reward_model,
            tokenizer=tokenizer,
            args=reward_config,
            train_dataset=dataset,
        )
        trainer.train()

        model_dir = Path(run_output_dir) / "reward_model"
        model_dir.mkdir(parents=True, exist_ok=True)
        reward_model.save_pretrained(str(model_dir))
        tokenizer.save_pretrained(str(model_dir))

        mlflow.log_artifacts(str(model_dir), artifact_path="reward_model")
        mlflow.log_metric("training_wall_seconds", time.time() - start_time)

        print(f"✓ Reward model training complete. Run ID: {run.info.run_id}")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train an RLHF reward model.")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--num-epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-seq-length", type=int, default=512)
    parser.add_argument("--output-dir", default="outputs/reward_model")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    train_reward_model(
        model_name=args.model_name,
        base_model=args.base_model,
        dataset_path=args.dataset_path,
        num_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        max_seq_length=args.max_seq_length,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
