"""
Purpose:
    Automatic rollback for online-learned model versions when accuracy drops
    more than 2%.  Restores the previous Production model from the MLflow
    Model Registry and sets the online_update tag to reflect the rollback.

Usage:
    rollback = OnlineRollback(model_name="fraud-detector")
    rollback.execute(current_version="12", reason="accuracy_drop")

Dependencies:
    mlflow>=2.14
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import mlflow
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class OnlineRollback:
    """
    Rolls back an online-updated model to the previous Production version.

    Parameters
    ----------
    model_name : str
        MLflow registered model name.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._client = MlflowClient()

    def _get_current_production_version(self) -> str | None:
        versions = self._client.get_latest_versions(self._model_name, stages=["Production"])
        if not versions:
            return None
        return versions[0].version

    def execute(self, current_version: str, reason: str = "accuracy_drop") -> str | None:
        """
        Transition current_version to Archived and promote the previous
        Production version back to Production.

        Returns the restored version string, or None if no candidate found.
        """
        logger.warning(
            "Initiating rollback for %s v%s — reason: %s",
            self._model_name,
            current_version,
            reason,
        )

        # Archive the failing version
        self._client.transition_model_version_stage(
            name=self._model_name,
            version=current_version,
            stage="Archived",
        )
        self._client.set_model_version_tag(
            name=self._model_name,
            version=current_version,
            key="online_update",
            value="rolled_back",
        )
        self._client.set_model_version_tag(
            name=self._model_name,
            version=current_version,
            key="rollback_reason",
            value=reason,
        )
        self._client.set_model_version_tag(
            name=self._model_name,
            version=current_version,
            key="rollback_at",
            value=datetime.now(tz=timezone.utc).isoformat(),
        )

        # Find the most recent Staging or previous Production version to restore
        all_versions = self._client.search_model_versions(f"name='{self._model_name}'")
        candidates = [
            v for v in all_versions
            if v.version != current_version and v.current_stage in ("Staging", "None")
        ]
        if not candidates:
            logger.error("No candidate version found for rollback of %s.", self._model_name)
            return None

        # Use the highest version number as restore target
        restore_target = max(candidates, key=lambda v: int(v.version))
        self._client.transition_model_version_stage(
            name=self._model_name,
            version=restore_target.version,
            stage="Production",
        )
        self._client.set_model_version_tag(
            name=self._model_name,
            version=restore_target.version,
            key="online_update",
            value="restored_after_rollback",
        )
        logger.info(
            "Rollback complete — %s v%s restored to Production.",
            self._model_name,
            restore_target.version,
        )
        return restore_target.version
