from monitoring.drift_detection import DriftDetector
from src.data.make_dataset import generate_synthetic_data


def test_detect_drift_no_drift(tmp_path, monkeypatch):
    import monitoring.drift_detection as drift_mod

    monkeypatch.setattr(drift_mod, "REPORTS_DIR", tmp_path)

    # Generate reference data
    ref_path = tmp_path / "ref.csv"
    ref_df = generate_synthetic_data(str(ref_path), n_samples=100).drop(columns=["target"])

    detector = DriftDetector(reference_data=ref_df, drift_share_threshold=0.3)

    # Same data shouldn't drift
    drift_detected = detector.detect_drift(ref_df, report_name="no_drift_report")

    assert drift_detected is False
    assert (tmp_path / "no_drift_report.html").exists()


def test_detect_drift_with_drift(tmp_path, monkeypatch):
    import monitoring.drift_detection as drift_mod

    monkeypatch.setattr(drift_mod, "REPORTS_DIR", tmp_path)

    ref_path = tmp_path / "ref.csv"
    ref_df = generate_synthetic_data(str(ref_path), n_samples=100).drop(columns=["target"])

    # Create shifted data
    current_df = ref_df.copy()
    for col in current_df.columns:
        current_df[col] = current_df[col] * 100 + 500

    detector = DriftDetector(reference_data=ref_df, drift_share_threshold=0.3)

    drift_detected = detector.detect_drift(current_df, report_name="drift_report")

    assert drift_detected is True
    assert (tmp_path / "drift_report.html").exists()
