# ADR-ML-005: GitHub Actions as the CI/CD Platform for ML Pipelines

**Status:** Accepted
**Date:** 2024-09-15
**Authors:** ML Platform Team
**Reviewers:** @ml-approvers

---

## Context

The ML lifecycle requires automated pipelines for training, evaluation, model promotion, deployment, and drift monitoring. These pipelines must:

- Trigger on code commits, schedule (cron), and external events (retraining dispatch).
- Provide environment isolation per job (Python version, dependencies).
- Support manual approval gates before production deployment.
- Produce auditable logs that satisfy model governance requirements (traceability of who approved what and when).
- Reuse security-sensitive steps (secret scanning, dependency audit) across multiple workflows without duplication.
- Be cost-efficient — training jobs are infrequent and bursty; pay-per-minute billing is preferred over always-on infrastructure.

The platform repository (`devops-playbook`) already standardises on GitHub Actions for application CI/CD. Adopting a different CI platform for ML would fragment tooling knowledge and double the number of CI systems teams need to learn.

---

## Decision

We will use **GitHub Actions** as the CI/CD platform for all ML pipelines in this repository.

Workflow layout:

| Workflow | File | Trigger |
|---------|------|---------|
| Model training | `ci/github-actions/model-training/train.yml` | `push main`, `workflow_dispatch` |
| Model evaluation | `ci/github-actions/model-evaluation/evaluate.yml` | Called by training workflow |
| Model deployment | `ci/github-actions/model-deployment/deploy.yml` | Manual, after evaluation passes |
| Drift monitoring | `ci/github-actions/model-monitoring/drift-check.yml` | Cron `0 6 * * *` |
| Security scan | `ci/github-actions/_shared/reusable-mlops-scan.yml` | Reusable (`workflow_call`) |

Key GitHub Actions patterns adopted:

| Pattern | Rationale |
|---------|-----------|
| `environment: production` gate | GitHub-native manual approval — audited with actor + timestamp |
| `workflow_call` reusable workflow | Shared security scan without duplication across pipelines |
| `workflow_dispatch` inputs | On-demand training with parameterised `dvc_remote` and `environment` |
| OIDC federation (via platform) | Short-lived cloud credentials — no long-lived secrets in GitHub |
| Job outputs (`run_id`, `data_hash`) | Pass MLflow run ID between training → evaluation → deployment jobs |

---

## Alternatives Considered

### Kubeflow Pipelines (KFP)
- **Pros:** Purpose-built for ML; native DAG orchestration; Kubernetes-native; component caching.
- **Cons:** Requires a Kubeflow cluster (significant platform investment). Steep learning curve for the Python DSL. Poor native support for GitHub review/approval workflows. Overkill at current pipeline count.

### Airflow / Astronomer
- **Pros:** Mature scheduler; rich operator library; strong community.
- **Cons:** Heavyweight deployment (PostgreSQL + Redis + worker pool). DAG authoring in Python adds cognitive overhead for engineers who want a simple YAML trigger. No native GitHub PR review integration.

### Jenkins
- **Pros:** Maximum flexibility; Groovy DSL.
- **Cons:** Team has no existing Jenkins expertise. Requires self-hosted infrastructure. Significantly inferior developer experience compared to GitHub Actions for GitHub-native repos.

### AWS CodePipeline / Azure DevOps
- **Cons:** Cloud-vendor lock-in. GitHub is the source-of-truth for code and reviews — spanning pipeline tooling across platforms adds friction without benefit at current scale.

---

## Consequences

**Positive:**
- Single platform for CI/CD knowledge across platform and ML teams.
- GitHub-native approval gates satisfy governance requirements with a complete audit log.
- Reusable workflows reduce duplication and enforce security standards centrally.

**Negative:**
- GitHub Actions runners are ephemeral and stateless — training jobs must restore DVC cache on every run (adds 2–5 min). Mitigated with `actions/cache` on `~/.dvc/cache`.
- Self-hosted GPU runners are needed for GPU-accelerated training at scale. The current default uses CPU-only hosted runners; GPU training is done by calling cloud training APIs (SageMaker, Vertex AI) rather than running on the runner directly.

**Neutral:**
- CI costs are usage-based. Long training runs on hosted runners are expensive — use `workflow_dispatch` with `environment: dev` for exploratory runs and reserve `environment: production` for promoted candidates.

---

## Review Triggers

Re-evaluate if:
- Training pipeline count exceeds 15 — dedicated orchestration (Prefect, Dagster) may improve observability.
- The team adopts Kubernetes-native serving at scale — Argo Workflows integration with serving rollouts may be preferred.
