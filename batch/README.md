# Batch Inference Module

Offline/batch model scoring against large datasets using Kubernetes Jobs and CronJobs.

## Directory layout

```
batch/
├── runner/
│   ├── batch_scorer.py          # Core scoring engine
│   ├── input_validator.py       # Pre-score input validation
│   ├── output_quality_gate.py   # Post-score output quality checks
│   └── downstream_notifier.py   # Slack / HTTP / Event Grid notifications
├── jobs/
│   ├── _job-schema.yaml         # Job config schema + template
│   └── README.md                # How to create job configs
└── README.md                    # This file
```

## Quick start

### 1. Create a job config

```bash
cp batch/jobs/_job-schema.yaml batch/jobs/<model>-production-batch-job.yaml
# Edit the file — fill in all (REQUIRED) fields
```

### 2. Submit via GitHub Actions

```bash
gh workflow run trigger-batch-job \
  --field model_name=fraud-detection \
  --field environment=production \
  --field job_config=batch/jobs/fraud-detection-production-batch-job.yaml
```

### 3. Monitor

```bash
kubectl get jobs -n <model-name>-production
kubectl logs -n <model-name>-production -l batch.kubernetes.io/job-name=<job-name> -f
```

## Scheduling (CronJob)

See `cd/kubernetes/batch/batch-cronjob.yaml` and the `scheduled-batch.yml` CI workflow.
Set `BATCH_SCHEDULE` in the workflow to a cron expression (e.g., `0 2 * * *` for 2 AM daily).

## Architecture

```
Input data  ──►  input_validator  ──►  batch_scorer  ──►  output_quality_gate  ──►  downstream_notifier
(S3/GCS/ABS)     (fail-fast)           (MLflow model)     (fail-fast)               (Slack/HTTP/EventGrid)
```

## Cost attribution

All batch pods must have the four required labels:

| Label | Example |
|---|---|
| `cost-center` | `cc-1234` |
| `team` | `ml-platform` |
| `model-name` | `fraud-detection` |
| `environment` | `production` |

These are set in the job config `labels:` section and applied to the Kubernetes Job pod template.

## Further reading

- `docs/golden-paths/batch-inference.md` — step-by-step guide
- `docs/decisions/ADR-ML-018-batch-inference.md` — framework selection ADR
- `cd/kubernetes/batch/` — Kubernetes Job / CronJob manifests
- `ci/github-actions/batch/` — CI workflows
