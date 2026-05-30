# Federated Learning

Privacy-preserving model training across data silos where raw data cannot leave
its jurisdiction.  Each party trains on local data; only model gradients or
parameters are transmitted to the coordinator for aggregation.

## Architecture

```
Federated Coordinator (federated_learning/coordinator.py)
  ├── Holds global model state
  ├── Schedules training rounds (each round = 1 Kubernetes Job)
  └── Applies FedAvg (default) or FedProx aggregation

        ↓ sends global model weights (HTTPS / TLS 1.3)
        ↑ receives updated model weights

Party A (federated_learning/party.py)      Party B             Party N
  ├── Trains on LOCAL data only            ├── Local training  ...
  ├── Computes model update               └── Sends weights
  └── Optional: DP noise via opacus
```

> **HARD POLICY: Raw data NEVER leaves a party's environment.**
> Only model weights / gradients are transmitted.  See `policy/data-governance/README.md`.

## Aggregation algorithms

| Algorithm | When to use | Module |
|---|---|---|
| **FedAvg** (default) | IID-ish data distributions across parties | `aggregation/fedavg.py` |
| **FedProx** | Non-IID / heterogeneous data distributions | `aggregation/fedprox.py` |

## Differential Privacy

Optional DP support via [opacus](https://opacus.ai/).  Enable per-party with:

```bash
FEDERATED_USE_DP=true
FEDERATED_DP_EPSILON=1.0
FEDERATED_DP_DELTA=1e-5
```

When DP is enabled, `dp_epsilon` and `dp_delta` are logged as MLflow tags on every
federated round.

## MLflow conventions

| Tag | Value |
|---|---|
| `federated_round` | Round number (1…N) |
| `federated_party_count` | Number of responding parties |
| `aggregation_algorithm` | `fedavg` or `fedprox` |
| `dp_epsilon` | DP epsilon value (if DP enabled) |
| `dp_delta` | DP delta value (if DP enabled) |

Experiment name: `<model-name>-federated`  
Each round registers a new global model version in the MLflow registry.

## Security requirements

- Gradient transmission: **TLS 1.3 minimum** (enforced at network policy level)
- Parties are isolated: only the coordinator can initiate connections
- Coordinator runs as a **Kubernetes Job** per round — not a long-lived Deployment

## Quick start

### 1. Start a party

```python
from federated_learning.party import FederatedParty
party = FederatedParty(local_dataset=my_dataset, model=my_model)
party.serve(host="0.0.0.0", port=8443)
```

### 2. Run the coordinator

```python
from federated_learning.coordinator import FederatedCoordinator
coordinator = FederatedCoordinator(
    model_name="fraud-detector",
    global_model=my_model,
    party_endpoints=["https://party-a:8443", "https://party-b:8443"],
    rounds=10,
)
coordinator.run()
```

### 3. Trigger via CI

```bash
gh workflow run federated-train.yml \
  --field model_name=fraud-detector \
  --field rounds=10 \
  --field algorithm=fedavg \
  --field party_endpoints='["https://party-a:8443","https://party-b:8443"]'
```

## CI workflows

| Workflow | Purpose |
|---|---|
| `ci/github-actions/federated/federated-train.yml` | Coordinator: dispatch rounds, aggregate, register global model |
| `ci/github-actions/federated/federated-eval.yml` | Evaluate global model on coordinator-held test set; accuracy gate |
