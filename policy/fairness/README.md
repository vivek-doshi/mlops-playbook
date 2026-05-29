# Fairness Policy

This directory holds per-model fairness configurations used by the fairness
gate (`ci/github-actions/fairness/fairness-gate.yml`).

## Layout

```
policy/fairness/
├── _fairness-config-schema.yaml    # Schema reference — read this first
├── README.md                       # This file
└── <model-name>-fairness.yaml      # One file per model (see example below)
```

## Creating a fairness config for a new model

1. Copy `example-fairness-config.yaml` to `<model-name>-fairness.yaml`.
2. Set `model_name`, `label_column`, and `sensitive_features`.
3. Adjust `thresholds` if the model-specific risk profile requires it
   (e.g., a high-stakes classification task might warrant a tighter `fnr_disparity`).
4. Fill in `reviewed_by` and `review_date`.
5. Open a PR — a member of `@ml-approvers` must review and approve.

## Default thresholds (playbook policy)

| Metric | Threshold |
|---|---|
| `disparate_impact_ratio` | ≥ 0.80 |
| `equalised_odds_difference` | ≤ 0.10 |
| `fnr_disparity` | ≤ 0.10 |

Relaxing a threshold below the playbook default requires a PR comment from the
model owner explaining the business justification and approval by `@ml-approvers`.

## Gate enforcement

The fairness gate is:
- **Optional** in dev (warnings logged but gate not blocking)
- **Required** in staging and production

If the gate fails, the model cannot be promoted to staging or production.
The failure reason is included in the GitHub Actions workflow summary.
