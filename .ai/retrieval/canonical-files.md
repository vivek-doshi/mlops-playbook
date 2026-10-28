# Canonical Files

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-10-28
**Source of Truth**: docs/golden-paths/
**Depends On**: docs/guides/, docs/decisions/
---

Primary files and directories that should be consulted first for most tasks.

## Repository-Level Canonical Files

- README.md: Primary repository purpose, capabilities, and quick links.
- GETTING_STARTED.md: Fast path from need to file.
- docs/golden-paths/mlops-workflow.md: Canonical end-to-end lifecycle guide.
- docs/golden-paths/: End-to-end preferred workflows.

## Domain Canonical Files

- CI/CD: ci/github-actions/ and ci/github-actions/_shared/
- Infrastructure: terraform/<cloud-target>/
- Kubernetes and runtime delivery: cd/kubernetes/, cd/argo/, and serving/
- Security and policy: policy/ and ci/github-actions/_shared/reusable-mlops-scan.yml
- Cost governance: finops/
- Monitoring: monitoring/
- Advanced lifecycle patterns: online_learning/, federated_learning/, multi_cloud_serving/, model_optimization/, llmops/, and portal/
- Repository browser: website/src/components/Sidebar.tsx and website/scripts/generate-index.js
- Production readiness: docs/production-readiness.md, docs/maturity-roadmap.md, and docs/lineage-and-observability-contract.md
- Release governance: policy/model-approval/gates.yaml and policy/model-inventory.yaml

## Canonical Operational Documentation

- docs/guides/ and docs/topology/: Supporting concepts, platform boundaries, and integration contracts.

## Canonical Selection Rules

- Prefer README and top-level decision guides before deep file reads.
- Prefer golden paths for implementation tasks.
- Prefer target-specific folders only after domain and architecture are identified.
- Prefer reusable shared templates before stack-specific one-off templates.
