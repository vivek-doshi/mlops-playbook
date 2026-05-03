from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_feature_pipeline() -> Pipeline:
    """
    Builds a scikit-learn pipeline for feature engineering.

    EDUCATIONAL NOTE:
    Feature engineering is how we prepare raw data for a machine learning model.
    Models can only understand numbers, and they prefer numbers to be roughly the same scale.
    This pipeline can be extended to include:
    - Imputers (filling in missing data)
    - Encoders (turning text categories into numbers)
    - Scalers (like StandardScaler, making all numbers have a mean of 0 and variance of 1)
    """
    # Example: Simple standard scaling for all features
    pipeline = Pipeline([("scaler", StandardScaler())])
    return pipeline
