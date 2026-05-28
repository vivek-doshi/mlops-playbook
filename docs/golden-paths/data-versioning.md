# Data Versioning Golden Path

## Purpose and Scope

Version datasets and pipeline artifacts so that any training run can be exactly
reproduced from a committed DVC pointer file. This guide covers DVC as the default
data versioning tool, as decided in `docs/decisions/ADR-ML-002-data-versioning.md`.

Scope: raw datasets, processed features, model artifacts, and pipeline outputs.

> **Beginner tip**: DVC (Data Version Control) works alongside Git. Git tracks your
> code; DVC tracks your large data files. DVC stores a small "pointer" file (`.dvc`)
> in Git that describes where the real data lives (S3, GCS, Azure Blob, etc.).
> When a teammate clones your repo and runs `dvc pull`, they get the exact same
> dataset you used — even if you trained the model months ago.

---

## Prerequisites

| Requirement | Where to configure |
|-------------|-------------------|
| DVC installed | `pip install "dvc[all]"` |
| One remote configured | `dvc/remote-storage/` (S3, GCS, or Azure) |
| Git repository initialised | `git init` (already done in this repo) |
| Cloud credentials available | See **Credential Setup** section below |

---

## Step-by-Step Implementation

### Step 1 — Initialise DVC in the repository

> Skip this step if DVC is already initialised (`.dvc/` folder already exists).

```bash
# dvc init creates the .dvc/ folder and a .dvcignore file.
# The .dvc/ folder is committed to Git — it contains DVC configuration.
dvc init

# Stage the new DVC files for Git.
git add .dvc .dvcignore

git commit -m "feat: initialise DVC"
```

---

### Step 2 — Add a remote storage backend

Choose the remote that matches your cloud. Samples are in `dvc/remote-storage/`.

```bash
# -----------------------------------------------------------------------
# S3 remote — replace the bucket name with your own.
# -----------------------------------------------------------------------
dvc remote add origin s3://my-mlops-dvc-bucket
dvc remote default origin

# -----------------------------------------------------------------------
# GCS remote
# -----------------------------------------------------------------------
# dvc remote add origin gs://my-mlops-dvc-bucket
# dvc remote default origin

# -----------------------------------------------------------------------
# Azure Blob Storage remote
# -----------------------------------------------------------------------
# dvc remote add origin azure://my-container
# dvc remote modify origin account_name MY_STORAGE_ACCOUNT
# dvc remote default origin
```

Save the remote config to Git:

```bash
git add .dvc/config
git commit -m "feat: add DVC remote for S3"
```

---

### Step 3 — Track a dataset

```bash
# -----------------------------------------------------------------------
# dvc add does two things:
#   1. Computes an MD5 hash of the file.
#   2. Creates a .dvc pointer file that records the hash and the path.
# The original file is added to .gitignore so Git does not track it.
# -----------------------------------------------------------------------
dvc add data/raw/dataset.csv

# Commit the pointer file and the updated .gitignore to Git.
# The actual CSV is NOT committed — only the tiny pointer.
git add data/raw/dataset.csv.dvc .gitignore
git commit -m "feat: track raw dataset v1"

# Upload the real file to your remote storage.
dvc push
```

---

### Step 4 — Use the DVC pipeline template

```bash
# Copy the pipeline template to the repo root as dvc.yaml.
# This file defines the stages of your ML pipeline (ingest, train, evaluate).
cp dvc/pipeline-templates/train-eval-deploy.yaml dvc.yaml

# Edit dvc.yaml to match your project's scripts and data paths.
# Then run the pipeline — DVC will only re-run stages whose inputs changed.
dvc repro
```

> **Beginner tip**: `dvc repro` is like `make` for data pipelines. It runs only the
> stages that are out of date. If the raw data has not changed, DVC skips the ingest
> stage and only re-runs training. This saves significant compute time.

---

### Step 5 — Pull data in CI

Reference `ci/github-actions/model-training/train.yml` for the full workflow.

The key step is:

```yaml
- name: Pull data
  env:
    # Cloud credentials must be stored as GitHub Actions secrets.
    # Never hardcode credentials in the workflow file.
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: dvc pull --remote "${{ github.event.inputs.dvc_remote }}"
```

---

## Credential Setup Per Cloud

### AWS S3

```bash
# Option 1: environment variables (simplest for CI)
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Option 2: OIDC federation (recommended for GitHub Actions — no stored secrets)
# Reference: cicd-reference/ci/github-actions/_shared/
```

### Google Cloud Storage

```bash
# Point to a service account key file.
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json

# Or use Workload Identity Federation (recommended):
# Reference: cicd-reference/ci/github-actions/_shared/
```

### Azure Blob Storage

```bash
# Option 1: storage account key
export AZURE_STORAGE_ACCOUNT=my-account
export AZURE_STORAGE_KEY=my-key

# Option 2: Managed Identity (recommended for Azure-hosted runners)
```

---

## Validation

```bash
# After dvc push, this should show "Data and pipelines are up to date."
dvc status

# On a clean clone, pull all data and re-run the pipeline.
# The output metrics hash should be identical to the original run.
git clone <repo-url> /tmp/test-clone
cd /tmp/test-clone
dvc pull
dvc repro
```

---

## Rollback / Failure Handling

| Situation | Action |
|-----------|--------|
| Wrong dataset version pushed | `git checkout <old-commit> -- data/raw/dataset.csv.dvc && dvc checkout` |
| Remote unreachable | Check cloud credentials and bucket permissions. Use `dvc status --cloud` to diagnose. |
| Partial push (interrupted) | Re-run `dvc push` — DVC is idempotent and skips already-uploaded files. |
| Pipeline stage failed | Fix the script, then `dvc repro` again. DVC will re-run only from the failed stage. |

---

## Related

- `dvc/remote-storage/README.md` — remote storage samples
- `dvc/pipeline-templates/train-eval-deploy.yaml` — pipeline definition
- `ci/github-actions/model-training/train.yml` — CI integration
- `docs/decisions/ADR-ML-002-data-versioning.md` — why DVC
- `docs/golden-paths/experiment-tracking.md` — linking data hash to MLflow runs
