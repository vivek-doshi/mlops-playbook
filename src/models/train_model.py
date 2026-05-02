from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline


def build_model(n_estimators: int = 100, max_depth: int = 5) -> Pipeline:
    """
    Builds the core machine learning model.

    EDUCATIONAL NOTE:
    Separating the model definition from the training pipeline script makes testing
    easier and allows you to swap algorithms (e.g., to XGBoost or LogisticRegression)
    without rewriting the heavy MLflow tracking code in pipelines/training_pipeline.py.
    """
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    return model
