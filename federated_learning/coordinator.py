"""
Purpose:
    Federated learning round coordinator. Orchestrates multi-round training
    across parties, aggregates model updates using FedAvg (default) or FedProx,
    and registers the global model in MLflow after each round.

    Each round is logged as a separate MLflow run tagged:
      - federated_round: <N>
      - federated_party_count: <N>

    Gradient transmission is expected to be over TLS 1.3 (enforced at
    network policy level — see cd/kubernetes/federated/).

Usage:
    coordinator = FederatedCoordinator(
        model_name="fraud-detector",
        party_endpoints=["https://party-a:8443", "https://party-b:8443"],
        rounds=10,
    )
    coordinator.run()

Dependencies:
    mlflow>=2.14, torch>=2.3, numpy>=1.26
"""

from __future__ import annotations

import copy
import logging
import os
from typing import Any

import mlflow
import numpy as np
import torch
import torch.nn as nn

from federated_learning.aggregation.fedavg import federated_average
from federated_learning.aggregation.fedprox import fedprox_aggregate

logger = logging.getLogger(__name__)

_MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
_TLS_VERIFY = os.environ.get("FEDERATED_TLS_VERIFY", "true").lower() != "false"


class FederatedCoordinator:
    """
    Orchestrates federated training rounds.

    The coordinator holds the global model, sends its weights to each party,
    receives model deltas, and applies FedAvg (or FedProx) aggregation.
    """

    def __init__(
        self,
        model_name: str,
        global_model: nn.Module,
        party_endpoints: list[str],
        rounds: int = 10,
        algorithm: str = "fedavg",  # "fedavg" | "fedprox"
        fedprox_mu: float = 0.01,
    ) -> None:
        self.model_name = model_name
        self.global_model = global_model
        self.party_endpoints = party_endpoints
        self.rounds = rounds
        self.algorithm = algorithm
        self.fedprox_mu = fedprox_mu

        mlflow.set_tracking_uri(_MLFLOW_TRACKING_URI)
        self._experiment_name = f"{model_name}-federated"
        mlflow.set_experiment(self._experiment_name)

    def _send_and_receive(
        self, party_url: str, global_weights: dict[str, Any], round_num: int
    ) -> dict[str, Any] | None:
        """
        Send global weights to a party and receive updated weights.
        Communication is HTTPS-only (TLS 1.3 enforced by network policy).
        """
        try:
            import httpx

            resp = httpx.post(
                f"{party_url}/train-round",
                json={"round": round_num, "weights": _weights_to_list(global_weights)},
                verify=_TLS_VERIFY,
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()
            return _list_to_weights(data["weights"], global_weights)
        except Exception as exc:
            logger.warning("Party %s failed in round %d: %s", party_url, round_num, exc)
            return None

    def run(self) -> None:
        for round_num in range(1, self.rounds + 1):
            logger.info("Starting federated round %d / %d", round_num, self.rounds)
            global_weights = copy.deepcopy(self.global_model.state_dict())

            # Collect updates from all parties
            party_updates: list[dict[str, Any]] = []
            for endpoint in self.party_endpoints:
                updated = self._send_and_receive(endpoint, global_weights, round_num)
                if updated is not None:
                    party_updates.append(updated)

            if not party_updates:
                logger.error("No parties responded in round %d — aborting.", round_num)
                break

            # Aggregate
            if self.algorithm == "fedprox":
                aggregated = fedprox_aggregate(
                    global_weights, party_updates, mu=self.fedprox_mu
                )
            else:
                aggregated = federated_average(party_updates)

            self.global_model.load_state_dict(aggregated)

            # Log round to MLflow
            with mlflow.start_run(run_name=f"round-{round_num}") as run:
                mlflow.set_tags(
                    {
                        "federated_round": round_num,
                        "federated_party_count": len(party_updates),
                        "aggregation_algorithm": self.algorithm,
                    }
                )
                mlflow.log_params(
                    {
                        "round": round_num,
                        "total_parties": len(self.party_endpoints),
                        "responding_parties": len(party_updates),
                    }
                )
                # Register updated global model
                mlflow.pytorch.log_model(
                    self.global_model,
                    artifact_path="model",
                    registered_model_name=self.model_name,
                )
                logger.info(
                    "Round %d complete — run_id=%s", round_num, run.info.run_id
                )


# ── Serialisation helpers (weights → JSON-serialisable list and back) ─────────


def _weights_to_list(state_dict: dict[str, Any]) -> dict[str, list]:
    return {k: v.cpu().numpy().tolist() for k, v in state_dict.items()}


def _list_to_weights(
    raw: dict[str, list], reference: dict[str, Any]
) -> dict[str, Any]:
    return {
        k: torch.tensor(np.array(raw[k]), dtype=reference[k].dtype)
        for k in reference
    }
