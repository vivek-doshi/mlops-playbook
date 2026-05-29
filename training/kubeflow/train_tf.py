"""
Purpose:
    Kubeflow TFJob distributed training script using tf.distribute.MultiWorkerMirroredStrategy.
    The Kubeflow Training Operator injects the TF_CONFIG environment variable, which
    TensorFlow reads automatically to discover the cluster topology.

Usage:
    python training/kubeflow/train_tf.py --config training/config/model.yaml

    The Kubeflow Training Operator sets:
        TF_CONFIG — cluster spec and current task type/index

Dependencies:
    tensorflow>=2.15
    mlflow>=2.11
    pandas>=2.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


def _load_config(path: str) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh)


def _is_chief() -> bool:
    """Return True if this process is the chief/task-0 worker."""
    tf_config = json.loads(os.environ.get("TF_CONFIG", "{}"))
    task = tf_config.get("task", {})
    return task.get("type") == "chief" or (
        task.get("type") == "worker" and task.get("index") == 0
    )


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #


def train(config: dict[str, Any]) -> None:
    # Defer TF import so the module can be imported without TF installed.
    import tensorflow as tf  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

    strategy = tf.distribute.MultiWorkerMirroredStrategy()

    # ---- MLflow (chief only) --------------------------------------------- #
    mlflow_uri = config.get("mlflow_tracking_uri", os.environ.get("MLFLOW_TRACKING_URI", ""))
    chief      = _is_chief()

    if mlflow_uri:
        mlflow.set_tracking_uri(mlflow_uri)
    if chief:
        mlflow.set_experiment(config.get("experiment_name", "tf-distributed"))
        mlflow.start_run(run_name=config.get("model_name", "tf-model"))
        mlflow.log_params(
            {
                "epochs":     config.get("epochs", 10),
                "batch_size": config.get("batch_size", 256),
                "lr":         config.get("learning_rate", 1e-3),
            }
        )

    # ---- Data ---------------------------------------------------------------- #
    df = pd.read_parquet(config["data_path"])
    X  = df.drop(columns=["label"]).values.astype("float32")
    y  = df["label"].values.astype("int32")

    scaler = StandardScaler()
    X = scaler.fit_transform(X).astype("float32")

    batch_size = config.get("batch_size", 256)
    dataset = (
        tf.data.Dataset.from_tensor_slices((X, y))
        .shuffle(len(X))
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )

    # ---- Model (built inside strategy scope) -------------------------------- #
    input_dim  = X.shape[1]
    output_dim = int(y.max()) + 1

    with strategy.scope():
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(256, activation="relu", input_shape=(input_dim,)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dense(output_dim, activation="softmax"),
            ]
        )
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=config.get("learning_rate", 1e-3)),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

    # ---- Checkpointing ------------------------------------------------------- #
    ckpt_dir  = Path(config.get("checkpoint_dir", "/checkpoints"))
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(ckpt_dir / "epoch-{epoch:05d}.h5"),
            save_best_only=False,
        ),
    ]

    # ---- Training ------------------------------------------------------------ #
    history = model.fit(
        dataset,
        epochs=config.get("epochs", 10),
        callbacks=callbacks,
        verbose=1 if chief else 0,
    )

    # ---- Finalise (chief only) ------------------------------------------------ #
    if chief:
        for epoch, (loss, acc) in enumerate(
            zip(history.history["loss"], history.history["accuracy"])
        ):
            mlflow.log_metrics({"train_loss": loss, "train_accuracy": acc}, step=epoch)
        mlflow.end_run()
        logger.info("Training complete. Checkpoints saved to %s", ckpt_dir)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kubeflow TFJob distributed training.")
    parser.add_argument("--config", required=True, help="Path to training config YAML")
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = _load_config(args.config)
    train(config)
