"""
Purpose:
    End-to-end model training pipeline.
    Chains data_ingestion → preprocessing → training → evaluation → registration
    components into a single executable pipeline.

    Supports two execution modes:
    - local:  runs all components in-process (for local development)
    - argo:   generates and submits an Argo Workflows manifest

Usage:
    # Local mode
    python pipelines/training_pipeline.py \\
        --config-file pipelines/config/fraud-detection.yaml \\
        --mode local

Dependencies:
    pandas>=2.0
    scikit-learn>=1.4
    mlflow>=2.11
    pyarrow>=14.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import logging
import tempfile
from pathlib import Path
from typing import Any

import yaml

from pipelines.components.data_ingestion.component import ingest
from pipelines.components.preprocessing.component import preprocess
from pipelines.components.training.component import train
from pipelines.components.evaluation.component import evaluate
from pipelines.components.registration.component import register

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_training_pipeline(config: dict[str, Any]) -> None:
    """
    Execute the end-to-end training pipeline locally.

    Steps:
        1. Ingest raw data
        2. Preprocess (split + scale)
        3. Train model, log to MLflow
        4. Evaluate on test split
        5. Register to Staging if thresholds pass
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path     = f"{tmpdir}/raw.parquet"
        processed_dir = f"{tmpdir}/processed/"
        run_id_path  = f"{tmpdir}/run_id.txt"
        metrics_path = f"{tmpdir}/metrics.json"

        logger.info("=== Step 1: Data ingestion ===")
        ingest(
            source_uri=config["source_uri"],
            output_path=raw_path,
            config=config.get("ingestion", {}),
        )

        logger.info("=== Step 2: Preprocessing ===")
        preprocess(
            input_path=raw_path,
            output_dir=processed_dir,
            config=config,
        )

        logger.info("=== Step 3: Training ===")
        train(
            data_dir=processed_dir,
            run_id_path=run_id_path,
            config=config,
        )

        logger.info("=== Step 4: Evaluation ===")
        evaluate(
            run_id_path=run_id_path,
            data_dir=processed_dir,
            metrics_path=metrics_path,
            config=config,
        )

        logger.info("=== Step 5: Registration ===")
        register(
            run_id_path=run_id_path,
            metrics_path=metrics_path,
            config=config,
        )

    logger.info("Training pipeline complete.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="End-to-end training pipeline.")
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--mode", default="local", choices=["local", "argo"])
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    if args.mode == "local":
        run_training_pipeline(config)
    else:
        raise NotImplementedError("Use ci/github-actions/pipelines/trigger-training-pipeline.yml for Argo mode.")
