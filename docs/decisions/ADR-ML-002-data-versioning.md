# ADR-ML-002: DVC for ML Data and Artifact Versioning

**Status:** Accepted  
**Date:** 2024-06-01  
**Authors:** ML Platform Team  
**Reviewers:** @ml-approvers

---

## Context

Machine learning projects require versioning of:

- **Training datasets** — so that runs are reproducible with the exact data used.
- **Model artifacts** — so that specific model versions can be retrieved for rollback.
- **Pipeline stages** — so that only changed stages are re-run, saving compute.

Git alone is unsuitable for large binary files (datasets, model weights) because:
- Git stores the full file history, causing repo bloat.
- Git is not designed for files > 100 MB.
- Cloud storage (S3/GCS/Azure Blob) is not natively versioned in a way that links
  to the code that produced the data.

---

## Decision

We will use **DVC (Data Version Control)** for versioning datasets, pipeline stages,
and model artifacts.

Key practices:

| Concern | DVC approach |
|---------|-------------|
| Large file storage | `.dvc` pointer files tracked in Git; binaries in remote (S3/GCS/Azure Blob) |
| Pipeline definition | `dvc.yaml` in repository root |
| Reproducibility | `dvc repro` re-runs only changed stages |
| Lineage | DVC MD5 hash logged to MLflow as a run tag |
| Multi-cloud | One `.dvc/config` per environment; secrets in GitHub Actions |

Pipeline template: `dvc/pipeline-templates/train-eval-deploy.yaml`  
Remote samples: `dvc/remote-storage/`

---

## Alternatives Considered

### LakeFS
- **Pros:** Git-like branching for data lakes. Excellent for data team collaboration.
- **Cons:** Requires deploying a LakeFS server (or using managed cloud service).
  Adds a new storage layer, increasing operational complexity.
  Overkill for our current dataset scale (<10 TB total).

### Delta Lake
- **Pros:** ACID transactions, time-travel queries, Parquet-native.
- **Cons:** Tightly coupled with Spark ecosystem.
  No native pipeline runner equivalent to `dvc repro`.
  Does not provide artifact versioning for model binaries.

### Plain S3 versioning + object tags
- **Pros:** Zero tooling overhead — just S3 bucket versioning.
- **Cons:** No Git integration, no pipeline definition, no stage-level caching.
  Reproducibility depends entirely on manual bookkeeping.

### Pachyderm
- **Pros:** Kubernetes-native pipeline runner with data versioning.
- **Cons:** Heavy operational footprint, complex cluster setup.
  Steep learning curve. Community edition has limited support.

### Git LFS
- **Pros:** Built into GitHub/GitLab.
- **Cons:** File size limits (GitHub: 2 GB per file, 5 GB total LFS storage free tier).
  No pipeline runner, no stage caching, no multi-cloud remote support.

---

## Why DVC Won

1. **Git-native workflow.** DVC files are checked into Git alongside code.
   `git log` and `git checkout` work for both code *and* data.

2. **Remote storage agnostic.** Supports S3, GCS, Azure Blob, SSH, and local.
   See remote samples in `dvc/remote-storage/`.

3. **Pipeline runner.** `dvc.yaml` defines stages, dependencies, outputs, and metrics.
   `dvc repro` only re-runs stages whose inputs changed.

4. **Minimal infrastructure.** No server required — DVC is a CLI tool.
   Teams start with a shared S3 bucket and a `.dvc/config` file.

5. **MLflow integration.** We log the DVC run hash as an MLflow tag, creating
   end-to-end lineage from dataset version to model registry entry.

---

## Consequences

### Positive
- Reproducible training runs — any run can be re-executed with `dvc checkout` + `dvc repro`.
- Full audit trail of which data produced which model.
- Pipeline caching reduces CI training time significantly after initial run.

### Negative / Trade-offs
- DVC remote storage requires IAM credentials in CI secrets for each cloud.
- Large datasets require DVC cache management (`dvc gc`) to avoid unbounded storage growth.
- Team members must install DVC locally — adds to onboarding steps.

### Operational notes
- Run `dvc gc --cloud --all-branches --all-tags` periodically to clean up orphaned cache.
- See `docs/golden-paths/data-versioning.md` for the daily workflow.
- See `ci/dvc/dvc-pipeline.yml` for the CI DVC pipeline definition.

---

## Related

- `dvc/pipeline-templates/train-eval-deploy.yaml`
- `docs/golden-paths/data-versioning.md`
- ADR-ML-001-experiment-tracking.md
- ADR-ML-003-model-serving.md
