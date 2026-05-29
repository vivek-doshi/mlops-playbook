"""
Purpose:
    Core batch scoring engine for offline/batch ML inference.
    Reads input data from a configurable source (local file, S3, GCS, Azure Blob),
    scores each row using an MLflow-registered model, writes predictions to an output
    sink, and emits quality metrics.

Usage:
    python batch/runner/batch_scorer.py \\
        --job-config batch/jobs/fraud-detection-batch-job.yaml

Dependencies:
    mlflow>=2.11
    pandas>=2.0
    pyarrow>=14.0
    pyyaml>=6.0
    scikit-learn>=1.4
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Any

import mlflow
import mlflow.pyfunc
import pandas as pd
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


def _load_job_config(path: str) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Data I/O
# --------------------------------------------------------------------------- #


def _read_input(config: dict[str, Any]) -> pd.DataFrame:
    """
    Load input data.  Supports:
    - ``parquet``  (default)
    - ``csv``
    - ``json``
    """
    path   = config["input"]["path"]
    fmt    = config["input"].get("format", "parquet")
    kwargs = config["input"].get("read_options", {})

    logger.info("Loading input data from %s (format=%s)", path, fmt)

    if fmt == "parquet":
        df = pd.read_parquet(path, **kwargs)
    elif fmt == "csv":
        df = pd.read_csv(path, **kwargs)
    elif fmt == "json":
        df = pd.read_json(path, **kwargs)
    else:
        raise ValueError(f"Unsupported input format: {fmt}")

    logger.info("Loaded %d rows × %d columns", len(df), len(df.columns))
    return df


def _write_output(predictions: pd.DataFrame, config: dict[str, Any]) -> None:
    """Write predictions to the configured output path."""
    path   = config["output"]["path"]
    fmt    = config["output"].get("format", "parquet")
    kwargs = config["output"].get("write_options", {})

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Writing %d predictions to %s (format=%s)", len(predictions), path, fmt)

    if fmt == "parquet":
        predictions.to_parquet(path, index=False, **kwargs)
    elif fmt == "csv":
        predictions.to_csv(path, index=False, **kwargs)
    elif fmt == "json":
        predictions.to_json(path, orient="records", indent=2, **kwargs)
    else:
        raise ValueError(f"Unsupported output format: {fmt}")


# --------------------------------------------------------------------------- #
# Model loading
# --------------------------------------------------------------------------- #


def _load_model(config: dict[str, Any]) -> mlflow.pyfunc.PyFuncModel:
    """Load an MLflow registered model by name + stage or version."""
    model_name = config["model"]["name"]
    stage      = config["model"].get("stage", "Production")
    version    = config["model"].get("version")
    tracking   = config["model"].get("tracking_uri")

    if tracking:
        mlflow.set_tracking_uri(tracking)

    if version:
        uri = f"models:/{model_name}/{version}"
    else:
        uri = f"models:/{model_name}/{stage}"

    logger.info("Loading model from %s", uri)
    return mlflow.pyfunc.load_model(uri)


# --------------------------------------------------------------------------- #
# Batch scorer
# --------------------------------------------------------------------------- #


def score_batch(config: dict[str, Any]) -> dict[str, Any]:
    """
    Execute one batch scoring job.

    Parameters
    ----------
    config:
        Parsed job YAML config (see ``batch/jobs/_job-schema.yaml``).

    Returns
    -------
    dict with keys: rows_scored, rows_failed, latency_seconds, output_path
    """
    start_time = time.monotonic()

    model = _load_model(config)
    df    = _read_input(config)

    # Drop the label/target column if present (batch scoring only).
    label_col = config.get("label_column", "label")
    if label_col in df.columns:
        df = df.drop(columns=[label_col])

    # Score in chunks to limit memory usage.
    chunk_size = config.get("chunk_size", 10_000)
    chunks     = [df.iloc[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

    logger.info("Scoring %d rows in %d chunk(s) of %d", len(df), len(chunks), chunk_size)

    all_predictions: list[pd.DataFrame] = []
    rows_failed = 0

    for idx, chunk in enumerate(chunks):
        try:
            preds = model.predict(chunk)
            if isinstance(preds, pd.DataFrame):
                all_predictions.append(preds)
            else:
                all_predictions.append(pd.DataFrame({"prediction": preds}))
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Chunk %d failed: %s", idx, exc)
            rows_failed += len(chunk)

    predictions = pd.concat(all_predictions, ignore_index=True)

    # Attach original index columns if configured.
    id_cols = config.get("id_columns", [])
    if id_cols:
        id_df = _read_input(config)[id_cols]
        predictions = pd.concat([id_df.reset_index(drop=True), predictions], axis=1)

    _write_output(predictions, config)

    elapsed = time.monotonic() - start_time
    stats   = {
        "rows_scored":    len(predictions),
        "rows_failed":    rows_failed,
        "latency_seconds": round(elapsed, 2),
        "output_path":    config["output"]["path"],
    }
    logger.info("Batch scoring complete: %s", stats)
    return stats


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch inference scorer.")
    parser.add_argument("--job-config", required=True, help="Path to job config YAML")
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = _load_job_config(args.job_config)
    score_batch(config)
