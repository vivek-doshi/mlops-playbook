"""
Purpose:
    Triggered retraining pipeline.
    Checks drift scores from Evidently, runs a full training pipeline only if
    drift is detected, and auto-promotes to Production if new metrics improve on
    the current Production model.

Usage:
    python pipelines/retraining_pipeline.py \\
        --config-file pipelines/config/fraud-detection.yaml \\
        --drift-report monitoring/evidently/drift_report.json

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

import mlflow
from mlflow.tracking import MlflowClient
import yaml

from pipelines.training_pipeline import run_training_pipeline

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _load_drift_report(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _drift_detected(report: dict, threshold: float) -> bool:
    """Return True if any feature's drift score exceeds *threshold*."""
    drift_scores = (
        report.get("data_drift", {})
              .get("metrics", {})
              .get("dataset_drift", False)
    )
    if isinstance(drift_scores, bool):
        return drift_scores
    score = report.get("data_drift", {}).get("metrics", {}).get("share_drifted_features", 0.0)
    return float(score) >= threshold


def _get_production_auc(model_name: str) -> float | None:
    """Return the test_auc of the current Production model version, or None."""
    client = MlflowClient()
    prod_versions = client.get_latest_versions(model_name, stages=["Production"])
    if not prod_versions:
        return None
    run_id = prod_versions[0].run_id
    run    = client.get_run(run_id)
    return run.data.metrics.get("test_auc")


def run_retraining_pipeline(config: dict[str, Any], drift_report_path: str) -> None:
    """
    Conditionally retrain and auto-promote if metrics improve.
    """
    drift_threshold = config.get("retraining", {}).get("drift_threshold", 0.1)
    tracking        = config.get("mlflow_tracking_uri")
    model_name      = config.get("model_name", "my-model")

    if tracking:
        mlflow.set_tracking_uri(tracking)

    report = _load_drift_report(drift_report_path)

    if not _drift_detected(report, drift_threshold):
        logger.info("No significant drift detected (threshold=%.2f). Skipping retraining.", drift_threshold)
        return

    logger.info("Drift detected — triggering full retraining pipeline.")
    run_training_pipeline(config)

    # Compare new Staging model against Production.
    client       = MlflowClient()
    prod_auc     = _get_production_auc(model_name)
    staging_vers = client.get_latest_versions(model_name, stages=["Staging"])

    if not staging_vers:
        logger.warning("No Staging version found after retraining.")
        return

    new_run      = client.get_run(staging_vers[0].run_id)
    new_auc      = new_run.data.metrics.get("test_auc", 0.0)
    new_version  = staging_vers[0].version

    if prod_auc is None or new_auc > prod_auc:
        logger.info(
            "New model AUC=%.4f > Production AUC=%s — auto-promoting v%s.",
            new_auc, prod_auc, new_version,
        )
        client.transition_model_version_stage(
            name=model_name, version=new_version,
            stage="Production", archive_existing_versions=True,
        )
    else:
        logger.info(
            "New model AUC=%.4f did NOT improve over Production AUC=%.4f — leaving in Staging.",
            new_auc, prod_auc,
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retraining pipeline.")
    parser.add_argument("--config-file",    required=True)
    parser.add_argument("--drift-report",   required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    run_retraining_pipeline(config, args.drift_report)
