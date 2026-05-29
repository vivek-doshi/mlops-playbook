"""
Purpose:
    SHAP-based explainability report generator.  Given an MLflow model and test
    data, computes SHAP values and produces a JSON summary report plus optional
    PNG plots (bar summary and beeswarm).  The report is suitable for logging as
    an MLflow artifact and for audit / model card documentation.

Usage:
    python -m fairness.explainability \\
        --model-uri   models:/fraud-detection/3 \\
        --test-data   data/test_features.parquet \\
        --output-dir  reports/explainability/ \\
        --max-display 20

Dependencies:
    shap>=0.44
    mlflow>=2.11
    pandas>=2.0
    matplotlib>=3.8
    numpy>=1.26
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for CI
import matplotlib.pyplot as plt
import mlflow


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _load_test_data(
    data_path: str,
    label_col: str = "label",
    sensitive_features: list[str] | None = None,
) -> pd.DataFrame:
    """Load Parquet and drop label + sensitive columns before explanation."""
    df = pd.read_parquet(data_path)
    drop_cols = [label_col] + (sensitive_features or [])
    drop_cols = [c for c in drop_cols if c in df.columns]
    return df.drop(columns=drop_cols)


def _get_shap_values(
    model: mlflow.pyfunc.PyFuncModel,
    X: pd.DataFrame,
    max_background: int = 100,
) -> tuple[shap.Explanation | np.ndarray, shap.Explainer]:
    """
    Compute SHAP values using a KernelExplainer (model-agnostic).
    For large datasets the background sample is capped at `max_background` rows.
    """
    background = shap.sample(X, min(max_background, len(X)), random_state=42)

    def _predict(data: np.ndarray) -> np.ndarray:
        return np.array(
            model.predict(pd.DataFrame(data, columns=X.columns))
        )

    explainer = shap.KernelExplainer(_predict, background)
    shap_values = explainer.shap_values(X, silent=True)
    return shap_values, explainer


def _mean_abs_shap(shap_values: np.ndarray, feature_names: list[str]) -> dict[str, float]:
    """Return mean absolute SHAP value per feature, sorted descending."""
    if isinstance(shap_values, list):
        # Multi-class: average across classes
        arr = np.mean([np.abs(sv) for sv in shap_values], axis=0)
    else:
        arr = np.abs(shap_values)
    means = arr.mean(axis=0)
    return dict(
        sorted(
            zip(feature_names, means.tolist()),
            key=lambda kv: kv[1],
            reverse=True,
        )
    )


# --------------------------------------------------------------------------- #
# Main routine
# --------------------------------------------------------------------------- #


def generate_explainability_report(
    model_uri: str,
    test_data_path: str,
    output_dir: str,
    label_col: str = "label",
    sensitive_features: list[str] | None = None,
    max_display: int = 20,
    max_background: int = 100,
    mlflow_tracking_uri: str | None = None,
) -> dict:
    """
    Generate SHAP explainability report and write artefacts to output_dir.
    Returns a summary dict.
    """
    if mlflow_tracking_uri:
        mlflow.set_tracking_uri(mlflow_tracking_uri)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Loading model: {model_uri}")
    model = mlflow.pyfunc.load_model(model_uri)

    print(f"Loading test data: {test_data_path}")
    X = _load_test_data(test_data_path, label_col, sensitive_features)

    print(f"Computing SHAP values for {len(X)} rows × {X.shape[1]} features …")
    shap_values, explainer = _get_shap_values(model, X, max_background)

    feature_names = X.columns.tolist()
    importance = _mean_abs_shap(shap_values, feature_names)

    # ---- Bar summary plot ------------------------------------------------- #
    bar_plot_path = out / "shap_bar_summary.png"
    plt.figure(figsize=(10, max(4, min(max_display, len(feature_names)) * 0.4 + 1)))
    top_features = list(importance.keys())[:max_display]
    top_values = [importance[f] for f in top_features]
    plt.barh(top_features[::-1], top_values[::-1])
    plt.xlabel("Mean |SHAP value|")
    plt.title("Feature Importance (SHAP)")
    plt.tight_layout()
    plt.savefig(bar_plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Bar plot saved: {bar_plot_path}")

    # ---- Beeswarm plot (single class or first class for multi-class) ------- #
    beeswarm_path = out / "shap_beeswarm.png"
    sv_for_plot = shap_values[0] if isinstance(shap_values, list) else shap_values
    explanation = shap.Explanation(
        values=sv_for_plot,
        base_values=explainer.expected_value if not isinstance(
            explainer.expected_value, list
        ) else explainer.expected_value[0],
        data=X.values,
        feature_names=feature_names,
    )
    plt.figure()
    shap.plots.beeswarm(explanation, max_display=max_display, show=False)
    plt.tight_layout()
    plt.savefig(beeswarm_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Beeswarm plot saved: {beeswarm_path}")

    # ---- JSON report ------------------------------------------------------- #
    report = {
        "model_uri": model_uri,
        "num_samples_explained": len(X),
        "num_features": len(feature_names),
        "top_features": {k: round(v, 6) for k, v in list(importance.items())[:max_display]},
        "artifacts": {
            "bar_plot": str(bar_plot_path),
            "beeswarm_plot": str(beeswarm_path),
        },
    }
    report_path = out / "explainability_report.json"
    with open(report_path, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"Report written: {report_path}")

    return report


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SHAP-based explainability report for an MLflow model."
    )
    parser.add_argument("--model-uri", required=True)
    parser.add_argument("--test-data", required=True)
    parser.add_argument("--output-dir", default="reports/explainability")
    parser.add_argument("--label-col", default="label")
    parser.add_argument(
        "--sensitive-features",
        nargs="*",
        default=[],
        help="Column names to exclude from SHAP input",
    )
    parser.add_argument("--max-display", type=int, default=20)
    parser.add_argument("--max-background", type=int, default=100)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    generate_explainability_report(
        model_uri=args.model_uri,
        test_data_path=args.test_data,
        output_dir=args.output_dir,
        label_col=args.label_col,
        sensitive_features=args.sensitive_features,
        max_display=args.max_display,
        max_background=args.max_background,
        mlflow_tracking_uri=os.environ.get("MLFLOW_TRACKING_URI"),
    )
    sys.exit(0)
