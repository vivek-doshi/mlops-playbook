"""
Purpose:
    FastAPI REST API routes for Slack and email alert configuration.
    Reads and writes notification config YAML files.
    Does not send notifications directly — wraps the monitoring alertmanager config.

Usage:
    from portal.backend.api.notifications import router
    app.include_router(router, prefix="/api/notifications")

Dependencies:
    fastapi>=0.111, pyyaml>=6.0
"""

from __future__ import annotations

import os
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(tags=["notifications"])

_NOTIFICATIONS_DIR = os.environ.get("NOTIFICATIONS_DIR", "monitoring/alerts")


class NotificationConfig(BaseModel):
    model_name: str
    slack_channel: str | None = None
    email_recipients: list[str] = []
    alert_on_drift: bool = True
    alert_on_slo_breach: bool = True
    alert_on_failover: bool = True


@router.get("/{model_name}", summary="Get notification config for a model")
def get_notifications(model_name: str) -> dict[str, Any]:
    fpath = os.path.join(_NOTIFICATIONS_DIR, f"{model_name}-notifications.yaml")
    if not os.path.isfile(fpath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No notification config for '{model_name}'",
        )
    with open(fpath) as f:
        return yaml.safe_load(f)


@router.put("/{model_name}", summary="Update notification config")
def update_notifications(model_name: str, config: NotificationConfig) -> dict[str, str]:
    if model_name != config.model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_name in path must match body",
        )
    os.makedirs(_NOTIFICATIONS_DIR, exist_ok=True)
    fpath = os.path.join(_NOTIFICATIONS_DIR, f"{model_name}-notifications.yaml")
    with open(fpath, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)
    return {"status": "updated", "path": fpath}
