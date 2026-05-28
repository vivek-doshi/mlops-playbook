# Model Monitoring

ML-specific monitoring is separate from platform infrastructure monitoring.

| Concern | Tool | Location |
|---------|------|----------|
| Data drift, prediction drift, feature statistics | Evidently | `monitoring/evidently/` |
| Drift alert rules (Prometheus) | YAML alert rules | `monitoring/alerts/` |
| Model health dashboards (Grafana) | Dashboard JSON | `monitoring/dashboards/` |
| Infrastructure metrics (CPU, GPU, latency) | Platform stack | `devops-playbook/observability/` |

## What to Monitor

1. **Data drift** — the distribution of incoming features shifts from the training distribution.
2. **Prediction drift** — the distribution of model outputs shifts (a leading indicator of accuracy degradation).
3. **Model accuracy** — when labels become available, compute held-out accuracy.
4. **Prediction volume** — sudden drops or spikes in prediction count indicate serving or upstream data issues.

## Architecture

```
Serving pod → prediction log (JSON) → drift_report.py → Prometheus metrics → Grafana dashboard
                                                       ↓
                                                 Evidently HTML report (artifact in MLflow)
                                                       ↓
                                                 Alert on threshold breach → retrain trigger
```

## Quick Start

```bash
# Run a drift report against a reference dataset.
python monitoring/evidently/drift_report.py \
  --reference data/reference/train_features.parquet \
  --current data/current/today_features.parquet \
  --output reports/drift_report.html \
  --threshold 0.3

# Exit code 0 = no drift detected, 1 = drift above threshold (use in CI).
echo "Exit code: $?"
```

## Related

- `docs/golden-paths/model-monitoring.md` — full monitoring golden path
- `monitoring/evidently/drift_report.py` — drift detection script
- `monitoring/alerts/drift-alerts.yaml` — Prometheus alert rules
- `monitoring/dashboards/model-health.json` — Grafana dashboard
