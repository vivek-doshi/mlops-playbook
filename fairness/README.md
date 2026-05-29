# Fairness & Explainability Module

This directory contains the tools for evaluating model fairness and generating
SHAP-based explainability reports.

## Files

| File | Purpose |
|---|---|
| `evaluate.py` | Fairness metrics runner (fairlearn) — disparate impact, equalised odds, FNR |
| `explainability.py` | SHAP report generator — feature importance bar + beeswarm plots |

## Quick Start

### Fairness evaluation

```bash
python -m fairness.evaluate \
    --model-uri   models:/fraud-detection/3 \
    --test-data   data/test_features.parquet \
    --config      policy/fairness/fraud-detection-fairness.yaml \
    --report-path reports/fairness/fraud-detection-v3.json
```

### Explainability report

```bash
python -m fairness.explainability \
    --model-uri   models:/fraud-detection/3 \
    --test-data   data/test_features.parquet \
    --output-dir  reports/explainability/fraud-detection-v3/
```

## Fairness Thresholds (defaults)

| Metric | Threshold | Direction |
|---|---|---|
| `disparate_impact_ratio` | ≥ 0.80 | Higher is better |
| `equalised_odds_difference` | ≤ 0.10 | Lower is better |
| `fnr_disparity` | ≤ 0.10 | Lower is better |

Override thresholds per-model in `policy/fairness/<model-name>-fairness.yaml`.

## CI Integration

The fairness gate runs automatically in `ci/github-actions/fairness/fairness-gate.yml`.
It is a required gate for staging and production promotions.

## Dependencies

```
fairlearn>=0.10
shap>=0.44
mlflow>=2.11
pandas>=2.0
scikit-learn>=1.4
matplotlib>=3.8
```

## Further Reading

- `policy/fairness/` — per-model fairness configs and schema
- `docs/golden-paths/fairness-and-explainability.md` — step-by-step guide
- `docs/decisions/ADR-ML-015-fairness-framework.md` — design rationale
