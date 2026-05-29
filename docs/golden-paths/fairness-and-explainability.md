# Fairness & Explainability Golden Path

## Purpose and Scope

This golden path describes how to measure model fairness using **fairlearn** and
generate SHAP-based explainability reports.  It applies to any model that:

- Uses features that are correlated with a protected attribute (age, gender, etc.), or
- Is deployed in a high-stakes context (credit, fraud, healthcare, hiring).

> **Beginner tip**: Fairness evaluation asks "does our model treat different groups
> of people equally?" Explainability asks "why did the model make this prediction?"
> Neither replaces the other — you need both.

---

## Prerequisites

| Requirement | Where to get it |
|---|---|
| Trained model registered in MLflow | `docs/golden-paths/model-registry.md` |
| Test dataset with sensitive columns | `docs/golden-paths/data-versioning.md` |
| Fairness config file | `policy/fairness/` (see below) |

---

## Step 1: Create a Fairness Config

Copy the example and edit it for your model:

```bash
cp policy/fairness/example-fairness-config.yaml \
   policy/fairness/<model-name>-fairness.yaml
```

Edit the file:

```yaml
model_name: <model-name>
label_column: label         # column with ground-truth labels in your test data
sensitive_features:
  - age_group               # one or more columns from your test Parquet
  - gender

thresholds:
  disparate_impact_ratio:    0.80   # min ratio of group selection rates
  equalised_odds_difference: 0.10   # max across-group EOD
  fnr_disparity:             0.10   # max FNR gap between groups
```

Open a PR.  A member of `@ml-approvers` must review and approve before the
config is used in a gate.

---

## Step 2: Run Fairness Evaluation Locally

```bash
pip install "fairlearn>=0.10" mlflow pandas scikit-learn pyyaml

python fairness/evaluate.py \
    --model-uri   models:/<model-name>/<version> \
    --test-data   data/test_features.parquet \
    --config      policy/fairness/<model-name>-fairness.yaml \
    --report-path reports/fairness/<model-name>-v<version>.json
```

The script exits 0 on pass, 1 on violation.

---

## Step 3: Run SHAP Explainability Locally

```bash
pip install "shap>=0.44" matplotlib

python fairness/explainability.py \
    --model-uri   models:/<model-name>/<version> \
    --test-data   data/test_features.parquet \
    --output-dir  reports/explainability/<model-name>-v<version>/
```

Outputs:
- `shap_bar_summary.png` — ranked feature importance
- `shap_beeswarm.png` — per-sample SHAP value spread
- `explainability_report.json` — top features with mean |SHAP|

---

## Step 4: CI Integration

The fairness gate is part of the promotion pipeline.

### Automatic (staging + production)

`promote-staging.yml` and `promote-production.yml` call `fairness-gate.yml`
automatically.  No extra steps required once the fairness config exists.

### Manual trigger

```bash
gh workflow run fairness-gate.yml \
  --field model_name=<model-name> \
  --field model_version=<version> \
  --field gate_mode=fail
```

---

## Interpreting Results

### Disparate Impact Ratio

$$\text{DI} = \frac{\min_g \text{selection\_rate}(g)}{\max_g \text{selection\_rate}(g)}$$

- DI = 1.0 → all groups have the same selection (positive prediction) rate.
- DI = 0.80 → the least-selected group is selected 80% as often as the most-selected.
- DI < 0.80 → **FAIL** (US EEOC 4/5ths rule threshold).

### Equalised Odds Difference

Maximum absolute difference in TPR and FPR across groups.

- 0.00 → equal TPR and FPR across all groups.
- > 0.10 → **FAIL** (groups experience meaningfully different error rates).

### FNR Disparity

Maximum absolute FNR difference between the best and worst group.

High FNR disparity is particularly harmful in fraud / medical screening (missed
detections have different consequences for different groups).

---

## Resolving a Fairness Failure

1. **Investigate data imbalance** — are some groups underrepresented in training data?
2. **Check threshold labels** — are some groups systematically mislabelled?
3. **Apply mitigation**:
   - Pre-processing: resample, reweight, or use fairlearn's `GridSearch` with
     fairness constraints.
   - Post-processing: use `ThresholdOptimizer` to calibrate per-group thresholds.
4. Re-train and re-evaluate.
5. If a business justification requires relaxing a threshold, update the
   `policy/fairness/<model-name>-fairness.yaml` with a `notes` explanation
   and get `@ml-approvers` sign-off.

---

## Monitoring Fairness in Production

Prometheus alerts in `monitoring/fairness/fairness-alerts.yaml` fire when:

- Disparate impact ratio drops below 0.80 (critical).
- Equalised odds difference exceeds 0.10 (warning).
- FNR disparity exceeds 0.10 (warning).
- Fairness evaluation has not run in 7 days (staleness guard).

---

## Further Reading

- `fairness/` — evaluation and explainability code
- `policy/fairness/` — per-model configs and schema
- `monitoring/fairness/` — Prometheus alerting rules
- `docs/decisions/ADR-ML-015-fairness-framework.md` — design rationale
