"""
Purpose:
    FastAPI REST API routes for deployment status, logs, and health checks.
    Reads Kubernetes deployment state via k8s_client.py.
    Mutations (scale, rollout) are dispatched as GitHub Actions workflows.

Usage:
    from portal.backend.api.deployments import router
    app.include_router(router, prefix="/api/deployments")

Dependencies:
    fastapi>=0.111, kubernetes>=29.0
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from portal.backend.k8s_client import PortalK8sClient
from portal.backend.github_client import GitHubActionsClient

router = APIRouter(tags=["deployments"])


def _k8s() -> PortalK8sClient:
    return PortalK8sClient()


def _github() -> GitHubActionsClient:
    return GitHubActionsClient()


@router.get("/", summary="List all model deployments across namespaces")
def list_deployments(k8s: PortalK8sClient = Depends(_k8s)) -> list[dict[str, Any]]:
    return k8s.list_model_deployments()


@router.get("/{model_name}/{environment}", summary="Get deployment status and health")
def get_deployment(
    model_name: str,
    environment: str,
    k8s: PortalK8sClient = Depends(_k8s),
) -> dict[str, Any]:
    deployment = k8s.get_deployment_status(model_name=model_name, environment=environment)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment '{model_name}' in '{environment}' not found",
        )
    return deployment


@router.post("/{model_name}/{environment}/rollback", summary="Trigger rollback via GitHub Actions")
def rollback_deployment(
    model_name: str,
    environment: str,
    github_client: GitHubActionsClient = Depends(_github),
) -> dict[str, str]:
    """Dispatch rollback workflow. The portal never modifies Kubernetes directly."""
    run_id = github_client.trigger_workflow(
        workflow_id="rollback.yml",
        inputs={"model_name": model_name, "environment": environment},
    )
    return {"status": "dispatched", "workflow_run_id": run_id}
