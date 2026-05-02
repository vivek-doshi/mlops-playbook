from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_feature_pipeline() -> Pipeline:
    """Builds a scikit-learn pipeline for feature engineering."""
    # Example: Simple standard scaling for all features
    pipeline = Pipeline([("scaler", StandardScaler())])
    return pipeline
