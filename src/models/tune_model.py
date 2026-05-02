from typing import Optional

import mlflow
import numpy as np
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

from src.features.build_features import build_feature_pipeline
from src.utils.logger import logger


def objective(trial: optuna.Trial, X_train, y_train) -> float:
    """Optuna objective: maximise mean CV accuracy."""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 15),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 4),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2"]),
        "random_state": 42,
    }
    pipeline = build_feature_pipeline()
    X_transformed = pipeline.fit_transform(X_train)
    clf = RandomForestClassifier(**params)
    scores = cross_val_score(clf, X_transformed, y_train, cv=3, scoring="accuracy", n_jobs=-1)
    return float(np.mean(scores))


def run_tuning(
    X_train,
    y_train,
    n_trials: int = 20,
    study_name: str = "rf_tuning",
    mlflow_run_id: Optional[str] = None,
) -> dict:
    """Run Optuna study and return best hyperparameters."""
    # suppress Optuna's default verbose logging
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study = optuna.create_study(direction="maximize", study_name=study_name)
    study.optimize(lambda trial: objective(trial, X_train, y_train), n_trials=n_trials)

    best_params = study.best_params
    best_value = study.best_value
    logger.info(f"Optuna best CV accuracy: {best_value:.4f} | params: {best_params}")

    # Log tuning results to active MLflow run if one exists
    if mlflow_run_id or mlflow.active_run():
        mlflow.log_params({f"tuned_{k}": v for k, v in best_params.items()})
        mlflow.log_metric("best_cv_accuracy", best_value)
        mlflow.log_metric("optuna_n_trials", n_trials)

    return best_params
