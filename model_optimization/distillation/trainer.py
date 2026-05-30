"""
Purpose:
    Knowledge distillation training loop.  Trains a smaller student model to
    mimic the output distribution of a larger teacher model using KL-divergence
    loss between teacher soft logits and student predictions.

    The teacher model must be in Production stage in the MLflow Model Registry.
    The student architecture is defined in a YAML config under
    ``model_optimization/distillation/student_configs/``.

Usage:
    python model_optimization/distillation/trainer.py \\
        --teacher-model-uri  models:/my-model/3 \\
        --student-config     model_optimization/distillation/student_configs/small.yaml \\
        --dataset-path       data/train_hf/ \\
        --model-name         my-model-distilled \\
        --num-epochs         5

Dependencies:
    mlflow>=2.14
    torch>=2.2
    transformers>=4.40
    datasets>=2.18
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import mlflow
    import torch
    import torch.nn.functional as F
    import yaml
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from datasets import Dataset, load_from_disk
except ImportError as exc:
    print(
        f"ERROR: {exc}\nInstall with: pip install mlflow torch transformers datasets pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


def _load_student_config(config_path: Path) -> dict[str, Any]:
    with config_path.open() as fh:
        return yaml.safe_load(fh)


def _load_teacher(model_uri: str, device: str) -> torch.nn.Module:
    model = mlflow.pytorch.load_model(model_uri)
    model.eval()
    model.to(device)
    return model


def _build_student(config: dict[str, Any], num_labels: int, device: str) -> torch.nn.Module:
    arch = config.get("architecture", "distilbert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained(arch, num_labels=num_labels)
    model.to(device)
    return model


def distillation_loss(
    student_logits: torch.Tensor,
    teacher_logits: torch.Tensor,
    labels: torch.Tensor,
    temperature: float = 4.0,
    alpha: float = 0.7,
) -> torch.Tensor:
    """
    Combined KL-divergence distillation loss + hard-label cross-entropy.

    Parameters
    ----------
    student_logits : Tensor  [B, num_labels]
    teacher_logits : Tensor  [B, num_labels]
    labels : Tensor          [B]
    temperature : float      Softmax temperature (higher → softer targets)
    alpha : float            Weight of the distillation loss (1-alpha → hard label)
    """
    soft_teacher = F.softmax(teacher_logits / temperature, dim=-1)
    soft_student = F.log_softmax(student_logits / temperature, dim=-1)
    kl_loss = F.kl_div(soft_student, soft_teacher, reduction="batchmean") * (temperature ** 2)
    ce_loss = F.cross_entropy(student_logits, labels)
    return alpha * kl_loss + (1.0 - alpha) * ce_loss


def run_distillation(
    teacher_model_uri: str,
    student_config_path: Path,
    dataset_path: str,
    model_name: str,
    num_epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 5e-5,
    temperature: float = 4.0,
    alpha: float = 0.7,
    tracking_uri: str = "http://localhost:5000",
) -> str:
    """Train a student model via knowledge distillation and log to MLflow."""
    mlflow.set_tracking_uri(tracking_uri)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    student_config = _load_student_config(student_config_path)

    print("Loading teacher model ...")
    teacher = _load_teacher(teacher_model_uri, device)

    # Infer num_labels from teacher
    num_labels = getattr(teacher.config, "num_labels", 2)

    print("Building student model ...")
    student = _build_student(student_config, num_labels, device)

    tokenizer_name = student_config.get("tokenizer", "distilbert-base-uncased")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    print(f"Loading dataset from {dataset_path} ...")
    dataset = load_from_disk(dataset_path)
    text_col = student_config.get("text_column", "text")
    label_col = student_config.get("label_column", "label")

    def tokenise(batch):
        return tokenizer(
            batch[text_col], truncation=True, padding="max_length", max_length=128
        )

    dataset = dataset.map(tokenise, batched=True)
    dataset.set_format("torch", columns=["input_ids", "attention_mask", label_col])
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimiser = torch.optim.AdamW(student.parameters(), lr=learning_rate)

    exp_name = f"{model_name}-distillation"
    mlflow.set_experiment(exp_name)

    with mlflow.start_run(run_name=f"{model_name}-distill") as run:
        mlflow.log_params(
            {
                "teacher_model_uri": teacher_model_uri,
                "student_architecture": student_config.get("architecture"),
                "num_epochs": num_epochs,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "temperature": temperature,
                "alpha": alpha,
            }
        )

        for epoch in range(num_epochs):
            student.train()
            total_loss = 0.0
            for batch in loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch[label_col].to(device)

                with torch.no_grad():
                    teacher_outputs = teacher(
                        input_ids=input_ids, attention_mask=attention_mask
                    )
                    teacher_logits = teacher_outputs.logits

                student_outputs = student(
                    input_ids=input_ids, attention_mask=attention_mask
                )
                loss = distillation_loss(
                    student_outputs.logits,
                    teacher_logits,
                    labels,
                    temperature=temperature,
                    alpha=alpha,
                )
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(loader)
            mlflow.log_metric("distillation_loss", avg_loss, step=epoch)
            print(f"  Epoch {epoch + 1}/{num_epochs} — loss: {avg_loss:.4f}")

        # Save and log student
        save_dir = Path(f"outputs/distilled/{model_name}/{run.info.run_id}/")
        save_dir.mkdir(parents=True, exist_ok=True)
        student.save_pretrained(str(save_dir))
        tokenizer.save_pretrained(str(save_dir))
        mlflow.log_artifacts(str(save_dir), artifact_path="student_model")
        mlflow.register_model(
            model_uri=f"runs:/{run.info.run_id}/student_model",
            name=f"{model_name}-distilled",
        )
        print(f"✓ Distilled model registered as {model_name}-distilled  run_id={run.info.run_id}")
        return run.info.run_id


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Knowledge distillation trainer.")
    parser.add_argument("--teacher-model-uri", required=True)
    parser.add_argument("--student-config", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--num-epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--temperature", type=float, default=4.0)
    parser.add_argument("--alpha", type=float, default=0.7)
    parser.add_argument("--tracking-uri", default="http://localhost:5000")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    run_distillation(
        teacher_model_uri=args.teacher_model_uri,
        student_config_path=Path(args.student_config),
        dataset_path=args.dataset_path,
        model_name=args.model_name,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        temperature=args.temperature,
        alpha=args.alpha,
        tracking_uri=args.tracking_uri,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
