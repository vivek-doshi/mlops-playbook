#!/usr/bin/env python3
"""
drift_report.py — ML data drift detection using Evidently AI.

USAGE:
    python monitoring/evidently/drift_report.py \\
        --reference data/reference/train_features.parquet \\
        --current   data/current/today_features.parquet \\
        --output    reports/drift_report.html \\
        --threshold 0.3

EXIT CODES:
    0  — drift score is below the threshold (no action needed)
    1  — drift score exceeds the threshold (retraining recommended)

The script also writes a JSON summary file alongside the HTML report, and
optionally logs results to MLflow when MLFLOW_TRACKING_URI is set.

BEGINNER NOTE:
    A drift score is a number between 0 and 1.
    0 means the current data perfectly matches the reference (training) distribution.
    1 means the current data is completely different from the reference.
    A threshold of 0.3 means: if 30% or more of the distribution has shifted, alert.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
from evidently.metric_presets import DataDriftPreset, TargetDriftPreset
from evidently.report import Report


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Evidently drift report and exit non-zero if drift is detected."
    )
    parser.add_argument(
        "--reference",
        required=True,
        help="Path to reference (training) Parquet file.",
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Path to current (production) Parquet file.",
    )
    parser.add_argument(
        "--output",
        default="reports/drift_report.html",
        help="Output path for the HTML report. Default: reports/drift_report.html",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Drift score threshold above which the script exits with code 1. Default: 0.3",
    )
    parser.add_argument(
        "--target-column",
        default=None,
        help="Column name for model target/prediction column. Optional. Enables TargetDriftPreset.",
    )
    return parser.parse_args()


def load_data(path: str) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Parquet is preferred over CSV because it preserves column data types
    exactly — no guessing about whether a column is a float or a string.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    print(f"Loading data from: {path}")
    return pd.read_parquet(path_obj)


def run_drift_report(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    include_target_drift: bool,
) -> Report:
    """
    Build and run an Evidently drift report.

    DataDriftPreset checks each feature column individually and reports:
      - Per-column drift detected (yes/no)
      - Per-column drift score (Wasserstein distance or similar)
      - Overall dataset drift score

    TargetDriftPreset checks the target/prediction column distribution.
    This is a leading indicator of model accuracy degradation.
    """
    metrics = [DataDriftPreset()]
    if include_target_drift:
        metrics.append(TargetDriftPreset())

    report = Report(metrics=metrics)
    report.run(reference_data=reference_df, current_data=current_df)
    return report


def extract_drift_score(report: Report) -> float:
    """
    Extract the overall dataset drift score from the report dictionary.

    The report structure from Evidently v0.4+:
    report.as_dict()["metrics"][0]["result"]["dataset_drift_score"]
    """
    result_dict = report.as_dict()
    # The first metric is always DataDriftPreset when present.
    drift_result = result_dict.get("metrics", [{}])[0].get("result", {})
    return float(drift_result.get("dataset_drift_score", 0.0))


def count_drifted_columns(report: Report) -> int:
    """Count the number of individual columns with drift detected."""
    result_dict = report.as_dict()
    drift_result = result_dict.get("metrics", [{}])[0].get("result", {})
    return int(drift_result.get("number_of_drifted_columns", 0))


def save_json_summary(
    output_html_path: str,
    drift_score: float,
    drifted_columns: int,
    threshold: float,
    threshold_breached: bool,
) -> str:
    """
    Write a compact JSON summary alongside the HTML report.

    The JSON file is easier to parse in CI scripts than the full HTML report.
    """
    json_path = output_html_path.replace(".html", ".json")
    summary = {
        "drift_score": round(drift_score, 4),
        "drifted_columns": drifted_columns,
        "threshold": threshold,
        "threshold_breached": threshold_breached,
    }
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"JSON summary written to: {json_path}")
    return json_path


def log_to_mlflow(
    drift_score: float,
    drifted_columns: int,
    html_path: str,
    json_path: str,
) -> None:
    """
    Log drift metrics and report artifact to MLflow.

    Only called when MLFLOW_TRACKING_URI is set in the environment.
    This makes the drift check results visible in the MLflow UI alongside
    training runs, creating a single source of truth for model health.
    """
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        print("MLFLOW_TRACKING_URI not set — skipping MLflow logging.")
        return

    try:
        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        with mlflow.start_run(run_name="drift_check"):
            mlflow.log_metric("dataset_drift_score", drift_score)
            mlflow.log_metric("drifted_columns", drifted_columns)
            mlflow.set_tag("run_type", "drift_check")

            # Log the HTML report so it is viewable directly in the MLflow UI.
            if Path(html_path).exists():
                mlflow.log_artifact(html_path, artifact_path="monitoring")

            # Log the JSON summary for downstream parsing.
            if Path(json_path).exists():
                mlflow.log_artifact(json_path, artifact_path="monitoring")

        print("Drift metrics logged to MLflow.")
    except ImportError:
        print("mlflow package not installed — skipping MLflow logging.")
    except Exception as exc:
        # Non-fatal: MLflow logging failure should not block a CI drift check.
        print(f"WARNING: MLflow logging failed: {exc}")


def main() -> int:
    """
    Main entry point.

    Returns:
        0 if drift score is below the threshold.
        1 if drift score meets or exceeds the threshold.
    """
    args = parse_args()

    # ------------------------------------------------------------------ #
    # 1. Load datasets.
    # ------------------------------------------------------------------ #
    print(f"Loading reference data: {args.reference}")
    reference_df = load_data(args.reference)

    print(f"Loading current data:   {args.current}")
    current_df = load_data(args.current)

    print(f"Reference shape: {reference_df.shape}, Current shape: {current_df.shape}")

    # ------------------------------------------------------------------ #
    # 2. Run drift analysis.
    # ------------------------------------------------------------------ #
    include_target = args.target_column is not None
    print("Running Evidently drift report...")
    report = run_drift_report(reference_df, current_df, include_target_drift=include_target)

    # ------------------------------------------------------------------ #
    # 3. Extract summary metrics.
    # ------------------------------------------------------------------ #
    drift_score = extract_drift_score(report)
    drifted_columns = count_drifted_columns(report)
    threshold_breached = drift_score >= args.threshold

    print(f"\n--- Drift Report Summary ---")
    print(f"  Dataset drift score : {drift_score:.4f}")
    print(f"  Drifted columns     : {drifted_columns}")
    print(f"  Threshold           : {args.threshold}")
    print(f"  Threshold breached  : {threshold_breached}")
    print(f"----------------------------\n")

    # ------------------------------------------------------------------ #
    # 4. Save reports.
    # ------------------------------------------------------------------ #
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    report.save_html(args.output)
    print(f"HTML report saved to: {args.output}")

    json_path = save_json_summary(
        output_html_path=args.output,
        drift_score=drift_score,
        drifted_columns=drifted_columns,
        threshold=args.threshold,
        threshold_breached=threshold_breached,
    )

    # ------------------------------------------------------------------ #
    # 5. Optionally log to MLflow.
    # ------------------------------------------------------------------ #
    log_to_mlflow(drift_score, drifted_columns, args.output, json_path)

    # ------------------------------------------------------------------ #
    # 6. Return exit code.
    # Returning 1 here causes CI steps that call this script to fail,
    # which blocks deployment until the drift is investigated.
    # ------------------------------------------------------------------ #
    if threshold_breached:
        print(
            f"DRIFT DETECTED: score {drift_score:.4f} >= threshold {args.threshold}. "
            f"Review the report and consider retraining."
        )
        return 1

    print(f"No significant drift detected (score {drift_score:.4f} < threshold {args.threshold}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
