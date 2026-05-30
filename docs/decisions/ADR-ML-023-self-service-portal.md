# ADR-ML-023: Self-Service Portal Architecture

**Status:** Accepted  
**Date:** 2026-05-30  
**Deciders:** Platform Engineering, MLOps Leads  

---

## Context

ML engineers and data scientists need a unified UI to monitor model health, trigger
promotions, review budgets, and configure notifications — without requiring direct
access to MLflow, Kubernetes, or GitHub.  A portal reduces the operational burden
and enforces policy by funnelling all mutations through CI/CD.

---

## Decision

### Architecture: React SPA + FastAPI backend

A single-page React TypeScript application communicates with a FastAPI backend.
The backend is deployed as a Kubernetes `Deployment` in the `mlops-portal` namespace
and is accessible via `/mlops-portal` on the cluster ingress.

### Read-and-trigger principle

The portal is **read-only for all data stores**.  It never calls:
- `MlflowClient` mutation methods (no `register_model`, no stage transitions)
- Kubernetes write APIs (no `patch_namespaced_deployment`)

All mutations are dispatched as GitHub Actions `workflow_dispatch` events.

### GitHub App, not PAT

The backend uses a **GitHub App installation token** for workflow dispatch.
Rationale:
- Installation tokens are short-lived (1 hour) — no long-lived credential rotation risk
- PATs are tied to individual user accounts — a leaving employee would break the portal
- GitHub Apps have fine-grained permission scopes (Actions: write only)

### Single deployment namespace

The portal runs in the `mlops-portal` namespace with a `NetworkPolicy` that permits:
- Egress to GitHub API (port 443)
- Egress to the MLflow tracking server (port 5000, in-cluster)
- Egress to the Kubernetes API server (port 443)
- Ingress only from the ingress-nginx namespace

### Cost labels

All pod specs carry the four cost labels required by Phase 3 FinOps rules:
`cost-center`, `team`, `model-name: portal`, `environment`.

---

## Consequences

**Positive:**
- No direct cluster or registry access required by portal users
- All mutations are auditable via GitHub Actions logs
- GitHub App token rotation is centralised

**Negative:**
- Workflow dispatch is asynchronous — the portal shows "dispatched" not "complete"
- An extra round-trip (portal → GitHub → runner → MLflow/k8s) adds latency for promotions

---

## Alternatives considered

| Option | Reason rejected |
|---|---|
| Direct MLflow SDK calls for mutations | Bypasses CI/CD audit trail |
| PAT-based workflow dispatch | Long-lived credential, user-tied |
| Full-stack monolith (no SPA) | Harder to iterate on UI; no separation of concerns |
