# ADR-ML-019 — Online Learning Pipeline

| Field       | Value                                             |
|-------------|---------------------------------------------------|
| ID          | ADR-ML-019                                        |
| Status      | Accepted                                          |
| Date        | 2025-05-30                                        |
| Deciders    | ML Engineering, Platform Engineering              |

---

## Context

Several production models degrade due to concept drift within days of deployment.
Offline retraining pipelines require at least 1–2 hours of compute and human review
before a new version reaches Production.  This creates a window where the model
operates on stale feature distributions.

Use cases requiring faster adaptation:

- Fraud detection: fraud patterns evolve within hours of a new campaign.
- Recommendation models: user preferences shift seasonally and within trending events.
- NLP classifiers: new terminology and topics not present in training data.

---

## Decision

### Stream Sources

**Kafka** is the default stream source for on-premises and hybrid deployments.
AWS Kinesis Data Streams and GCP Pub/Sub are supported as alternatives via the
consumer dispatcher (`online_learning/consumer.py`).

### Update Strategy

| Model type | Update method |
|---|---|
| scikit-learn | `partial_fit()` — incremental learning without full re-fit |
| PyTorch | Single-epoch gradient step on the mini-batch |

### Gates

Three gates must pass before an online update is committed:

| Gate | Threshold | Enforcement |
|---|---|---|
| Minimum batch size | ≥ 500 records | `OnlineUpdater.apply()` |
| Cooldown | 30 minutes between updates | `OnlineUpdater._last_update` |
| Accuracy drop | ≤ 2% vs. baseline holdout | `OnlineValidator.evaluate()` |

### Rollback

If the accuracy gate fails, `OnlineRollback.execute()` archives the failing version
and restores the most recent eligible version to Production.  The restored version
is tagged `online_update: restored_after_rollback`.

### MLflow Tags

All online-updated model versions carry `online_update: true`.  This allows
monitoring and audit queries to distinguish online-updated versions from
offline-trained versions.

---

## Alternatives Considered

### A: Retrain from scratch on each batch

**Rejected**: too slow for sub-minute concept drift; infeasible compute cost for
large models.

### B: Shadow mode with delayed promotion

**Rejected**: adds 15–30 minutes of promotion latency; acceptable for scheduled
retraining but not for emergency concept-drift response.

### C: River (streaming ML library)

**Considered**: River provides purpose-built online learning algorithms but does not
support PyTorch models or the PEFT fine-tuning approach used in LLMOps.  We opted
for a thin wrapper over sklearn's `partial_fit` and PyTorch training loops to avoid
an additional framework dependency.

---

## Consequences

**Positive**:
- Sub-minute adaptation to concept drift for sklearn models.
- Automatic rollback prevents accuracy degradation from noisy batches.
- Stream source is swappable without changing update logic.

**Negative / Risks**:
- `partial_fit` does not support all sklearn estimators; check compatibility.
- Single-epoch gradient steps may cause PyTorch models to overfit on small batches
  if learning rate is too high.  Default lr=1e-4 is conservative.
- Holdout data must remain representative; if holdout drifts, the gate becomes unreliable.

---

## Related Decisions

- [ADR-ML-004](ADR-ML-004-drift-monitoring.md) — Drift Monitoring (trigger source)
- [ADR-ML-008](ADR-ML-008-model-approval-policy.md) — Model Approval Policy
- [ADR-ML-022](ADR-ML-022-llmops.md) — LLMOps (full fine-tune alternative)
