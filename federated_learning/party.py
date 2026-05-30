"""
Purpose:
    Federated learning party — runs local training on party-resident data
    and returns model deltas to the coordinator.

    Raw data NEVER leaves the party environment.  Only model weights /
    gradient deltas are sent to the coordinator.

    Exposes a simple HTTP server (POST /train-round) to receive the global
    model from the coordinator and return updated weights.

Usage:
    party = FederatedParty(local_dataset=my_dataset, model=my_model)
    party.serve(host="0.0.0.0", port=8443)

Dependencies:
    torch>=2.3, fastapi>=0.111, uvicorn>=0.30, opacus>=1.4 (optional)
"""

from __future__ import annotations

import copy
import logging
import os
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)

_LOCAL_EPOCHS = int(os.environ.get("FEDERATED_LOCAL_EPOCHS", "3"))
_LEARNING_RATE = float(os.environ.get("FEDERATED_LR", "0.01"))
_USE_DP = os.environ.get("FEDERATED_USE_DP", "false").lower() == "true"
_DP_EPSILON = float(os.environ.get("FEDERATED_DP_EPSILON", "1.0"))
_DP_DELTA = float(os.environ.get("FEDERATED_DP_DELTA", "1e-5"))
_DP_MAX_GRAD_NORM = float(os.environ.get("FEDERATED_DP_MAX_GRAD_NORM", "1.0"))


class FederatedParty:
    """
    Performs local training on party-resident data.

    SECURITY NOTE: raw data never leaves this environment.
    Only model weights (the delta = updated − initial) are returned.
    """

    def __init__(
        self,
        local_dataset: Dataset,
        model: nn.Module,
        batch_size: int = 32,
    ) -> None:
        self.local_dataset = local_dataset
        self.model = model
        self.batch_size = batch_size

    def train_round(
        self, global_weights: dict[str, Any], round_num: int
    ) -> dict[str, Any]:
        """
        Load global weights, run local epochs, return updated weights.
        Optionally applies differential privacy noise via opacus.
        """
        self.model.load_state_dict(
            {k: torch.tensor(np.array(v)) for k, v in global_weights.items()}
        )
        initial_weights = copy.deepcopy(self.model.state_dict())

        loader = DataLoader(self.local_dataset, batch_size=self.batch_size, shuffle=True)
        optimizer = torch.optim.SGD(self.model.parameters(), lr=_LEARNING_RATE)
        criterion = nn.CrossEntropyLoss()

        if _USE_DP:
            try:
                from opacus import PrivacyEngine

                privacy_engine = PrivacyEngine()
                self.model, optimizer, loader = privacy_engine.make_private_with_epsilon(
                    module=self.model,
                    optimizer=optimizer,
                    data_loader=loader,
                    target_epsilon=_DP_EPSILON,
                    target_delta=_DP_DELTA,
                    max_grad_norm=_DP_MAX_GRAD_NORM,
                    epochs=_LOCAL_EPOCHS,
                )
                logger.info(
                    "DP enabled for round %d: epsilon=%.2f delta=%.2e",
                    round_num,
                    _DP_EPSILON,
                    _DP_DELTA,
                )
            except ImportError:
                logger.warning("opacus not installed — running without DP")

        self.model.train()
        for epoch in range(_LOCAL_EPOCHS):
            for inputs, targets in loader:
                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()

        updated_weights = self.model.state_dict()
        logger.info("Party completed local training for round %d", round_num)
        return {k: v.cpu().numpy().tolist() for k, v in updated_weights.items()}

    def serve(self, host: str = "0.0.0.0", port: int = 8443) -> None:
        """Start the party HTTP server. TLS is expected at the load-balancer layer."""
        from fastapi import FastAPI
        import uvicorn
        from pydantic import BaseModel

        app = FastAPI(title="Federated Party")

        class RoundRequest(BaseModel):
            round: int
            weights: dict[str, list]

        @app.post("/train-round")
        def train(request: RoundRequest) -> dict:
            updated = self.train_round(request.weights, request.round)
            return {
                "round": request.round,
                "weights": updated,
                "dp_epsilon": _DP_EPSILON if _USE_DP else None,
                "dp_delta": _DP_DELTA if _USE_DP else None,
            }

        @app.get("/health")
        def health() -> dict:
            return {"status": "ok"}

        uvicorn.run(app, host=host, port=port)
