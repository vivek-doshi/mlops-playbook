# Batch Jobs

This directory contains per-model batch inference job configurations.

## File naming convention

```
<model-name>-<environment>-batch-job.yaml
```

Examples:
- `fraud-detection-production-batch-job.yaml`
- `churn-prediction-staging-batch-job.yaml`

## Creating a new job config

1. Copy the schema template:

   ```bash
   cp batch/jobs/_job-schema.yaml batch/jobs/<model-name>-<env>-batch-job.yaml
   ```

2. Fill in every `(REQUIRED)` field.

3. Set correct pod labels for cost attribution (`cost-center`, `team`, `model-name`, `environment`).

4. Commit the config — the config file is the source of truth for CI.

## Running locally

```bash
# Validate input data.
python batch/runner/input_validator.py \
  --job-config batch/jobs/<model-name>-<env>-batch-job.yaml

# Run scoring.
python batch/runner/batch_scorer.py \
  --job-config batch/jobs/<model-name>-<env>-batch-job.yaml

# Check output quality.
python batch/runner/output_quality_gate.py \
  --job-config batch/jobs/<model-name>-<env>-batch-job.yaml \
  --predictions-path <output-path>
```

## Schema reference

See `_job-schema.yaml` for all supported fields with inline documentation.
