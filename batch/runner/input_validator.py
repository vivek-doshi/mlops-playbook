"""
Purpose:
    Input data validator for batch inference jobs.
    Validates schema (column names + types), null rates, and value ranges
    against expectations defined in the job config.  Exits 1 if validation fails,
    so it can be used as a CI gate before batch scoring runs.

Usage:
    python batch/runner/input_validator.py \\
        --job-config batch/jobs/fraud-detection-batch-job.yaml

Dependencies:
    pandas>=2.0
    pyarrow>=14.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import logging
import sys
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


def _read_input(config: dict[str, Any]) -> pd.DataFrame:
    path = config["input"]["path"]
    fmt  = config["input"].get("format", "parquet")
    if fmt == "parquet":
        return pd.read_parquet(path)
    if fmt == "csv":
        return pd.read_csv(path)
    if fmt == "json":
        return pd.read_json(path)
    raise ValueError(f"Unsupported format: {fmt}")


# --------------------------------------------------------------------------- #
# Validators
# --------------------------------------------------------------------------- #


def validate_schema(df: pd.DataFrame, expectations: dict) -> list[str]:
    """Return a list of schema violation messages (empty = pass)."""
    errors: list[str] = []

    required_cols = expectations.get("required_columns", [])
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    dtype_checks = expectations.get("dtypes", {})
    for col, expected_dtype in dtype_checks.items():
        if col not in df.columns:
            continue
        actual = str(df[col].dtype)
        if expected_dtype not in actual:
            errors.append(
                f"Column '{col}' dtype mismatch: expected '{expected_dtype}', got '{actual}'"
            )

    return errors


def validate_null_rates(df: pd.DataFrame, expectations: dict) -> list[str]:
    """Return null rate violation messages."""
    errors: list[str] = []
    max_null_rate = expectations.get("max_null_rate", 0.05)

    for col in df.columns:
        null_rate = df[col].isna().mean()
        col_limit = expectations.get("column_null_limits", {}).get(col, max_null_rate)
        if null_rate > col_limit:
            errors.append(
                f"Column '{col}' null rate {null_rate:.2%} exceeds limit {col_limit:.2%}"
            )

    return errors


def validate_value_ranges(df: pd.DataFrame, expectations: dict) -> list[str]:
    """Return value range violation messages."""
    errors: list[str] = []
    ranges = expectations.get("value_ranges", {})

    for col, bounds in ranges.items():
        if col not in df.columns:
            continue
        if "min" in bounds:
            violations = (df[col] < bounds["min"]).sum()
            if violations > 0:
                errors.append(
                    f"Column '{col}': {violations} values below min={bounds['min']}"
                )
        if "max" in bounds:
            violations = (df[col] > bounds["max"]).sum()
            if violations > 0:
                errors.append(
                    f"Column '{col}': {violations} values above max={bounds['max']}"
                )

    return errors


def validate_row_count(df: pd.DataFrame, expectations: dict) -> list[str]:
    """Return row count violation messages."""
    errors: list[str] = []
    min_rows = expectations.get("min_rows", 1)
    max_rows = expectations.get("max_rows")

    if len(df) < min_rows:
        errors.append(f"Row count {len(df)} below minimum {min_rows}")
    if max_rows is not None and len(df) > max_rows:
        errors.append(f"Row count {len(df)} exceeds maximum {max_rows}")

    return errors


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def validate_input(config: dict[str, Any]) -> bool:
    """
    Run all input validators.  Returns True if all pass.
    """
    expectations = config.get("input", {}).get("expectations", {})
    if not expectations:
        logger.info("No input expectations configured — skipping validation.")
        return True

    df = _read_input(config)
    logger.info("Validating %d rows × %d columns", len(df), len(df.columns))

    all_errors: list[str] = []
    all_errors.extend(validate_schema(df, expectations))
    all_errors.extend(validate_null_rates(df, expectations))
    all_errors.extend(validate_value_ranges(df, expectations))
    all_errors.extend(validate_row_count(df, expectations))

    if all_errors:
        logger.error("Input validation FAILED with %d error(s):", len(all_errors))
        for err in all_errors:
            logger.error("  - %s", err)
        return False

    logger.info("Input validation PASSED (%d checks).", 4)
    return True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch input validator.")
    parser.add_argument("--job-config", required=True, help="Path to job config YAML")
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = _load_config(args.job_config)
    passed = validate_input(config)
    sys.exit(0 if passed else 1)
