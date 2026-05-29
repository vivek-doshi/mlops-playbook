"""
Purpose:
    Distributed model training entry-point using Ray Train.
    This module defines a standard training loop that runs on a Ray cluster
    (local or KubeRay) with:
      - MLflow experiment tracking
      - DVC data loading
      - Checkpointing via Ray Train's checkpoint API
      - Automatic model registration after training

Usage (local):
    python training/ray/train_distributed.py \\
        --config training/config/fraud-detection.yaml

Usage (Ray cluster):
    ray job submit --working-dir . \\
        -- python training/ray/train_distributed.py \\
               --config training/config/fraud-detection.yaml

Dependencies:
    ray[train]>=2.9
    torch>=2.2
    mlflow>=2.11
    pandas>=2.0
    scikit-learn>=1.4
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

# Ray imports — optional at import time so the module can be unit-tested
# without a Ray cluster present.
try:
    import ray
    from ray import train as ray_train
    from ray.train import Checkpoint, ScalingConfig
    from ray.train.torch import TorchTrainer
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

import mlflow
import pandas as pd


# --------------------------------------------------------------------------- #
# Config loading
# --------------------------------------------------------------------------- #


def _load_config(config_path: str) -> dict[str, Any]:
    with open(config_path) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Training function (runs inside each Ray worker)
# --------------------------------------------------------------------------- #


def _train_loop_per_worker(config: dict[str, Any]) -> None:
    """
    Single-worker training loop executed by Ray Train on each worker process.
    Uses PyTorch DDP under the hood via TorchTrainer.

    config keys:
        mlflow_tracking_uri  : str
        experiment_name      : str
        model_name           : str
        data_path            : str
        epochs               : int
        batch_size           : int
        learning_rate        : float
        checkpoint_dir       : str (optional)
    """
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    from sklearn.preprocessing import StandardScaler

    mlflow_uri  = config.get("mlflow_tracking_uri", os.environ.get("MLFLOW_TRACKING_URI", ""))
    exp_name    = config.get("experiment_name", "distributed-training")
    model_name  = config.get("model_name", "distributed-model")
    data_path   = config.get("data_path", "data/train_features.parquet")
    epochs      = config.get("epochs", 10)
    batch_size  = config.get("batch_size", 256)
    lr          = config.get("learning_rate", 1e-3)

    # Only the rank-0 worker logs to MLflow to avoid duplicate runs.
    is_rank_zero = ray_train.get_context().get_world_rank() == 0

    if mlflow_uri:
        mlflow.set_tracking_uri(mlflow_uri)

    if is_rank_zero:
        mlflow.set_experiment(exp_name)
        mlflow.start_run(run_name=f"{model_name}-distributed")
        mlflow.log_params(
            {
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": lr,
                "num_workers": ray_train.get_context().get_world_size(),
            }
        )

    # ---- Data loading ---------------------------------------------------- #
    df = pd.read_parquet(data_path)
    X = df.drop(columns=["label"]).values
    y = df["label"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.long)
    dataset  = TensorDataset(X_tensor, y_tensor)

    # Distributed sampler is handled automatically by TorchTrainer.
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # ---- Model ----------------------------------------------------------- #
    input_dim  = X.shape[1]
    output_dim = int(y.max()) + 1

    model = nn.Sequential(
        nn.Linear(input_dim, 128),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(128, 64),
        nn.ReLU(),
        nn.Linear(64, output_dim),
    )

    # Wrap with DDP.
    model = ray_train.torch.prepare_model(model)
    loader = ray_train.torch.prepare_data_loader(loader)

    criterion  = nn.CrossEntropyLoss()
    optimiser  = torch.optim.Adam(model.parameters(), lr=lr)

    # ---- Training loop --------------------------------------------------- #
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        correct    = 0
        for X_batch, y_batch in loader:
            optimiser.zero_grad()
            logits = model(X_batch)
            loss   = criterion(logits, y_batch)
            loss.backward()
            optimiser.step()
            total_loss += loss.item() * len(y_batch)
            correct    += (logits.argmax(dim=1) == y_batch).sum().item()

        avg_loss = total_loss / len(dataset)
        accuracy = correct / len(dataset)

        if is_rank_zero:
            mlflow.log_metrics(
                {"train_loss": avg_loss, "train_accuracy": accuracy},
                step=epoch,
            )

        # Checkpoint after each epoch (rank 0 only).
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = Path(tmpdir) / "model.pt"
            if is_rank_zero:
                torch.save(
                    {
                        "epoch":       epoch,
                        "model_state": model.module.state_dict()
                        if hasattr(model, "module")
                        else model.state_dict(),
                        "optim_state": optimiser.state_dict(),
                        "train_loss":  avg_loss,
                        "train_accuracy": accuracy,
                    },
                    ckpt_path,
                )
            checkpoint = Checkpoint.from_directory(tmpdir)
            ray_train.report(
                {"train_loss": avg_loss, "train_accuracy": accuracy},
                checkpoint=checkpoint,
            )

    if is_rank_zero:
        mlflow.end_run()


# --------------------------------------------------------------------------- #
# Training job entry-point
# --------------------------------------------------------------------------- #


def run_training(config: dict[str, Any]) -> None:
    """
    Launch a distributed Ray Train job with the given config dict.
    """
    if not HAS_RAY:
        print("ERROR: ray is not installed.", file=sys.stderr)
        sys.exit(1)

    num_workers = config.get("num_workers", 2)
    use_gpu     = config.get("use_gpu", True)

    trainer = TorchTrainer(
        train_loop_per_worker=_train_loop_per_worker,
        train_loop_config=config,
        scaling_config=ScalingConfig(
            num_workers=num_workers,
            use_gpu=use_gpu,
            resources_per_worker={
                "CPU": config.get("cpu_per_worker", 4),
                "GPU": 1 if use_gpu else 0,
            },
        ),
    )

    result = trainer.fit()
    print(f"Training complete. Best checkpoint: {result.checkpoint}")
    print(f"Metrics: {result.metrics}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Distributed training launcher using Ray Train."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to training config YAML",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    cfg  = _load_config(args.config)
    run_training(cfg)
