# Golden Path: Self-Service Portal

This guide walks through onboarding to and using the MLOps Self-Service Portal.

## Prerequisites

- Cluster ingress accessible at your organisation's base URL
- GitHub App secrets configured in the `mlops-portal` namespace
- MLflow tracking server reachable from the `mlops-portal` namespace

---

## Step 1 — Open the portal

Navigate to `https://<cluster-host>/mlops-portal` in your browser.

The portal shows all models registered in the MLflow Model Registry.

---

## Step 2 — Inspect a model

Click a model name to view:
- All registered versions
- Current stage (`Staging`, `Production`, `Archived`)
- MLflow run ID per version
- Model tags (PII-filtered — raw tags are never exposed)

---

## Step 3 — Promote a model version

1. Go to **Deploy** in the nav bar
2. Enter model name, version, and target environment
3. Click **Promote →**

The portal dispatches a `workflow_dispatch` event to `promote.yml`.  Check the
**Actions** tab in GitHub for progress.  The portal does not wait for completion.

---

## Step 4 — Review deployment status

The **Models** list shows Kubernetes `ready_replicas / replicas` for each model
deployment across `mlops-dev`, `mlops-staging`, and `mlops-production`.

---

## Step 5 — Manage budgets

1. Go to **Budgets** in the nav bar
2. Review current monthly limits and alert thresholds
3. Edit the corresponding YAML in `finops/budgets/<model-name>.yaml` and commit
   via a PR — the portal does not write budgets directly

---

## Step 6 — Configure notifications

Notification configs live in `monitoring/alerts/<model-name>-notifications.yaml`.
Use the `/api/notifications/{model_name}` endpoint (PUT) to update them via the API,
or edit the YAML files and commit.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Promote returns 500 | GitHub App token expired or misconfigured | Check `GITHUB_APP_PRIVATE_KEY` secret |
| Models list empty | MLflow unreachable | Check `MLFLOW_TRACKING_URI` ConfigMap |
| Deployment shows 0/2 ready | Pod crash — check logs | `kubectl logs -n mlops-portal -l app=mlops-portal` |
