"""
Purpose:
    Applies incremental model updates from a stream of mini-batches.
    Supports scikit-learn partial_fit and PyTorch single-epoch gradient steps.
    Enforces a 30-minute cooldown between updates and logs MLflow metrics for
    each update cycle (update_batch_size, update_mini_batch_count, stream_lag_seconds).

Usage:
    updater = OnlineUpdater(model=model, mlflow_run_id="abc123")
    updater.apply(mini_batch)

Dependencies:
    mlflow>=2.14, scikit-learn>=1.4, torch>=2.2
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any

import mlflow

logger = logging.getLogger(__name__)

_COOLDOWN_SECONDS = 1800  # 30 minutes


class OnlineUpdater:
    """
    Incremental model updater supporting sklearn and PyTorch models.

    Parameters
    ----------
    model : object
        Loaded sklearn estimator (must have partial_fit) or PyTorch Module.
    mlflow_run_id : str | None
        Active MLflow run to log metrics.  If None, metrics are only logged.
    cooldown_seconds : int
        Minimum seconds between updates.  Default 1800 (30 minutes).
    """

    def __init__(
        self,
        model: Any,
        mlflow_run_id: str | None = None,
        cooldown_seconds: int = _COOLDOWN_SECONDS,
    ) -> None:
        self._model = model
        self._mlflow_run_id = mlflow_run_id
        self._cooldown_seconds = cooldown_seconds
        self._last_update: float = 0.0
        self._mini_batch_count: int = 0

    def _is_sklearn(self) -> bool:
        return hasattr(self._model, "partial_fit")

    def _is_pytorch(self) -> bool:
        try:
            import torch.nn as nn
            return isinstance(self._model, nn.Module)
        except ImportError:
            return False

    def apply(
        self,
        batch: list[dict[str, Any]],
        feature_cols: list[str] | None = None,
        label_col: str = "label",
        stream_lag_seconds: float = 0.0,
    ) -> bool:
        """
        Apply a mini-batch update.  Respects cooldown.

        Returns True if the update was applied, False if within cooldown.
        """
        now = time.monotonic()
        if now - self._last_update < self._cooldown_seconds:
            remaining = int(self._cooldown_seconds - (now - self._last_update))
            logger.info("Cooldown active — skipping update (%ds remaining).", remaining)
            return False

        if not batch:
            logger.warning("Empty batch received; skipping update.")
            return False

        self._mini_batch_count += 1

        if self._is_sklearn():
            self._sklearn_update(batch, feature_cols, label_col)
        elif self._is_pytorch():
            self._pytorch_update(batch, feature_cols, label_col)
        else:
            raise TypeError("Model must support partial_fit (sklearn) or be a torch.nn.Module.")

        self._last_update = time.monotonic()
        self._log_metrics(
            update_batch_size=len(batch),
            update_mini_batch_count=self._mini_batch_count,
            stream_lag_seconds=stream_lag_seconds,
        )
        return True

    def _sklearn_update(
        self,
        batch: list[dict[str, Any]],
        feature_cols: list[str] | None,
        label_col: str,
    ) -> None:
        import numpy as np

        if feature_cols is None:
            feature_cols = [k for k in batch[0] if k != label_col]
        X = np.array([[row[c] for c in feature_cols] for row in batch], dtype=float)
        y = np.array([row[label_col] for row in batch])
        self._model.partial_fit(X, y)
        logger.info("sklearn partial_fit applied — batch_size=%d.", len(batch))

    def _pytorch_update(
        self,
        batch: list[dict[str, Any]],
        feature_cols: list[str] | None,
        label_col: str,
    ) -> None:
        import torch
        import torch.nn.functional as F

        if feature_cols is None:
            feature_cols = [k for k in batch[0] if k != label_col]

        X = torch.tensor(
            [[row[c] for c in feature_cols] for row in batch], dtype=torch.float32
        )
        y = torch.tensor([row[label_col] for row in batch], dtype=torch.long)

        optimizer = torch.optim.Adam(self._model.parameters(), lr=1e-4)
        self._model.train()
        optimizer.zero_grad()
        logits = self._model(X)
        loss = F.cross_entropy(logits, y)
        loss.backward()
        optimizer.step()
        logger.info(
            "PyTorch single-epoch gradient step — batch_size=%d, loss=%.4f.",
            len(batch),
            loss.item(),
        )

    def _log_metrics(
        self,
        update_batch_size: int,
        update_mini_batch_count: int,
        stream_lag_seconds: float,
    ) -> None:
        metrics = {
            "update_batch_size": update_batch_size,
            "update_mini_batch_count": update_mini_batch_count,
            "stream_lag_seconds": stream_lag_seconds,
        }
        logger.info("Online update metrics: %s", metrics)
        if self._mlflow_run_id:
            try:
                with mlflow.start_run(run_id=self._mlflow_run_id):
                    mlflow.log_metrics(metrics, step=update_mini_batch_count)
            except Exception as exc:
                logger.warning("Failed to log MLflow metrics: %s", exc)
