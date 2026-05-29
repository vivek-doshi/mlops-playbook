"""
Purpose:
    Batch inference pipeline.
    Chains data_ingestion → batch_scorer → output_quality_gate → downstream_notifier
    into a single executable pipeline.

Usage:
    python pipelines/batch_inference_pipeline.py \\
        --job-config batch/jobs/fraud-detection-production-batch-job.yaml \\
        --mode local

Dependencies:
    mlflow>=2.11
    pandas>=2.0
    pyarrow>=14.0
    pyyaml>=6.0
    requests>=2.31
"""

from __future__ import annotations

import argparse
import logging
import time
from typing import Any

import yaml

from batch.runner.batch_scorer import score_batch
from batch.runner.input_validator import validate_input
from batch.runner.output_quality_gate import run_quality_gate
from batch.runner.downstream_notifier import send_notifications

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_batch_inference_pipeline(config: dict[str, Any]) -> None:
    """
    Execute the end-to-end batch inference pipeline locally.

    Steps:
        1. Validate input data
        2. Score batch (MLflow pyfunc)
        3. Check output quality
        4. Notify downstream systems
    """
    start = time.monotonic()

    logger.info("=== Step 1: Input validation ===")
    if not validate_input(config):
        send_notifications(config, status="failure", rows_scored=0, output_path="")
        raise RuntimeError("Input validation failed — aborting batch pipeline.")

    logger.info("=== Step 2: Batch scoring ===")
    stats = score_batch(config)

    logger.info("=== Step 3: Output quality gate ===")
    if not run_quality_gate(config, stats["output_path"]):
        send_notifications(
            config, status="failure",
            rows_scored=stats["rows_scored"],
            output_path=stats["output_path"],
            latency_seconds=time.monotonic() - start,
        )
        raise RuntimeError("Output quality gate failed — predictions not released.")

    logger.info("=== Step 4: Downstream notification ===")
    send_notifications(
        config, status="success",
        rows_scored=stats["rows_scored"],
        output_path=stats["output_path"],
        latency_seconds=time.monotonic() - start,
    )

    logger.info("Batch inference pipeline complete: %s", stats)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch inference pipeline.")
    parser.add_argument("--job-config", required=True)
    parser.add_argument("--mode", default="local", choices=["local", "argo"])
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.job_config))
    if args.mode == "local":
        run_batch_inference_pipeline(config)
    else:
        raise NotImplementedError("Use ci/github-actions/batch/trigger-batch-job.yml for Argo mode.")
