from src.data.make_dataset import generate_synthetic_data
from src.models.tune_model import run_tuning


def test_run_tuning(tmp_path):
    output_path = tmp_path / "dataset.csv"
    df = generate_synthetic_data(str(output_path), n_samples=100)

    X = df.drop(columns=["target"])
    y = df["target"]

    best_params = run_tuning(X, y, n_trials=2, study_name="test_tuning")

    # Check that it returns expected keys
    assert "n_estimators" in best_params
    assert "max_depth" in best_params

    # Check that values are within expected ranges defined in objective
    assert 50 <= best_params["n_estimators"] <= 300
    assert 3 <= best_params["max_depth"] <= 15
