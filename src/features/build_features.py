from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_feature_pipeline() -> Pipeline:
    """
    Builds a scikit-learn pipeline for feature engineering.

    EDUCATIONAL NOTE:
    In MLOps, it's critical to bundle all feature transformations into a single object
    (like an sklearn Pipeline). This prevents "train/serve skew" — a common bug where
    data is transformed differently in the API than it was during training.
    The returned pipeline will be fitted on training data, saved as an artifact,
    and loaded by the inference API.
    """
    # Example: Simple standard scaling for all features
    pipeline = Pipeline([("scaler", StandardScaler())])
    return pipeline
