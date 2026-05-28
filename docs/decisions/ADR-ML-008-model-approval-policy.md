# ADR-ML-008: Three-Gate Model Approval Policy for Production Promotion

**Status:** Accepted
**Date:** 2024-11-01
**Authors:** ML Platform Team, ML Governance Team
**Reviewers:** @ml-approvers, @ml-governance-team

---

## Context

Promoting a model to production without structured evaluation gates has historically caused several classes of production incidents:

1. **Silent accuracy regression** — a model trained on fresh data scores lower on a held-out test set but the difference is not caught before deployment.
2. **Data lineage gaps** — a deployed model cannot be traced to the exact dataset hash that produced it, making audit and rollback difficult.
3. **Drift at deploy time** — the inference distribution at the time of deployment already differs from the training distribution (concept drift in the training data itself).

Regulatory and internal audit requirements additionally mandate:
- A record of who approved a model transition to production and when.
- A documented justification for any exception to the evaluation gates.
- The ability to roll back to a previous approved version within 30 minutes.

---

## Decision

We will enforce a **three-gate approval policy** for all model transitions to `Production` in the MLflow Model Registry.

The three gates, evaluated in sequence:

| Gate | Check | Failure action |
|------|-------|---------------|
| **Gate 1 — Accuracy** | Evaluation metric (accuracy, F1, AUC) must meet or exceed the threshold defined in `policy/model-approval/approved-versions.yaml` | Block promotion; open GitHub Issue from CI |
| **Gate 2 — Drift** | Evidently AI drift score on the evaluation dataset must be below 0.3 (warning threshold) | Block promotion; notify data team |
| **Gate 3 — Lineage** | MLflow run must have a `dvc_data_hash` tag matching the hash of the training dataset tracked in DVC | Block promotion; require re-training with verified data |

After all three gates pass automatically, a **human approval** step is required via GitHub Actions `environment: production` before the deployment workflow runs.

Implementation files:
- Gate evaluation: `ci/github-actions/model-evaluation/evaluate.yml`
- Deployment approval: `ci/github-actions/model-deployment/deploy.yml`
- Approved versions registry: `policy/model-approval/approved-versions.yaml`
- PII-specific checklist: `policy/data-governance/pii-model-checklist.md`

---

## Alternatives Considered

### Single accuracy-threshold gate
- **Pros:** Simpler. Fewer false-positive blocks.
- **Cons:** Does not catch data quality issues, lineage gaps, or deployment-time distribution shift. Does not satisfy audit requirements for traceability.

### Full Responsible AI platform (Azure RAI, Fiddler, Arthur AI)
- **Pros:** Rich dashboards; fairness metrics; automated reports.
- **Cons:** SaaS dependency (data residency concern). Significant platform cost. The three gates cover the 80% case without the overhead of a full RAI platform. RAI platform may be added as a future Layer 4 gate for high-risk models.

### MLflow Model Registry approvals only (no CI integration)
- **Pros:** Uses MLflow's built-in stage transitions.
- **Cons:** MLflow stage transitions are not auditable in GitHub — approvals would not appear in the PR/deployment history. Bypassing via `mlflow.register_model()` in a notebook is trivially easy without the CI gate wrapper.

### Shadow deployment / canary with automatic rollback
- **Partly adopted:** The deployment workflow includes a `kubectl rollout undo` on health probe failure. Full canary analysis (traffic-split + metric comparison) is deferred to a future ADR pending Argo Rollouts adoption in the platform repository.

---

## Consequences

**Positive:**
- Every production model has a traceable chain: Git commit → DVC data hash → MLflow run ID → approval actor + timestamp.
- The `approved-versions.yaml` file is the single source of truth for what is running in production — diffable, reviewable, auditable.
- PII-trained models have an additional checklist gate (DPO sign-off) gated via CODEOWNERS (`policy/data-governance/` requires `@data-protection-officer`).

**Negative:**
- The three gates add approximately 8–12 minutes to the promotion pipeline (drift check + Evidently evaluation is the bottleneck).
- Teams with very tight feedback loops (A/B test iteration) may find the manual approval step slow. A `fast-track` label on the PR can be used to skip the human gate for non-production environments only.

**Neutral:**
- Gate thresholds are configurable per model in `approved-versions.yaml` — a fraud detection model may set a higher accuracy threshold than an internal recommendation model.

---

## Review Triggers

Re-evaluate if:
- The team adopts continuous deployment (deploy every green commit) — the human gate would need to be replaced with automated canary + metric-based promotion.
- Regulatory requirements mandate a fourth gate (fairness / bias audit) for models in regulated verticals.
