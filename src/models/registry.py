from typing import Optional

import mlflow
from mlflow import MlflowClient

from src.utils.logger import logger


def register_model(
    run_id: str,
    model_artifact_path: str,
    model_name: str,
    accuracy: float,
    accuracy_threshold: float = 0.70,
) -> Optional[str]:
    """
    Register a model run in the MLflow Model Registry if it meets
    the accuracy threshold. Returns the model version or None.

    Args:
        run_id: MLflow run ID to register.
        model_artifact_path: Path of the artifact within the run (e.g. "models/model.pkl").
        model_name: Registered model name in the registry.
        accuracy: Evaluation accuracy of this run.
        accuracy_threshold: Minimum accuracy required to register.

    Returns:
        Model version string if registered, None if below threshold.
    """
    if accuracy < accuracy_threshold:
        logger.warning(
            f"Model accuracy {accuracy:.4f} below threshold {accuracy_threshold:.4f}. " "Skipping registry registration."
        )
        return None

    client = MlflowClient()
    model_uri = f"runs:/{run_id}/{model_artifact_path}"

    logger.info(f"Registering model '{model_name}' from run {run_id}...")
    result = mlflow.register_model(model_uri=model_uri, name=model_name)
    version = result.version
    logger.info(f"Model registered as version {version}")

    # Add accuracy tag to the version
    client.set_model_version_tag(model_name, version, "accuracy", f"{accuracy:.4f}")
    client.set_model_version_tag(model_name, version, "promoted_by", "training_pipeline")

    return version


def promote_model(
    model_name: str,
    version: str,
    stage: str = "Production",
    archive_existing: bool = True,
) -> None:
    """
    Promote a registered model version to a given stage (Staging / Production).

    Args:
        model_name: Registered model name.
        version: Model version to promote.
        stage: Target stage — "Staging" or "Production".
        archive_existing: If True, archive existing models in that stage first.
    """
    client = MlflowClient()

    if archive_existing:
        existing = client.get_latest_versions(model_name, stages=[stage])
        for mv in existing:
            logger.info(f"Archiving existing {stage} model version {mv.version}")
            client.transition_model_version_stage(
                name=model_name,
                version=mv.version,
                stage="Archived",
            )

    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=stage,
    )
    logger.info(f"Model '{model_name}' v{version} promoted to {stage}")


def get_production_model_uri(model_name: str) -> str:
    """
    Return the MLflow URI for the current Production model version.
    Falls back to the file-based model path if no production model exists.
    """
    import os

    client = MlflowClient()
    try:
        versions = client.get_latest_versions(model_name, stages=["Production"])
        if versions:
            uri = f"models:/{model_name}/Production"
            logger.info(f"Loaded production model URI: {uri}")
            return uri
    except Exception as e:
        logger.warning(f"Could not retrieve production model from registry: {e}")

    fallback = os.getenv("MODEL_PATH", "models/model.pkl")
    logger.info(f"Falling back to file-based model: {fallback}")
    return fallback
