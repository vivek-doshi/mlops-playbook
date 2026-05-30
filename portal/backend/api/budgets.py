"""
Purpose:
    FastAPI REST API routes for budget configuration CRUD.
    Reads and writes budget YAML files in finops/budgets/ via the filesystem.
    Budget changes are committed via GitHub Actions to maintain version history.

Usage:
    from portal.backend.api.budgets import router
    app.include_router(router, prefix="/api/budgets")

Dependencies:
    fastapi>=0.111, pyyaml>=6.0
"""

from __future__ import annotations

import os
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(tags=["budgets"])

_BUDGETS_DIR = os.environ.get("BUDGETS_DIR", "finops/budgets")


class BudgetUpdate(BaseModel):
    model_name: str
    monthly_limit_usd: float
    alert_threshold_pct: float = 0.80  # alert at 80% of limit


@router.get("/", summary="List all model budget configurations")
def list_budgets() -> list[dict[str, Any]]:
    budgets = []
    if not os.path.isdir(_BUDGETS_DIR):
        return budgets
    for fname in os.listdir(_BUDGETS_DIR):
        if fname.endswith(".yaml") or fname.endswith(".yml"):
            fpath = os.path.join(_BUDGETS_DIR, fname)
            with open(fpath) as f:
                budgets.append(yaml.safe_load(f))
    return budgets


@router.get("/{model_name}", summary="Get budget config for a model")
def get_budget(model_name: str) -> dict[str, Any]:
    fpath = os.path.join(_BUDGETS_DIR, f"{model_name}.yaml")
    if not os.path.isfile(fpath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No budget config found for model '{model_name}'",
        )
    with open(fpath) as f:
        return yaml.safe_load(f)


@router.put("/{model_name}", summary="Update budget config (writes YAML file)")
def update_budget(model_name: str, update: BudgetUpdate) -> dict[str, str]:
    if model_name != update.model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_name in path must match body",
        )
    os.makedirs(_BUDGETS_DIR, exist_ok=True)
    fpath = os.path.join(_BUDGETS_DIR, f"{model_name}.yaml")
    budget_data = {
        "model_name": model_name,
        "monthly_limit_usd": update.monthly_limit_usd,
        "alert_threshold_pct": update.alert_threshold_pct,
    }
    with open(fpath, "w") as f:
        yaml.dump(budget_data, f, default_flow_style=False)
    return {"status": "updated", "path": fpath}
