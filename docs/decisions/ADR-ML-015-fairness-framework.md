# ADR-ML-015: Fairness & Explainability Framework

**Status:** Accepted  
**Date:** 2026-05-29  
**Authors:** ML Platform Team  
**Reviewers:** @ml-approvers

---

## Context

As ML models are promoted to production they may interact with users across
protected demographic groups.  Without structured fairness evaluation the
organisation risks:

1. Deploying models that systematically disadvantage protected groups (legal,
   reputational, ethical risk).
2. Having no audit trail when a fairness complaint is raised.
3. Making explainability ad-hoc — different analysts using different SHAP
   settings produce incompatible reports.

Existing tooling in this playbook covers accuracy, drift, and performance gates
but has no structured fairness or explainability step.

Regulatory context: the EU AI Act (2024) classifies high-risk AI systems and
mandates bias assessment; internal data governance policy requires fairness
review for any model used in customer-facing decisions.

---

## Decision

We will adopt **fairlearn** for fairness metrics and **SHAP (KernelExplainer)**
for model-agnostic explainability, enforced as a mandatory gate before staging
and production promotion.

### Fairness library: fairlearn ≥ 0.10

Rationale:
- Scikit-learn compatible API — works with any pyfunc model via a predict wrapper.
- Built-in `MetricFrame` computes per-group metrics and overall metrics together.
- Provides both assessment (our use case) and mitigation (`ThresholdOptimizer`,
  `GridSearch`).
- Active maintenance and Microsoft sponsorship (aligns with Azure ecosystem).

Alternative rejected: IBM's AI Fairness 360 — larger dependency surface, less
active maintenance.

### Explainability library: SHAP ≥ 0.44 (KernelExplainer)

Rationale:
- Model-agnostic: works for any pyfunc model via a predict function wrapper.
- KernelExplainer requires no model-internal access — compatible with opaque
  serving containers.
- SHAP values are the industry standard for local feature attribution.

Alternative rejected: LIME — SHAP is more stable and reproducible;
LIME's kernel width selection is dataset-dependent.

### Fairness thresholds (playbook defaults)

| Metric | Threshold | Rationale |
|---|---|---|
| `disparate_impact_ratio` | ≥ 0.80 | US EEOC 4/5ths rule; widely accepted baseline |
| `equalised_odds_difference` | ≤ 0.10 | Practical bound on differential error rates |
| `fnr_disparity` | ≤ 0.10 | Protects against disproportionate missed detections |

Individual models may tighten (but not relax below default) thresholds via
`policy/fairness/<model-name>-fairness.yaml` with `@ml-approvers` sign-off.

### Gate placement

| Environment | Fairness gate | Behaviour |
|---|---|---|
| dev | Optional | Logs results; `gate_mode=warn` (never blocks) |
| staging | Required | `gate_mode=fail` — blocks promotion on violation |
| production | Required | `gate_mode=fail` — blocks promotion on violation |

### Config-as-code approach

Each model has a fairness config in `policy/fairness/<model-name>-fairness.yaml`.
This makes threshold decisions reviewable as code diffs and auditable via git history.

---

## Alternatives Considered

### Option A: Run fairness checks in a Jupyter notebook (ad-hoc)

**Pros:** Flexible, interactive.  
**Cons:** Not reproducible across runs.  No enforcement — a developer can skip it.
No audit record.  
**Rejected.**

### Option B: Delegate fairness to the model owner's custom pre-PR script

**Pros:** Flexibility per model.  
**Cons:** Inconsistent metrics, thresholds, and tooling.  Cannot be compared
across models.  No central audit trail.  
**Rejected.**

### Option C: Embed fairness checks inside the existing evaluate.yml

**Pros:** Fewer workflow files.  
**Cons:** evaluate.yml is already the accuracy/drift/lineage gate.  Mixing
concerns makes it harder to add or adjust the fairness gate independently.
Separate `fairness-gate.yml` can be versioned and updated without touching
the accuracy gate.  
**Rejected.**

---

## Consequences

### Positive

- Structured, auditable fairness gate enforced in CI for every model.
- Per-model config-as-code — threshold decisions are reviewable in PRs.
- SHAP reports stored as 90-day artifacts alongside each promotion run.
- Prometheus fairness alerts provide continuous monitoring post-deployment.

### Negative / Trade-offs

- `KernelExplainer` is slow for large datasets.  Background sample is capped at
  100 rows; this approximates SHAP values but may miss rare-feature interactions.
- Fairness metrics depend on sensitive-feature columns being present in test data.
  If a dataset does not include demographic columns, the gate will skip per-group
  analysis (warning logged).
- Adding new dependencies: `fairlearn>=0.10`, `shap>=0.44`, `matplotlib>=3.8`.

### Mitigation

For large models where KernelExplainer is prohibitively slow, teams may use
`shap.TreeExplainer` (for tree models) or `shap.LinearExplainer` (for linear
models) by subclassing `fairness/explainability.py`.

---

## Review Triggers

This ADR should be revisited if:

- EU AI Act implementing regulations change the required fairness metrics.
- A faster or more accurate explainability library becomes available and is
  compatible with the model-agnostic serving constraint.
- The playbook adopts a dedicated fairness monitoring platform (e.g., Azure
  Responsible AI Dashboard) that supersedes the custom gate.
