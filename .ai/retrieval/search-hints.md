# Search Hints

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-08-31
**Source of Truth**: docs/golden-paths/
**Depends On**: docs/guides/, docs/decisions/
---

Practical search terms and patterns to accelerate accurate retrieval.

## High-Value Keywords By Domain

- CI: model-training, model-evaluation, model-deployment, promotion, drift-check
- Delivery: kustomize, argo, rollout, triton, torchserve, vllm
- Terraform: provider, module, backend, state, plan, apply
- Governance: model-approval, data-governance, pii, fairness, gitleaks, pip-audit
- FinOps: budget, rightsizing, cost-center, model-name, gpu
- Monitoring: evidently, drift, prometheus, grafana, slo, alert

## Path-Focused Search Patterns

- ci/github-actions/**
- cd/kubernetes/**
- cd/argo/**
- terraform/**/main.tf
- policy/**
- monitoring/**
- finops/**

## Query Refinement Tips

- Add cloud target: aws, azure, gcp.
- Add runtime stack: triton, torchserve, vllm, ray, kubeflow, argo.
- Add lifecycle phase: experiment, version, train, evaluate, promote, serve, monitor.

## Disambiguation

If results are broad, narrow by:

1. platform
2. workload type
3. environment (dev/staging/prod)
4. enforcement needs (security/cost/policy)
