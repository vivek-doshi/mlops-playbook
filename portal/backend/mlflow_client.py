"""
Purpose:
    MLflow client wrapper for the self-service portal.
    Provides read-only access to the MLflow Model Registry and run metrics.
    Never modifies MLflow state — all mutations go through GitHub Actions.

Usage:
    client = PortalMLflowClient()
    models = client.list_models()

Dependencies:
    mlflow>=2.14
"""

from __future__ import annotations

import logging
import os
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)

_MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")


class PortalMLflowClient:
    """Read-only wrapper for MLflow registry operations used by the portal."""

    def __init__(self) -> None:
        mlflow.set_tracking_uri(_MLFLOW_TRACKING_URI)
        self._client = MlflowClient()

    def list_models(self) -> list[dict[str, Any]]:
        models = self._client.search_registered_models()
        return [
            {
                "name": m.name,
                "latest_versions": [
                    {
                        "version": v.version,
                        "stage": v.current_stage,
                        "run_id": v.run_id,
                    }
                    for v in m.latest_versions
                ],
            }
            for m in models
        ]

    def get_model(self, model_name: str) -> dict[str, Any] | None:
        try:
            model = self._client.get_registered_model(model_name)
        except Exception:
            return None
        versions = self._client.search_model_versions(f"name='{model_name}'")
        return {
            "name": model.name,
            "description": model.description,
            "tags": dict(model.tags),
            "versions": [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "run_id": v.run_id,
                    "tags": dict(v.tags),
                }
                for v in versions
            ],
        }
