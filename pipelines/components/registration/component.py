"""
Purpose:
    Model registration pipeline component.
    Reads evaluation metrics, compares them against thresholds, and
    transitions the MLflow model to the Staging stage if all gates pass.
    Exits 1 if any threshold is not met, blocking the pipeline.

Usage:
    Called as a pipeline step.  Standalone:
        python pipelines/components/registration/component.py \\
            --run-id-path /tmp/run_id.txt \\
            --metrics-path /tmp/metrics.json \\
            --config-file pipelines/config/fraud-detection.yaml

Dependencies:
    mlflow>=2.11
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient

import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def register(
    run_id_path: str,
    metrics_path: str,
    config: dict[str, Any],
) -> str:
    """
    Gate + promote model to Staging.  Returns the model version.
    """
    model_name = config.get("model_name",         "my-model")
    tracking   = config.get("mlflow_tracking_uri")
    thresholds = config.get("registration_thresholds", {})

    if tracking:
        mlflow.set_tracking_uri(tracking)

    run_id  = Path(run_id_path).read_text().strip()
    metrics = json.loads(Path(metrics_path).read_text())

    # Evaluate thresholds.
    failures: list[str] = []
    for metric, threshold in thresholds.items():
        actual = metrics.get(metric)
        if actual is None:
            failures.append(f"Metric '{metric}' not found in evaluation output")
            continue
        if actual < threshold:
            failures.append(f"{metric}={actual:.4f} below threshold={threshold}")

    if failures:
        logger.error("Registration gate FAILED:")
        for f in failures:
            logger.error("  - %s", f)
        sys.exit(1)

    # Register and promote.
    client  = MlflowClient()
    model_uri = f"runs:/{run_id}/model"
    result    = mlflow.register_model(model_uri=model_uri, name=model_name)
    version   = result.version

    client.transition_model_version_stage(
        name=model_name, version=version, stage="Staging"
    )
    logger.info("Registered model %s version %s → Staging", model_name, version)
    return version


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Registration component.")
    parser.add_argument("--run-id-path",  required=True)
    parser.add_argument("--metrics-path", required=True)
    parser.add_argument("--config-file",  required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    register(args.run_id_path, args.metrics_path, config)
