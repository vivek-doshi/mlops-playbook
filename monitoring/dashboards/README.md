# Grafana Dashboards

## model-health.json

Grafana dashboard for ML model health monitoring. Provides panels for:

- Dataset drift score (gauge with warning/critical thresholds)
- Number of drifted feature columns
- Prediction request rate over time
- Serving latency p99
- Drift score historical trend

### Import Instructions

1. Open your Grafana instance (usually `http://localhost:3000`).
2. Navigate to **Dashboards → Import** (or click the **+** icon → Import).
3. Click **Upload JSON file** and select `monitoring/dashboards/model-health.json`.
4. Select your **Prometheus** datasource from the dropdown.
5. Click **Import**.

### Using with docker-compose (local development)

If you are running the MLflow stack locally using `mlflow/tracking-server/docker-compose.yml`,
start Grafana separately:

```bash
docker run -d \
  -p 3000:3000 \
  --name grafana \
  -e GF_AUTH_ANONYMOUS_ENABLED=true \
  -e GF_AUTH_ANONYMOUS_ORG_ROLE=Admin \
  grafana/grafana:latest
```

Then add your Prometheus instance as a datasource:

1. Go to **Connections → Data Sources → Add data source**.
2. Select **Prometheus**.
3. Set URL to `http://prometheus:9090` (or your Prometheus address).
4. Click **Save & Test**.
5. Import the dashboard JSON.

### Required Prometheus Metrics

The dashboard queries these metrics. They must be exposed by the serving
runtime or the drift check script (pushed via Pushgateway or scraped directly):

| Metric | Source | Description |
|--------|--------|-------------|
| `ml_dataset_drift_score` | `drift_report.py` | Overall drift score (0–1) |
| `ml_drifted_columns` | `drift_report.py` | Number of drifted feature columns |
| `ml_predictions_total` | Serving runtime | Total prediction count (counter) |
| `ml_inference_duration_seconds` | Serving runtime | Inference latency histogram |

### Alert Rules

See `monitoring/alerts/drift-alerts.yaml` for the Prometheus alert rules that
fire based on the same metrics shown in this dashboard.
