from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline


def build_model(n_estimators: int = 100, max_depth: int = 5) -> Pipeline:
    """
    Builds a RandomForest model.

    EDUCATIONAL NOTE:
    This is where the actual algorithm is defined.
    A Random Forest is an ensemble of Decision Trees.
    'n_estimators' is the number of trees, and 'max_depth' controls how deep each tree can grow.
    You can replace this entirely with a different algorithm (like XGBoost or a Neural Network)
    without breaking the rest of the pipeline!
    """
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    return model
