"""
Purpose:
    Differential privacy wrapper for federated learning parties using opacus.
    Wraps a PyTorch model and optimizer with DP-SGD noise addition.
    Logs dp_epsilon and dp_delta as MLflow tags on every federated round.

Usage:
    from federated_learning.privacy.dp_wrapper import DPWrapper
    model, optimizer, loader = DPWrapper.make_private(
        model, optimizer, loader, epsilon=1.0, delta=1e-5, epochs=3
    )

Dependencies:
    opacus>=1.4, mlflow>=2.14, torch>=2.3
"""

from __future__ import annotations

import logging
from typing import Any

import mlflow
import torch.nn as nn
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


class DPWrapper:
    """Convenience wrapper for opacus PrivacyEngine integration."""

    @staticmethod
    def make_private(
        model: nn.Module,
        optimizer: Any,
        data_loader: DataLoader,
        epsilon: float,
        delta: float,
        epochs: int,
        max_grad_norm: float = 1.0,
    ) -> tuple[nn.Module, Any, DataLoader]:
        """
        Apply DP-SGD to the given model/optimizer/loader.
        Logs dp_epsilon and dp_delta to the active MLflow run.

        Returns:
            Tuple of (dp_model, dp_optimizer, dp_loader).
        """
        try:
            from opacus import PrivacyEngine
        except ImportError as exc:
            raise RuntimeError(
                "opacus is required for differential privacy. "
                "Install with: pip install opacus"
            ) from exc

        privacy_engine = PrivacyEngine()
        dp_model, dp_optimizer, dp_loader = privacy_engine.make_private_with_epsilon(
            module=model,
            optimizer=optimizer,
            data_loader=data_loader,
            target_epsilon=epsilon,
            target_delta=delta,
            max_grad_norm=max_grad_norm,
            epochs=epochs,
        )
        # Log DP parameters to the active MLflow run (if one is active)
        try:
            mlflow.set_tags({"dp_epsilon": str(epsilon), "dp_delta": str(delta)})
        except Exception:
            pass  # No active run — caller is responsible for logging

        logger.info("DP-SGD enabled: epsilon=%.2f delta=%.2e", epsilon, delta)
        return dp_model, dp_optimizer, dp_loader
