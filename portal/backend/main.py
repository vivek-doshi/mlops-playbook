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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from portal.backend.api.models import router as models_router
from portal.backend.api.deployments import router as deployments_router
from portal.backend.api.budgets import router as budgets_router
from portal.backend.api.notifications import router as notifications_router

app = FastAPI(
    title="MLOps Self-Service Portal",
    description="Read-and-trigger portal for ML models, deployments, and budgets.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production via ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models_router, prefix="/api/models")
app.include_router(deployments_router, prefix="/api/deployments")
app.include_router(budgets_router, prefix="/api/budgets")
app.include_router(notifications_router, prefix="/api/notifications")


@app.get("/health", tags=["health"], summary="Liveness and readiness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}
