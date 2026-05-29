"""
Purpose:
    Kubeflow PyTorch distributed training script using torch.distributed
    and the Kubeflow Training Operator environment variables for rank/size
    discovery.

Usage:
    python training/kubeflow/train_pytorch.py --config training/config/model.yaml

    The Kubeflow Training Operator injects:
        MASTER_ADDR, MASTER_PORT, RANK, WORLD_SIZE
    so that torch.distributed.init_process_group() picks them up automatically.

Dependencies:
    torch>=2.2
    mlflow>=2.11
    pandas>=2.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, TensorDataset, DistributedSampler

import mlflow
import pandas as pd
import yaml
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


def _load_config(path: str) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #


def _build_model(input_dim: int, output_dim: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(input_dim, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, output_dim),
    )


# --------------------------------------------------------------------------- #
# Training loop
# --------------------------------------------------------------------------- #


def train(config: dict[str, Any]) -> None:
    # ---- Distributed setup ---------------------------------------------- #
    backend  = config.get("dist_backend", "nccl" if torch.cuda.is_available() else "gloo")
    dist.init_process_group(backend=backend)

    rank       = dist.get_rank()
    world_size = dist.get_world_size()
    device     = torch.device(f"cuda:{rank}" if torch.cuda.is_available() else "cpu")

    # ---- MLflow (rank 0 only) ------------------------------------------- #
    mlflow_uri = config.get("mlflow_tracking_uri", os.environ.get("MLFLOW_TRACKING_URI", ""))
    if mlflow_uri:
        mlflow.set_tracking_uri(mlflow_uri)
    if rank == 0:
        mlflow.set_experiment(config.get("experiment_name", "pytorch-distributed"))
        mlflow.start_run(run_name=config.get("model_name", "pytorch-model"))
        mlflow.log_params(
            {
                "world_size": world_size,
                "epochs":     config.get("epochs", 10),
                "batch_size": config.get("batch_size", 256),
                "lr":         config.get("learning_rate", 1e-3),
            }
        )

    # ---- Data ------------------------------------------------------------ #
    df = pd.read_parquet(config["data_path"])
    X  = df.drop(columns=["label"]).values
    y  = df["label"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    dataset  = TensorDataset(
        torch.tensor(X, dtype=torch.float32),
        torch.tensor(y, dtype=torch.long),
    )
    sampler  = DistributedSampler(dataset, num_replicas=world_size, rank=rank)
    loader   = DataLoader(
        dataset,
        batch_size=config.get("batch_size", 256),
        sampler=sampler,
        num_workers=2,
        pin_memory=True,
    )

    # ---- Model ----------------------------------------------------------- #
    input_dim  = X.shape[1]
    output_dim = int(y.max()) + 1

    model = _build_model(input_dim, output_dim).to(device)
    model = DDP(model, device_ids=[rank] if torch.cuda.is_available() else None)

    criterion = nn.CrossEntropyLoss()
    optimiser = torch.optim.Adam(model.parameters(), lr=config.get("learning_rate", 1e-3))

    # ---- Training -------------------------------------------------------- #
    epochs     = config.get("epochs", 10)
    ckpt_dir   = Path(config.get("checkpoint_dir", "/checkpoints"))
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(epochs):
        sampler.set_epoch(epoch)
        model.train()

        total_loss = 0.0
        correct    = 0

        for X_batch, y_batch in loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimiser.zero_grad()
            logits = model(X_batch)
            loss   = criterion(logits, y_batch)
            loss.backward()
            optimiser.step()
            total_loss += loss.item() * len(y_batch)
            correct    += (logits.argmax(1) == y_batch).sum().item()

        avg_loss = total_loss / len(dataset)
        accuracy = correct / len(dataset)

        if rank == 0:
            logger.info("Epoch %d/%d  loss=%.4f  acc=%.4f", epoch + 1, epochs, avg_loss, accuracy)
            mlflow.log_metrics({"train_loss": avg_loss, "train_accuracy": accuracy}, step=epoch)

            # Save checkpoint.
            ckpt_path = ckpt_dir / f"epoch-{epoch:05d}.pt"
            torch.save(
                {
                    "epoch":       epoch,
                    "model_state": model.module.state_dict(),
                    "optim_state": optimiser.state_dict(),
                    "metrics":     {"train_loss": avg_loss, "train_accuracy": accuracy},
                },
                ckpt_path,
            )

    # ---- Finalise -------------------------------------------------------- #
    if rank == 0:
        mlflow.log_artifact(str(ckpt_dir))
        mlflow.end_run()

    dist.destroy_process_group()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kubeflow PyTorch distributed training.")
    parser.add_argument("--config", required=True, help="Path to training config YAML")
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = _load_config(args.config)
    train(config)
