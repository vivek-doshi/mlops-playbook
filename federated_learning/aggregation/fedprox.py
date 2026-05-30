"""
Purpose:
    FedProx aggregation algorithm for heterogeneous (non-IID) data distributions.
    Adds a proximal term that penalises party updates that deviate too far from
    the global model, improving convergence when party data is skewed.

Usage:
    from federated_learning.aggregation.fedprox import fedprox_aggregate
    aggregated = fedprox_aggregate(global_weights, party_updates, mu=0.01)

Dependencies:
    torch>=2.3
"""

from __future__ import annotations

from typing import Any

import torch


def fedprox_aggregate(
    global_weights: dict[str, Any],
    party_updates: list[dict[str, Any]],
    mu: float = 0.01,
) -> dict[str, Any]:
    """
    FedProx aggregation: weight each party update by 1/(1 + mu * ||w_i - w_global||).

    A higher mu causes the aggregated result to stay closer to the global model,
    which is beneficial when party data distributions are very different.

    Args:
        global_weights: Current global model state dict.
        party_updates: List of state_dicts from each responding party.
        mu: Proximal regularisation strength (default 0.01).

    Returns:
        Aggregated state_dict.
    """
    if not party_updates:
        raise ValueError("party_updates must not be empty")

    keys = list(global_weights.keys())
    weights: list[float] = []
    for update in party_updates:
        deviation = sum(
            torch.norm(update[k].float() - global_weights[k].float()).item()
            for k in keys
        )
        weights.append(1.0 / (1.0 + mu * deviation))

    total_weight = sum(weights)
    aggregated: dict[str, Any] = {}
    for key in keys:
        stacked = torch.stack(
            [
                update[key].float() * (w / total_weight)
                for update, w in zip(party_updates, weights)
            ]
        )
        aggregated[key] = stacked.sum(dim=0)
    return aggregated
