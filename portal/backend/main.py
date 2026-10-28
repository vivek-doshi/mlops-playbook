"""
Purpose:
    FastAPI application entrypoint for the self-service portal backend.
    Exposes /health for Kubernetes liveness/readiness probes.
    Aggregates routers for models, deployments, budgets, and notifications.

Usage:
    uvicorn portal.backend.main:app --host 0.0.0.0 --port 8080

Dependencies:
    fastapi>=0.111, uvicorn>=0.30
"""

from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from portal.backend.auth import require_user
from portal.backend.api.models import router as models_router
from portal.backend.api.deployments import router as deployments_router
from portal.backend.api.budgets import router as budgets_router
from portal.backend.api.notifications import router as notifications_router

app = FastAPI(
    title="MLOps Self-Service Portal",
    description="Read-and-trigger portal for ML models, deployments, and budgets.",
    version="1.0.0",
)


@app.middleware("http")
async def audit_api_requests(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        user = getattr(request.state, "user", {})
        logging.getLogger("portal.audit").info(
            "api_request method=%s path=%s status=%s subject=%s",
            request.method,
            request.url.path,
            response.status_code,
            user.get("sub", "unknown"),
        )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(models_router, prefix="/api/models", dependencies=[Depends(require_user)])
app.include_router(deployments_router, prefix="/api/deployments", dependencies=[Depends(require_user)])
app.include_router(budgets_router, prefix="/api/budgets", dependencies=[Depends(require_user)])
app.include_router(notifications_router, prefix="/api/notifications", dependencies=[Depends(require_user)])


@app.get("/health", tags=["health"], summary="Liveness and readiness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}
