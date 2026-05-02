from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline


def build_model(n_estimators: int = 100, max_depth: int = 5) -> Pipeline:
    """Builds a RandomForest model."""
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    return model
