"""
Purpose:
    FastAPI REST API routes for ML model registration, listing, and promotion.
    Read-only for model metadata (reads MLflow registry); all mutations
    are dispatched as GitHub Actions workflow triggers via github_client.py.

Usage:
    from portal.backend.api.models import router
    app.include_router(router, prefix="/api/models")

Dependencies:
    fastapi>=0.111, mlflow>=2.14
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from portal.backend.mlflow_client import PortalMLflowClient
from portal.backend.github_client import GitHubActionsClient

router = APIRouter(tags=["models"])


class PromoteRequest(BaseModel):
    model_name: str
    model_version: str
    target_environment: str  # dev | staging | production


def _mlflow() -> PortalMLflowClient:
    return PortalMLflowClient()


def _github() -> GitHubActionsClient:
    return GitHubActionsClient()


@router.get("/", summary="List all registered models")
def list_models(mlflow_client: PortalMLflowClient = Depends(_mlflow)) -> list[dict[str, Any]]:
    return mlflow_client.list_models()


@router.get("/{model_name}", summary="Get model details with versions and metrics")
def get_model(
    model_name: str,
    mlflow_client: PortalMLflowClient = Depends(_mlflow),
) -> dict[str, Any]:
    model = mlflow_client.get_model(model_name)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model '{model_name}' not found")
    return model


@router.post("/promote", summary="Trigger promotion workflow via GitHub Actions")
def promote_model(
    request: PromoteRequest,
    github_client: GitHubActionsClient = Depends(_github),
) -> dict[str, str]:
    """Dispatch a promotion workflow. The portal never modifies MLflow directly."""
    run_id = github_client.trigger_workflow(
        workflow_id="promote.yml",
        inputs={
            "model_name": request.model_name,
            "model_version": request.model_version,
            "target_environment": request.target_environment,
        },
    )
    return {"status": "dispatched", "workflow_run_id": run_id}
