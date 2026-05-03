import os

import hydra
import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from omegaconf import DictConfig
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from src.features.build_features import build_feature_pipeline
from src.models.train_model import build_model


@hydra.main(version_base=None, config_path="../configs", config_name="hydra_config")
def run_training_hydra(config: DictConfig):
    # MLflow Setup
    tracking_uri = (
        config.mlflow.tracking_uri
        if "mlflow" in config and "tracking_uri" in config.mlflow
        else os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db")
    )
    experiment_name = (
        config.mlflow.experiment_name
        if "mlflow" in config and "experiment_name" in config.mlflow
        else os.getenv("MLFLOW_EXPERIMENT_NAME", "churn_prediction")
    )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    print(f"Loading data from {config.data.raw_path}...")
    df = pd.read_csv(config.data.raw_path)

    X = df.drop(columns=["target"])
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.data.test_size, random_state=config.data.random_state
    )

    feature_pipeline = build_feature_pipeline()
    model = build_model(n_estimators=config.model.n_estimators, max_depth=config.model.max_depth)

    with mlflow.start_run():
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

        # Log to MLflow
        mlflow.log_params(dict(config.model))
        mlflow.log_metrics({"accuracy": accuracy, "precision": precision, "recall": recall})

        # Save model and pipeline
        os.makedirs("models", exist_ok=True)
        model_path = "models/model.pkl"
        pipeline_path = "models/feature_pipeline.pkl"
        joblib.dump(model, model_path)
        joblib.dump(feature_pipeline, pipeline_path)

        mlflow.sklearn.log_model(model, "model")
        mlflow.log_artifact(pipeline_path)
        print("Training complete. Artifacts saved.")

        # Model registry (optional — controlled by config)
        if "registry" in config and config.registry.get("enabled", True):
            from src.models.registry import promote_model, register_model

            run_id = mlflow.active_run().info.run_id
            version = register_model(
                run_id=run_id,
                model_artifact_path="model",
                model_name=config.registry.model_name,
                accuracy=accuracy,
                accuracy_threshold=config.registry.accuracy_threshold,
            )
            if version:
                promote_model(
                    model_name=config.registry.model_name,
                    version=version,
                    stage=config.registry.promote_to,
                )

if __name__ == "__main__":
    run_training_hydra()
