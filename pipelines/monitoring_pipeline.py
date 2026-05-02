import argparse
import sys
import tempfile

import pandas as pd

from monitoring.drift_detection import DriftDetector
from src.data.make_dataset import generate_synthetic_data
from src.utils.logger import logger


def run_monitoring(reference_path: str, current_path: str = None, threshold: float = 0.3):
    """
    Run drift detection comparing reference vs current data.
    Exits with code 1 if drift is detected (for CI integration).
    """
    logger.info(f"Loading reference data from {reference_path}")
    reference_df = pd.read_csv(reference_path).drop(columns=["target"], errors="ignore")

    if current_path:
        logger.info(f"Loading current data from {current_path}")
        current_df = pd.read_csv(current_path).drop(columns=["target"], errors="ignore")
    else:
        logger.info("No current data provided — generating simulated drift data")
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            current_df = generate_synthetic_data(f.name, n_samples=200)
            current_df = current_df.drop(columns=["target"], errors="ignore")

    detector = DriftDetector(reference_data=reference_df, drift_share_threshold=threshold)
    drift_detected = detector.detect_drift(
        current_data=current_df,
        report_name="latest_drift_report",
        log_to_mlflow=False,
    )

    if drift_detected:
        logger.warning("Drift detected — exiting with code 1")
        sys.exit(1)
    else:
        logger.info("No drift detected — pipeline healthy")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run drift detection monitoring pipeline.")
    parser.add_argument("--reference", type=str, default="data/raw/dataset.csv")
    parser.add_argument("--current", type=str, default=None)
    parser.add_argument("--threshold", type=float, default=0.3)
    args = parser.parse_args()
    run_monitoring(args.reference, args.current, args.threshold)
