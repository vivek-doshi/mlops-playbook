"""
Purpose:
    Prompt registry for versioned, validated prompt templates used by LLM serving.
    Prompts are stored as YAML files matching llmops/prompts/schema.yaml and
    tracked in MLflow as named artifacts under the experiment <model-name>-prompts.

    The registry supports:
      - Registering a new prompt version.
      - Loading the latest or a specific version of a prompt.
      - Validating prompt files against the schema.

Usage:
    from llmops.prompts.registry import PromptRegistry

    registry = PromptRegistry()
    registry.register(model_name="my-llm", prompt_file=Path("prompts/v3.yaml"))
    template = registry.load(model_name="my-llm", version="latest")

Dependencies:
    mlflow>=2.11
    pyyaml>=6.0
    jsonschema>=4.0
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

try:
    import mlflow
    import jsonschema
except ImportError as exc:
    raise ImportError(
        f"{exc}\nInstall with: pip install mlflow pyyaml jsonschema"
    ) from exc

_SCHEMA_PATH = Path(__file__).parent / "schema.yaml"


def _load_schema() -> dict[str, Any]:
    if not _SCHEMA_PATH.exists():
        return {}
    return yaml.safe_load(_SCHEMA_PATH.read_text())


class PromptRegistry:
    """Manages versioned prompt templates via MLflow artifact storage."""

    def __init__(self, tracking_uri: str | None = None) -> None:
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        self._schema = _load_schema()
        self._client = mlflow.tracking.MlflowClient()

    def validate(self, prompt_data: dict[str, Any]) -> None:
        """Raise jsonschema.ValidationError if prompt_data violates the schema."""
        if self._schema:
            jsonschema.validate(prompt_data, self._schema)

    def register(
        self,
        model_name: str,
        prompt_file: Path,
        description: str = "",
    ) -> str:
        """
        Register a prompt file.  Validates against schema, logs to MLflow, and
        returns the MLflow run ID for the registration.
        """
        prompt_data: dict[str, Any] = yaml.safe_load(prompt_file.read_text())
        self.validate(prompt_data)

        # Content hash for deduplication
        content_hash = hashlib.sha256(
            json.dumps(prompt_data, sort_keys=True).encode()
        ).hexdigest()[:12]

        experiment_name = f"{model_name}-prompts"
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(
            tags={
                "prompt_name": prompt_data.get("name", prompt_file.stem),
                "content_hash": content_hash,
                "description": description,
            }
        ) as run:
            mlflow.log_artifact(str(prompt_file), artifact_path="prompt")
            mlflow.log_param("prompt_name", prompt_data.get("name", prompt_file.stem))
            mlflow.log_param("content_hash", content_hash)
            return run.info.run_id

    def load(self, model_name: str, version: str = "latest") -> dict[str, Any]:
        """
        Load a prompt template from MLflow.

        version: "latest" returns the most recently registered prompt,
                 or a specific MLflow run ID can be supplied.
        """
        experiment_name = f"{model_name}-prompts"
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise ValueError(
                f"No prompt experiment found for model '{model_name}'."
            )

        if version == "latest":
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["start_time DESC"],
                max_results=1,
            )
            if runs.empty:
                raise ValueError(
                    f"No prompts registered for model '{model_name}'."
                )
            run_id = runs.iloc[0]["run_id"]
        else:
            run_id = version

        artifacts_dir = Path(
            mlflow.artifacts.download_artifacts(
                run_id=run_id, artifact_path="prompt"
            )
        )
        prompt_files = list(artifacts_dir.glob("*.yaml")) + list(artifacts_dir.glob("*.yml"))
        if not prompt_files:
            raise ValueError(
                f"No YAML prompt file found in MLflow artifacts for run {run_id}."
            )
        return yaml.safe_load(prompt_files[0].read_text())
