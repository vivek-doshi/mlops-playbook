"""
Purpose:
    Output quality gate for batch inference jobs.
    Checks prediction distributions against expected baselines to detect
    silent model failures (e.g., all predictions are one class, score
    distribution shifted dramatically from the previous run).

Usage:
    python batch/runner/output_quality_gate.py \\
        --job-config batch/jobs/fraud-detection-batch-job.yaml \\
        --predictions-path /output/predictions.parquet

Dependencies:
    pandas>=2.0
    pyarrow>=14.0
    pyyaml>=6.0
    scipy>=1.12
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

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


def _read_predictions(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".parquet":
        return pd.read_parquet(path)
    if p.suffix == ".csv":
        return pd.read_csv(path)
    if p.suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"Unsupported predictions format: {p.suffix}")


# --------------------------------------------------------------------------- #
# Quality checks
# --------------------------------------------------------------------------- #


def check_prediction_coverage(df: pd.DataFrame, pred_col: str, threshold: float = 0.999) -> list[str]:
    """Flag if more than ``(1-threshold)`` of predictions are null."""
    errors: list[str] = []
    if pred_col not in df.columns:
        errors.append(f"Prediction column '{pred_col}' not found in output")
        return errors

    null_rate = df[pred_col].isna().mean()
    if null_rate > (1 - threshold):
        errors.append(
            f"Prediction null rate {null_rate:.2%} exceeds threshold {1 - threshold:.2%}"
        )
    return errors


def check_class_distribution(
    df: pd.DataFrame,
    pred_col: str,
    expectations: dict[str, Any],
) -> list[str]:
    """
    Check that class distribution is within expected bounds.

    expectations keys:
        class_rate_bounds: {<class_label>: {min: float, max: float}}
        max_dominant_class_rate: float  (alerts if one class > this rate)
    """
    errors: list[str] = []
    if pred_col not in df.columns:
        return errors

    rates     = df[pred_col].value_counts(normalize=True).to_dict()
    bounds    = expectations.get("class_rate_bounds", {})
    max_dom   = expectations.get("max_dominant_class_rate", 0.99)

    # Check individual class bounds.
    for cls, bound in bounds.items():
        actual = rates.get(cls, 0.0)
        if "min" in bound and actual < bound["min"]:
            errors.append(
                f"Class '{cls}' rate {actual:.2%} below min {bound['min']:.2%}"
            )
        if "max" in bound and actual > bound["max"]:
            errors.append(
                f"Class '{cls}' rate {actual:.2%} above max {bound['max']:.2%}"
            )

    # Check dominant class guard.
    if rates:
        dominant_rate = max(rates.values())
        if dominant_rate > max_dom:
            dominant_cls = max(rates, key=rates.get)  # type: ignore[arg-type]
            errors.append(
                f"Dominant class '{dominant_cls}' rate {dominant_rate:.2%} "
                f"exceeds max_dominant_class_rate={max_dom:.2%} — "
                "possible degenerate model output."
            )

    return errors


def check_score_distribution(
    df: pd.DataFrame,
    score_col: str,
    expectations: dict[str, Any],
) -> list[str]:
    """Check numeric score statistics (mean, std) are within expected bounds."""
    errors: list[str] = []
    if score_col not in df.columns:
        return errors

    series = df[score_col].dropna()
    mean   = float(series.mean())
    std    = float(series.std())

    mean_bounds = expectations.get("score_mean_bounds", {})
    std_bounds  = expectations.get("score_std_bounds", {})

    if "min" in mean_bounds and mean < mean_bounds["min"]:
        errors.append(f"Score mean {mean:.4f} below min={mean_bounds['min']}")
    if "max" in mean_bounds and mean > mean_bounds["max"]:
        errors.append(f"Score mean {mean:.4f} above max={mean_bounds['max']}")
    if "min" in std_bounds and std < std_bounds["min"]:
        errors.append(f"Score std {std:.4f} below min={std_bounds['min']}")
    if "max" in std_bounds and std > std_bounds["max"]:
        errors.append(f"Score std {std:.4f} above max={std_bounds['max']}")

    logger.info("Score distribution: mean=%.4f  std=%.4f", mean, std)
    return errors


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def run_quality_gate(config: dict[str, Any], predictions_path: str) -> bool:
    """
    Run all output quality checks.  Returns True if all pass.
    """
    quality_cfg  = config.get("output", {}).get("quality_checks", {})
    if not quality_cfg:
        logger.info("No output quality checks configured — gate passes.")
        return True

    df       = _read_predictions(predictions_path)
    pred_col  = quality_cfg.get("prediction_column", "prediction")
    score_col = quality_cfg.get("score_column", "score")

    logger.info("Running quality gate on %d predictions", len(df))

    all_errors: list[str] = []
    all_errors.extend(
        check_prediction_coverage(df, pred_col, quality_cfg.get("min_coverage", 0.999))
    )
    all_errors.extend(check_class_distribution(df, pred_col, quality_cfg))
    all_errors.extend(check_score_distribution(df, score_col, quality_cfg))

    if all_errors:
        logger.error("Output quality gate FAILED with %d error(s):", len(all_errors))
        for err in all_errors:
            logger.error("  - %s", err)
        return False

    logger.info("Output quality gate PASSED.")
    return True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch output quality gate.")
    parser.add_argument("--job-config",        required=True, help="Path to job config YAML")
    parser.add_argument("--predictions-path",  required=True, help="Path to predictions file")
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = _load_config(args.job_config)
    passed = run_quality_gate(config, args.predictions_path)
    sys.exit(0 if passed else 1)
