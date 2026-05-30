"""
Purpose:
    Federated Averaging (FedAvg) aggregation algorithm.
    Computes the element-wise mean of model weights across participating parties.

Usage:
    from federated_learning.aggregation.fedavg import federated_average
    aggregated = federated_average(party_updates)

Dependencies:
    torch>=2.3
"""

from __future__ import annotations

from typing import Any

import torch


def federated_average(party_updates: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute element-wise mean of model state dicts from all parties.

    Args:
        party_updates: List of state_dict tensors from each responding party.

    Returns:
        Averaged state_dict.
    """
    if not party_updates:
        raise ValueError("party_updates must not be empty")

    keys = list(party_updates[0].keys())
    averaged: dict[str, Any] = {}
    for key in keys:
        stacked = torch.stack([update[key].float() for update in party_updates])
        averaged[key] = stacked.mean(dim=0)
    return averaged
