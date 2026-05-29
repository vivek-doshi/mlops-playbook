# ADR-ML-014: Multi-Environment Promotion Strategy

**Status:** Accepted  
**Date:** 2026-05-29  
**Authors:** ML Platform Team  
**Reviewers:** @ml-approvers

---

## Context

As ML models move from experimentation to production, the organisation needs
structural guarantees that:

1. Development workloads cannot accidentally affect production traffic.
2. Every model version passes a progressively stronger quality gate before
   reaching higher environments.
3. Production promotions have a human approval record with an audit trail.
4. Environment configurations are not duplicated — changes apply consistently.
5. Resource consumption per environment is bounded to prevent runaway spend.

The existing single-environment deploy workflow (`ci/github-actions/model-deployment/deploy.yml`)
conflates all environments into one job with manual namespace parameters.
It has no structural isolation and no staged gate progression.

---

## Decision

We will implement **three structurally isolated environments** using Kubernetes
namespaces and Kustomize overlays, with a one-directional promotion pipeline and
environment-specific quality gates.

### Namespace isolation model

Each model gets its own namespace per environment:

| Environment | Namespace pattern | MLflow experiment |
|---|---|---|
| dev | `<model>-dev` | `<model>-dev` |
| staging | `<model>-staging` | `<model>-staging` |
| production | `<model>-prod` | `<model>-production` |

Using model-scoped namespaces (instead of shared `dev`/`staging`/`prod`) prevents
one model's resource usage from starving another at the same tier.

### Kustomize overlay strategy

We use **Kustomize base + overlay** over Helm for environment differentiation:

- `cd/kubernetes/_base/` — shared base manifests (Deployment, Service)
- `cd/kubernetes/environments/<env>/` — per-environment overlays with patches

Rationale for Kustomize over Helm:
- No templating language to learn; plain YAML with patches.
- Overlays are structurally minimal — only the differences from base are expressed.
- Compatible with GitOps tools (ArgoCD, Flux) without chart management overhead.
- Environment configs are reviewed as code diffs, not Helm value explosions.

### Gate progression

| Gate | dev | staging | production |
|---|---|---|---|
| Smoke test | ✅ | ✅ | ✅ |
| Unit metrics | ✅ | ✅ | ✅ |
| Schema check | ✅ | ✅ | ✅ |
| Drift check | optional | ✅ | ✅ |
| Load test | ❌ | ✅ | ✅ |
| Integration test | ❌ | ✅ | ✅ |
| Fairness gate | optional | ✅ | ✅ |
| Compliance check | ❌ | ❌ | ✅ |
| SLO baseline | ❌ | ❌ | ✅ |
| Lineage complete | ❌ | ❌ | ✅ |

### Approval requirements

| Environment | Approval | Mechanism |
|---|---|---|
| dev | None | Auto-deploy on merge to `main` |
| staging | None | Auto-promote after dev gates pass |
| production | 2 × @ml-approvers | GitHub Environment protection rule |

Production also requires a 10-minute wait timer (blast-radius window) configured
on the `production` GitHub Environment.

---

## Alternatives Considered

### Option A: Helm charts with per-environment values files

**Pros:** Helm is widely known; rich ecosystem of charts.  
**Cons:** Helm's templating logic (`{{ if eq .Values.env "production" }}`) creates
conditional branches that are hard to review and test. Value file naming conventions
vary across teams. Upgrading chart versions requires careful impact analysis across
all environments.  
**Decision:** Rejected — Kustomize patches are clearer for this use case.

### Option B: Shared `dev`/`staging`/`prod` namespaces across all models

**Pros:** Simpler namespace management.  
**Cons:** Resource contention between models. One noisy model can starve others.
Cross-model blast radius for security incidents.  
**Decision:** Rejected — per-model namespaces provide the required isolation.

### Option C: Branch-based environments (feature branches → dev, main → staging, tags → production)

**Pros:** Familiar git-flow pattern.  
**Cons:** Forces a git branching strategy that conflicts with trunk-based development.
Model versions are not always aligned with git branches. Makes rollback harder.  
**Decision:** Rejected — version-based promotion (by MLflow model version) is more
flexible and matches how model registry stages already work.

### Option D: Keep single workflow, add environment parameter

**Pros:** Minimal change.  
**Cons:** No structural isolation. Human error can target the wrong environment.
No staged gate progression. Impossible to enforce approval requirements per stage.  
**Decision:** Rejected — does not meet the isolation requirements for Phase 2.

---

## Consequences

### Positive

- Clear audit trail: every promotion creates a record in `policy/model-approval/approved-versions.yaml`.
- Resource isolation: dev load tests cannot impact staging memory quotas.
- Reviewable gates: all gate logic is in `promotion-gates.yml`, reviewed as code.
- Rollback is systematic: `rollback.yml` handles the Kubernetes + MLflow state consistently.

### Negative / Trade-offs

- Additional operational overhead: 3× the namespaces per model.
- Platform team must provision per-model namespaces and KUBECONFIG secrets.
- First-time promotion for a new model requires platform team to create the namespace
  and add the KUBECONFIG secret to GitHub Actions.

### Mitigation

Platform team maintains a namespace bootstrap script in `scripts/bootstrap-namespace.sh`
(to be created alongside platform infra work) that creates the namespace, applies the
ResourceQuota, and registers the kubeconfig secret in one command.

---

## Review Triggers

This ADR should be revisited if:

- The number of models exceeds 50 (namespace sprawl may need a different isolation model).
- We adopt a GitOps controller (ArgoCD/Flux) — the promotion trigger mechanism changes.
- Helm is standardised org-wide — reconsider Kustomize vs Helm trade-offs.
- The 2-approver production gate causes deployment bottlenecks — consider async approval.
