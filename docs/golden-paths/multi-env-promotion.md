# Multi-Environment Promotion Golden Path

## Purpose and Scope

This golden path describes the canonical way to promote a trained model through
**dev → staging → production** in the MLOps playbook. Following this path ensures
structural environment isolation, auditable promotion records, and consistent
quality gates at every stage.

> **Beginner tip**: Think of environments like branches in a deployment pipeline.
> Each one is a separate Kubernetes namespace with its own resource limits, its own
> MLflow experiment, and its own approval requirements. A model can only move
> forward (dev → staging → prod) — never backwards.

---

## Prerequisites

| Requirement | Location |
|---|---|
| Model registered in MLflow | `docs/golden-paths/model-registry.md` |
| DVC data lineage pointer | `docs/golden-paths/data-versioning.md` |
| Kubernetes cluster configured | Platform team (devops-playbook) |
| Namespace naming convention understood | This document |

---

## Environment Overview

| Environment | Namespace | MLflow Experiment | Approval | Resource Limits |
|---|---|---|---|---|
| dev | `<model>-dev` | `<model>-dev` | None (auto) | 2 CPU, 8Gi, 1 GPU |
| staging | `<model>-staging` | `<model>-staging` | None (auto after dev gates) | 4 CPU, 16Gi, 2 GPU |
| production | `<model>-prod` | `<model>-production` | 2 × @ml-approvers + 10 min delay | VPA-governed |

---

## Promotion Flow

```
Merge PR to main
      ↓
[promote-dev.yml]
  ├── Gate 1: Smoke test
  ├── Gate 2: Unit metrics
  ├── Gate 3: Schema check
  └── Deploy to <model>-dev namespace (auto)
      ↓
[promote-staging.yml] (triggered automatically after dev succeeds)
  ├── Gate 1–3: Same as dev
  ├── Gate 4: Drift check
  ├── Gate 5: Load test
  └── Deploy to <model>-staging namespace (auto)
      ↓
[promote-production.yml] (manual workflow_dispatch only)
  ├── Pre-flight: Model must be in Staging stage
  ├── Gate 1–5: Full gate suite
  ├── Gate 6: Compliance check
  ├── Gate 7: SLO baseline verify
  ├── AWAIT 2 approvals from @ml-approvers
  ├── WAIT 10 minutes (blast radius window)
  └── Deploy to <model>-prod namespace
```

---

## Step-by-Step: Promoting to Dev

Dev promotion is **automatic**. Every merge to `main` triggers `promote-dev.yml`.
No action required.

To trigger manually:

```bash
gh workflow run promote-dev.yml \
  --field model_name=my-model \
  --field model_version=3 \
  --field image_tag=my-model:v3-dev
```

---

## Step-by-Step: Promoting to Staging

Staging promotion is **automatic** after dev succeeds.

To trigger manually:

```bash
gh workflow run promote-staging.yml \
  --field model_name=my-model \
  --field model_version=3 \
  --field image_tag=my-model:v3-staging
```

---

## Step-by-Step: Promoting to Production

Production promotion requires explicit intent and 2 human approvals.

### 1. Write a rollback plan

Before running the workflow, document your rollback plan:

```
If this deployment fails, I will run rollback.yml targeting version 2
(the previous production version), then investigate the failure with
the post-mortem template in docs/runbooks/incident-response.md.
```

### 2. Trigger the promotion workflow

```bash
gh workflow run promote-production.yml \
  --field model_name=my-model \
  --field model_version=3 \
  --field image_tag=my-model:v3-production \
  --field rollback_plan="Roll back to v2 via rollback.yml if P99 latency > 1s"
```

### 3. Approve in GitHub Actions UI

Two members of `@ml-approvers` must click **Approve** in:
`Actions → promote-production → <run> → Review deployments`

### 4. 10-minute delay runs

After both approvals, GitHub waits 10 minutes before the deploy job starts.
This is the blast-radius window — use it to confirm no ongoing incidents.

### 5. Deployment executes

Kustomize applies the production overlay, Kubernetes rolls out the new version,
and the model is transitioned to Production stage in MLflow.

---

## Rollback

If a production deployment fails or causes a SLO breach:

```bash
gh workflow run rollback.yml \
  --field model_name=my-model \
  --field rollback_version=previous \
  --field environment=production \
  --field reason="P99 latency exceeded 1s SLO — rolling back to v2"
```

The rollback:
1. Demotes the current Production version → Staging in MLflow.
2. Promotes the rollback target → Production in MLflow.
3. Re-applies the Kubernetes overlay with the rollback image.
4. Records the rollback in `policy/model-approval/approved-versions.yaml`.
5. Opens a PR with the audit record and `rollback` + `incident` labels.

---

## Environment Isolation Rules

- Each environment uses its own Kubernetes **namespace** — never share across models.
- Each environment uses its own MLflow **experiment** — never log staging runs to a
  dev experiment.
- Each environment uses its own **DVC remote prefix** (configured in `.dvc/config`).
- Promotion is **one-directional**: dev → staging → production only.
- A model that has never been in Staging **cannot** be promoted to Production.

---

## Namespace Resource Quotas

Resource quotas are enforced by Kubernetes `ResourceQuota` and `LimitRange` objects
applied per namespace. See `cd/kubernetes/environments/<env>/resource-quota.yaml`.

If a workload exceeds the namespace quota, it will be rejected by the Kubernetes API
server. Adjust the quota via a PR to `resource-quota.yaml` and request platform review.

---

## Cost Attribution

Every pod deployed by these workflows must carry the required labels:
`cost-center`, `team`, `model-name`, `environment`.

These labels are set in the Kustomize base and overlays. If a pod is missing any
label, the Kyverno policy in the platform repo will reject it.

See `docs/golden-paths/ml-cost-attribution.md` for the full cost tracking guide.

---

## Further Reading

- `policy/environments/` — per-environment policy files
- `cd/kubernetes/environments/` — Kustomize overlays
- `ci/github-actions/promotion/` — workflow files
- `policy/model-approval/` — approval registry
- ADR-ML-014: Multi-Environment Strategy (docs/decisions/)
