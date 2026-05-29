"""
Purpose:
    Model evaluation pipeline component.
    Loads a trained model from MLflow, evaluates it on the test split,
    and writes evaluation metrics to a JSON file for the registration gate.

Usage:
    Called as a pipeline step.  Standalone:
        python pipelines/components/evaluation/component.py \\
            --run-id-path /tmp/run_id.txt \\
            --data-dir /tmp/processed/ \\
            --metrics-path /tmp/metrics.json \\
            --config-file pipelines/config/fraud-detection.yaml

Dependencies:
    mlflow>=2.11
    pandas>=2.0
    scikit-learn>=1.4
    pyarrow>=14.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import mlflow.pyfunc
import pandas as pd
import yaml
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def evaluate(
    run_id_path: str,
    data_dir: str,
    metrics_path: str,
    config: dict[str, Any],
) -> dict[str, float]:
    """
    Evaluate model on test split.  Returns a metrics dict.
    """
    label_col = config.get("label_column", "label")
    tracking  = config.get("mlflow_tracking_uri")

    if tracking:
        import mlflow
        mlflow.set_tracking_uri(tracking)

    run_id = Path(run_id_path).read_text().strip()
    model  = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")

    test_df = pd.read_parquet(Path(data_dir) / "test.parquet")
    X_test  = test_df.drop(columns=[label_col])
    y_test  = test_df[label_col]

    preds = model.predict(X_test)

    try:
        proba = model.predict_proba(X_test)[:, 1]
        auc   = float(roc_auc_score(y_test, proba))
    except (AttributeError, TypeError):
        auc   = 0.0

    metrics: dict[str, float] = {
        "test_accuracy":  float(accuracy_score(y_test, preds)),
        "test_f1":        float(f1_score(y_test, preds, average="weighted")),
        "test_precision": float(precision_score(y_test, preds, average="weighted")),
        "test_recall":    float(recall_score(y_test, preds, average="weighted")),
        "test_auc":       auc,
    }
    logger.info("Evaluation metrics: %s", metrics)

    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
    Path(metrics_path).write_text(json.dumps(metrics, indent=2))

    return metrics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluation component.")
    parser.add_argument("--run-id-path",  required=True)
    parser.add_argument("--data-dir",     required=True)
    parser.add_argument("--metrics-path", required=True)
    parser.add_argument("--config-file",  required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    evaluate(args.run_id_path, args.data_dir, args.metrics_path, config)
