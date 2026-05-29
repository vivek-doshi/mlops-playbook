"""
Purpose:
    Fairness evaluation runner using fairlearn.  Given a trained MLflow model,
    test features, and a fairness configuration, this module computes the
    disparate-impact ratio, equalised-odds difference, and false-negative rate
    disparity per sensitive group.  Results are logged back to the originating
    MLflow run and written to a JSON report file.

Usage:
    python -m fairness.evaluate \\
        --model-uri   models:/fraud-detection/3 \\
        --test-data   data/test_features.parquet \\
        --config      policy/fairness/fraud-detection-fairness.yaml \\
        --report-path fairness_report.json

Dependencies:
    fairlearn>=0.10
    mlflow>=2.11
    pandas>=2.0
    scikit-learn>=1.4
    pyyaml>=6.0
    numpy>=1.26
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from fairlearn.metrics import (
    MetricFrame,
    count,
    equalized_odds_difference,
    false_negative_rate,
    selection_rate,
)
from sklearn.metrics import accuracy_score
import mlflow


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DEFAULT_DISPARATE_IMPACT_THRESHOLD = 0.80
DEFAULT_EQUALISED_ODDS_THRESHOLD = 0.10
DEFAULT_FNR_DISPARITY_THRESHOLD = 0.10


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def _load_config(config_path: str) -> dict[str, Any]:
    """Load and return the fairness configuration YAML."""
    with open(config_path) as fh:
        return yaml.safe_load(fh)


def _load_test_data(
    data_path: str,
    label_col: str,
    sensitive_features: list[str],
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Return (X, y, sensitive_df) from a Parquet file."""
    df = pd.read_parquet(data_path)
    missing = [c for c in sensitive_features + [label_col] if c not in df.columns]
    if missing:
        print(
            f"ERROR: Required columns missing from test data: {missing}",
            file=sys.stderr,
        )
        sys.exit(1)
    y = df[label_col]
    sensitive_df = df[sensitive_features]
    X = df.drop(columns=sensitive_features + [label_col])
    return X, y, sensitive_df


def _compute_disparate_impact_ratio(
    y_true: pd.Series,
    y_pred: np.ndarray,
    sensitive_col: pd.Series,
) -> float:
    """
    Compute disparate impact ratio: min(group_selection_rate) / max(group_selection_rate).
    A value below DEFAULT_DISPARATE_IMPACT_THRESHOLD indicates potential bias.
    """
    mf = MetricFrame(
        metrics={"selection_rate": selection_rate},
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_col,
    )
    group_rates: pd.Series = mf.by_group["selection_rate"]
    if group_rates.max() == 0:
        return 1.0  # edge case: no positive predictions
    return float(group_rates.min() / group_rates.max())


def _compute_fnr_disparity(
    y_true: pd.Series,
    y_pred: np.ndarray,
    sensitive_col: pd.Series,
) -> float:
    """
    Compute the maximum absolute FNR difference across groups.
    """
    mf = MetricFrame(
        metrics={"fnr": false_negative_rate},
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_col,
    )
    group_fnr: pd.Series = mf.by_group["fnr"]
    return float(group_fnr.max() - group_fnr.min())


# --------------------------------------------------------------------------- #
# Main evaluation routine
# --------------------------------------------------------------------------- #


def evaluate_fairness(
    model_uri: str,
    test_data_path: str,
    config_path: str,
    report_path: str,
    mlflow_tracking_uri: str | None = None,
) -> dict[str, Any]:
    """
    Run fairness evaluation and return the report dict.
    Raises SystemExit with code 1 if any threshold is breached.
    """
    if mlflow_tracking_uri:
        mlflow.set_tracking_uri(mlflow_tracking_uri)

    config = _load_config(config_path)
    label_col: str = config.get("label_column", "label")
    sensitive_features: list[str] = config.get("sensitive_features", [])

    if not sensitive_features:
        print(
            "ERROR: No sensitive_features defined in the fairness config.",
            file=sys.stderr,
        )
        sys.exit(1)

    thresholds = config.get("thresholds", {})
    di_threshold: float = thresholds.get(
        "disparate_impact_ratio", DEFAULT_DISPARATE_IMPACT_THRESHOLD
    )
    eod_threshold: float = thresholds.get(
        "equalised_odds_difference", DEFAULT_EQUALISED_ODDS_THRESHOLD
    )
    fnr_threshold: float = thresholds.get(
        "fnr_disparity", DEFAULT_FNR_DISPARITY_THRESHOLD
    )

    print(f"Loading model from: {model_uri}")
    model = mlflow.pyfunc.load_model(model_uri)

    X, y_true, sensitive_df = _load_test_data(test_data_path, label_col, sensitive_features)

    print("Running model predictions …")
    y_pred = np.array(model.predict(X))

    report: dict[str, Any] = {
        "model_uri": model_uri,
        "config_path": config_path,
        "label_column": label_col,
        "sensitive_features": sensitive_features,
        "thresholds": {
            "disparate_impact_ratio": di_threshold,
            "equalised_odds_difference": eod_threshold,
            "fnr_disparity": fnr_threshold,
        },
        "results": {},
        "violations": [],
        "passed": True,
    }

    for feature in sensitive_features:
        group_col = sensitive_df[feature]

        di_ratio = _compute_disparate_impact_ratio(y_true, y_pred, group_col)
        eod = equalized_odds_difference(y_true, y_pred, sensitive_features=group_col)
        fnr_disp = _compute_fnr_disparity(y_true, y_pred, group_col)
        accuracy = float(accuracy_score(y_true, y_pred))

        # Per-group counts via MetricFrame
        mf_count = MetricFrame(
            metrics={"count": count},
            y_true=y_true,
            y_pred=y_pred,
            sensitive_features=group_col,
        )

        report["results"][feature] = {
            "disparate_impact_ratio": round(di_ratio, 4),
            "equalised_odds_difference": round(eod, 4),
            "fnr_disparity": round(fnr_disp, 4),
            "overall_accuracy": round(accuracy, 4),
            "group_counts": mf_count.by_group["count"].to_dict(),
        }

        # Check thresholds
        if di_ratio < di_threshold:
            msg = (
                f"[FAIL] {feature}: disparate_impact_ratio={di_ratio:.4f} "
                f"< threshold={di_threshold}"
            )
            print(msg)
            report["violations"].append(msg)
            report["passed"] = False

        if eod > eod_threshold:
            msg = (
                f"[FAIL] {feature}: equalised_odds_difference={eod:.4f} "
                f"> threshold={eod_threshold}"
            )
            print(msg)
            report["violations"].append(msg)
            report["passed"] = False

        if fnr_disp > fnr_threshold:
            msg = (
                f"[FAIL] {feature}: fnr_disparity={fnr_disp:.4f} "
                f"> threshold={fnr_threshold}"
            )
            print(msg)
            report["violations"].append(msg)
            report["passed"] = False

        status = "PASS" if report["passed"] else "FAIL"
        print(
            f"[{status}] {feature}: DI={di_ratio:.4f} "
            f"EOD={eod:.4f} FNR_disp={fnr_disp:.4f}"
        )

    # Write JSON report
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"Fairness report written to: {report_path}")

    return report


# --------------------------------------------------------------------------- #
# CLI entry-point
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run fairness evaluation on an MLflow model."
    )
    parser.add_argument("--model-uri", required=True, help="MLflow model URI")
    parser.add_argument(
        "--test-data", required=True, help="Path to test Parquet file"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to fairness config YAML (policy/fairness/)",
    )
    parser.add_argument(
        "--report-path",
        default="fairness_report.json",
        help="Output path for the JSON report",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    report = evaluate_fairness(
        model_uri=args.model_uri,
        test_data_path=args.test_data,
        config_path=args.config,
        report_path=args.report_path,
        mlflow_tracking_uri=os.environ.get("MLFLOW_TRACKING_URI"),
    )
    if not report["passed"]:
        print(
            f"\nFairness gate FAILED with {len(report['violations'])} violation(s).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nFairness gate PASSED.")
    sys.exit(0)
