import os
import hydra
from omegaconf import DictConfig
import mlflow
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib

from src.features.build_features import build_feature_pipeline
from src.models.train_model import build_model

@hydra.main(version_base=None, config_path="../configs", config_name="hydra_config")
def run_training_hydra(config: DictConfig):
    # MLflow Setup
    mlflow.set_tracking_uri(config.mlflow.tracking_uri)
    mlflow.set_experiment(config.mlflow.experiment_name)

    print(f"Loading data from {config.data.raw_path}...")
    df = pd.read_csv(config.data.raw_path)

    X = df.drop(columns=["target"])
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config.data.test_size,
        random_state=config.data.random_state
    )

    feature_pipeline = build_feature_pipeline()
    model = build_model(
        n_estimators=config.model.n_estimators,
        max_depth=config.model.max_depth
    )

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
        mlflow.log_metrics({
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall
        })

        # Save model and pipeline
        os.makedirs("models", exist_ok=True)
        model_path = "models/model.pkl"
        pipeline_path = "models/feature_pipeline.pkl"
        joblib.dump(model, model_path)
        joblib.dump(feature_pipeline, pipeline_path)

        mlflow.log_artifact(model_path)
        mlflow.log_artifact(pipeline_path)
        print("Training complete. Artifacts saved.")

if __name__ == "__main__":
    run_training_hydra()
