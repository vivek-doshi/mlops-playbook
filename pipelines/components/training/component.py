"""
Purpose:
    Model training pipeline component.
    Trains a model on preprocessed train/val splits, logs metrics and
    the trained model artifact to MLflow, and writes the MLflow run ID
    to a file for downstream components.

Usage:
    Called as a pipeline step.  Standalone:
        python pipelines/components/training/component.py \\
            --data-dir /tmp/processed/ \\
            --run-id-path /tmp/run_id.txt \\
            --config-file pipelines/config/fraud-detection.yaml

Dependencies:
    mlflow>=2.11
    scikit-learn>=1.4
    pandas>=2.0
    pyarrow>=14.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_MODELS = {
    "random_forest":        RandomForestClassifier,
    "gradient_boosting":    GradientBoostingClassifier,
    "logistic_regression":  LogisticRegression,
}


def train(
    data_dir: str,
    run_id_path: str,
    config: dict[str, Any],
) -> str:
    """
    Train and log model.  Returns the MLflow run ID.
    """
    label_col  = config.get("label_column",    "label")
    model_type = config.get("model_type",      "random_forest")
    model_name = config.get("model_name",      "my-model")
    experiment  = config.get("experiment_name", f"{model_name}-dev")
    tracking   = config.get("mlflow_tracking_uri")
    params     = config.get("model_params", {})

    if tracking:
        mlflow.set_tracking_uri(tracking)

    mlflow.set_experiment(experiment)

    d        = Path(data_dir)
    train_df = pd.read_parquet(d / "train.parquet")
    val_df   = pd.read_parquet(d / "val.parquet")

    X_train = train_df.drop(columns=[label_col])
    y_train = train_df[label_col]
    X_val   = val_df.drop(columns=[label_col])
    y_val   = val_df[label_col]

    model_cls = _MODELS.get(model_type)
    if model_cls is None:
        raise ValueError(f"Unknown model_type: {model_type}. Choices: {list(_MODELS)}")

    model = model_cls(**params)

    with mlflow.start_run() as run:
        mlflow.log_params({"model_type": model_type, **params})
        model.fit(X_train, y_train)

        val_preds = model.predict(X_val)
        val_proba = model.predict_proba(X_val)[:, 1] if hasattr(model, "predict_proba") else val_preds

        metrics = {
            "val_f1":  f1_score(y_val, val_preds, average="weighted"),
            "val_auc": roc_auc_score(y_val, val_proba),
        }
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, artifact_path="model", registered_model_name=model_name)
        logger.info("Logged model to MLflow run %s  metrics=%s", run.info.run_id, metrics)

        run_id = run.info.run_id

    Path(run_id_path).parent.mkdir(parents=True, exist_ok=True)
    Path(run_id_path).write_text(run_id)
    return run_id


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Training component.")
    parser.add_argument("--data-dir",    required=True)
    parser.add_argument("--run-id-path", required=True)
    parser.add_argument("--config-file", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    train(args.data_dir, args.run_id_path, config)
