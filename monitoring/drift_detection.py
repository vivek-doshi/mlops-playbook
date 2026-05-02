import logging
from pathlib import Path

import mlflow
import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("monitoring/reports")


class DriftDetector:
    """
    Evidently-backed data drift detector.

    Compares a reference dataset (training distribution) against
    current inference data and generates an HTML drift report.
    """

    def __init__(self, reference_data: pd.DataFrame, drift_share_threshold: float = 0.3):
        """
        Args:
            reference_data: The training dataset used as the drift baseline.
            drift_share_threshold: Fraction of drifted features that triggers a drift alert.
        """
        self.reference_data = reference_data
        self.drift_share_threshold = drift_share_threshold
        logger.info(
            f"DriftDetector initialised | reference rows: {len(reference_data)} | " f"threshold: {drift_share_threshold}"
        )

    def detect_drift(
        self,
        current_data: pd.DataFrame,
        report_name: str = "drift_report",
        log_to_mlflow: bool = False,
    ) -> bool:
        """
        Run Evidently DataDriftPreset and return True if drift is detected.

        Args:
            current_data: New data to compare against the reference.
            report_name: Filename stem for the HTML report.
            log_to_mlflow: If True, log drift metrics to the active MLflow run.

        Returns:
            True if the share of drifted features exceeds the threshold.
        """
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        report = Report(metrics=[DataDriftPreset()])
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=ColumnMapping(),
        )

        # Extract drift summary
        report_dict = report.as_dict()
        drift_metrics = report_dict["metrics"][0]["result"]
        share_drifted = drift_metrics.get("share_of_drifted_columns", 0.0)
        n_drifted = drift_metrics.get("number_of_drifted_columns", 0)
        n_total = drift_metrics.get("number_of_columns", 0)
        drift_detected = share_drifted >= self.drift_share_threshold

        logger.info(
            f"Drift check: {n_drifted}/{n_total} features drifted "
            f"({share_drifted:.1%}) | threshold: {self.drift_share_threshold:.1%} | "
            f"drift_detected: {drift_detected}"
        )

        # Save HTML report
        report_path = REPORTS_DIR / f"{report_name}.html"
        report.save_html(str(report_path))
        logger.info(f"Drift report saved to {report_path}")

        # Log to MLflow if requested
        if log_to_mlflow and mlflow.active_run():
            mlflow.log_metric("drift_share_of_features", share_drifted)
            mlflow.log_metric("drift_n_features", n_drifted)
            mlflow.log_metric("drift_detected", int(drift_detected))
            mlflow.log_artifact(str(report_path))

        if drift_detected:
            logger.warning(f"⚠ Data drift detected! {n_drifted}/{n_total} features drifted. " "Consider retraining the model.")

        return drift_detected
