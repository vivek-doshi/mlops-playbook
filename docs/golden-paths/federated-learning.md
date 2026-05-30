# Golden Path: Federated Learning

This guide walks through setting up and running federated model training across
data silos using the MLOps playbook's federated learning framework.

## Prerequisites

- Each party has a running `FederatedParty` HTTP server accessible from the coordinator
- All party endpoints are HTTPS with TLS 1.3 certificates
- MLflow tracking server is reachable from the coordinator and all parties
- The global test dataset is available at `data/global_test.parquet` on the coordinator

---

## Step 1 — Confirm data residency policy

Before starting, verify that the data at each party is classified and that you
understand the data residency requirements.

> **HARD POLICY: Raw data NEVER leaves the party environment.**
> See `policy/data-governance/README.md` for the full policy.

---

## Step 2 — Start party servers

On each party's infrastructure:

```python
from federated_learning.party import FederatedParty

party = FederatedParty(
    local_dataset=load_local_dataset(),
    model=build_model_architecture(),
)
party.serve(host="0.0.0.0", port=8443)
```

Enable differential privacy if the data is `confidential`:

```bash
export FEDERATED_USE_DP=true
export FEDERATED_DP_EPSILON=1.0
export FEDERATED_DP_DELTA=1e-5
```

---

## Step 3 — Trigger federated training via CI

```bash
gh workflow run federated-train.yml \
  --field model_name=fraud-detector \
  --field rounds=10 \
  --field algorithm=fedavg \
  --field party_endpoints='["https://party-a.internal:8443","https://party-b.internal:8443"]'
```

Use `algorithm=fedprox` if party data distributions are heterogeneous.

---

## Step 4 — Monitor rounds in MLflow

Each round creates a new MLflow run in the `fraud-detector-federated` experiment.
Check tags:

| Tag | Expected value |
|---|---|
| `federated_round` | 1, 2, …, N |
| `federated_party_count` | Number of responding parties |
| `aggregation_algorithm` | `fedavg` or `fedprox` |
| `dp_epsilon` | Set if DP was enabled |

---

## Step 5 — Review the evaluation gate

After the final round, `federated-eval.yml` runs automatically and evaluates the
global model on the coordinator-held test set.  The workflow fails if accuracy
is below the configured gate (default: 0.80).

Check the Actions tab in GitHub for the evaluation output.

---

## Step 6 — Promote the global model

Once the evaluation gate passes, the global model version appears in the MLflow
registry under `fraud-detector`.  Use the Self-Service Portal or trigger the
`promote.yml` workflow to promote to Staging or Production.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Party returns connection error | TLS cert mismatch or port blocked | Check NetworkPolicy and cert chain |
| Round completes with 0 parties | All party requests timed out | Check party server logs and firewall |
| Eval accuracy below gate | Insufficient rounds or skewed data | Increase rounds or switch to FedProx |
| `dp_epsilon` missing from MLflow | opacus not installed on party | `pip install opacus` on party image |
