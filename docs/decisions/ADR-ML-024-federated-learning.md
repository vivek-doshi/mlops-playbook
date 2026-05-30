# ADR-ML-024: Federated Learning Architecture

**Status:** Accepted  
**Date:** 2026-05-30  
**Deciders:** Platform Engineering, Data Governance, MLOps Leads  

---

## Context

Several model training use cases involve data that is subject to jurisdiction-specific
data residency requirements (GDPR, HIPAA, etc.) and cannot be centralised for training.
Federated learning allows training a global model across these data silos without
ever moving raw data.

---

## Decision

### Aggregation: FedAvg default, FedProx for heterogeneous data

**Federated Averaging (FedAvg)** is the default algorithm.  It computes the simple
element-wise mean of all party weight updates.  It converges reliably when party
data distributions are roughly IID.

**FedProx** is offered as an alternative for non-IID (heterogeneous) data distributions.
It adds a proximal term `mu * ||w_i − w_global||` that penalises party updates
that deviate strongly from the global model, improving convergence stability.

The algorithm is a workflow input — operators choose at dispatch time.

### Raw data stays at the party — hard policy

Raw training data **NEVER** leaves the party's environment.  This is a hard policy
violation, not a recommendation.  Only model weights and gradients are transmitted.
This is documented in `policy/data-governance/README.md` and enforced by:
- Network policies that block data egress from party pods except on the model-weight port
- CI checks that verify no dataset paths appear in coordinator communication logs

### Differential Privacy (optional, recommended for sensitive data)

DP is optional but recommended for `confidential` and `restricted` classified data.
The `opacus` library provides DP-SGD for PyTorch parties.
`dp_epsilon` and `dp_delta` are required MLflow tags on every federated round when DP is active.

### Coordinator as Kubernetes Job

The coordinator runs as a **Kubernetes Job** per round — not a long-lived Deployment.
This ensures:
- No idle compute cost between rounds
- Clean failure semantics (Job status = round status)
- Round-level audit trail via Job completion events

### MLflow experiment naming

Federated models use experiment name `<model-name>-federated` and register each
aggregated model as a new version.  Tags `federated_round` and `federated_party_count`
are required on every run.

### TLS 1.3 minimum for gradient transmission

All coordinator ↔ party communication must be over TLS 1.3.  Parties reject
connections that do not present a valid certificate.  The `FEDERATED_TLS_VERIFY`
env var must be `"true"` in production.

---

## Consequences

**Positive:**
- Data residency requirements met — raw data never crosses jurisdiction boundary
- FedProx handles real-world non-IID distributions common in enterprise federated setups
- Job-per-round gives clean audit trail and avoids idle compute

**Negative:**
- Higher communication overhead than centralised training (N round-trips per round)
- Each party must expose an HTTPS endpoint accessible from the coordinator
- FedProx introduces a `mu` hyperparameter requiring tuning

---

## Alternatives considered

| Option | Reason rejected |
|---|---|
| Centralise data for training | Violates data residency requirements |
| Gradient-only transmission (no full weights) | Complicates aggregation and convergence analysis |
| Flower framework | Adds opinionated framework dependency; custom implementation is simpler for our scale |
| Secure aggregation (cryptographic) | Significant complexity overhead; accepted for future roadmap |
