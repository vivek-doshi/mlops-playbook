import argparse
import json
import os

import joblib
import mlflow
import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from src.features.build_features import build_feature_pipeline
from src.models.train_model import build_model


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        if config_path.endswith(".yaml"):
            return yaml.safe_load(f)
        else:
            return json.load(f)


def run_training(config_path: str):
    config = load_config(config_path)

    # MLflow Setup
    tracking_uri = config.get("mlflow", {}).get("tracking_uri") or os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db")
    experiment_name = config.get("mlflow", {}).get("experiment_name") or os.getenv(
        "MLFLOW_EXPERIMENT_NAME", "churn_prediction"
    )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    print(f"Loading data from {config['data']['raw_path']}...")
    df = pd.read_csv(config["data"]["raw_path"])

    X = df.drop(columns=["target"])
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config["data"]["test_size"],
        random_state=config["data"]["random_state"],
    )

    # EDUCATIONAL NOTE:
    # A training pipeline integrates data loading, feature engineering, and model training.
    # We wrap the training logic in `mlflow.start_run()` to ensure everything (metrics,
    # parameters, models) is logged together as a single experiment in MLflow.
    with mlflow.start_run():
        # Hyperparameter tuning (optional — controlled by config)
        if config.get("tuning", {}).get("enabled", False):
            from src.models.tune_model import run_tuning
            from src.utils.logger import logger

            logger.info("Running Optuna hyperparameter tuning...")
            best_params = run_tuning(
                X_train,
                y_train,
                n_trials=config["tuning"]["n_trials"],
                study_name=config["tuning"]["study_name"],
            )
            # Override config model params with tuned values
            config["model"]["n_estimators"] = best_params["n_estimators"]
            config["model"]["max_depth"] = best_params["max_depth"]
            logger.info(f"Using tuned params: {best_params}")

        feature_pipeline = build_feature_pipeline()
        model = build_model(
            n_estimators=config["model"]["n_estimators"],
            max_depth=config["model"]["max_depth"],
        )

        print("Transforming features...")
        X_train_transformed = feature_pipeline.fit_transform(X_train)
        X_test_transformed = feature_pipeline.transform(X_test)

        print("Training model...")
        model.fit(X_train_transformed, y_train)

        print("Evaluating model...")
        predictions = model.predict(X_test_transformed)
        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions)
        recall = recall_score(y_test, predictions)

        print(f"Metrics - Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}")

        # EDUCATIONAL NOTE:
        # Logging parameters (inputs) and metrics (outputs) allows Data Scientists to
        # compare hundreds of experiments in the MLflow UI and easily identify the best model.
        # Log to MLflow
        mlflow.log_params(config["model"])
        mlflow.log_metrics({"accuracy": accuracy, "precision": precision, "recall": recall})

        # Save model and pipeline
        os.makedirs("models", exist_ok=True)
        model_path = "models/model.pkl"
        pipeline_path = "models/feature_pipeline.pkl"
        joblib.dump(model, model_path)
        joblib.dump(feature_pipeline, pipeline_path)

        mlflow.log_artifact(model_path)
        mlflow.log_artifact(pipeline_path)
        print("Training complete. Artifacts saved.")

        # Model registry (optional — controlled by config)
        if config.get("registry", {}).get("enabled", True):
            from src.models.registry import promote_model, register_model

            run_id = mlflow.active_run().info.run_id
            version = register_model(
                run_id=run_id,
                model_artifact_path="model.pkl",
                model_name=config["registry"]["model_name"],
                accuracy=accuracy,
                accuracy_threshold=config["registry"]["accuracy_threshold"],
            )
            if version:
                promote_model(
                    model_name=config["registry"]["model_name"],
                    version=version,
                    stage=config["registry"]["promote_to"],
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run training pipeline.")
    parser.add_argument("--config", type=str, default="configs/config.yaml", help="Path to config file.")
    args = parser.parse_args()

    run_training(args.config)
