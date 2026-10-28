# Entrypoints

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-10-28
**Source of Truth**: docs/golden-paths/
**Depends On**: docs/guides/, docs/decisions/
---

Recommended first files to open by intent.

## Global Entrypoints

- README.md
- GETTING_STARTED.md
- docs/golden-paths/mlops-workflow.md
- docs/golden-paths/

## By Task Type

- ML lifecycle delivery:
  - docs/golden-paths/mlops-workflow.md
  - docs/golden-paths/model-training-pipeline.md
  - docs/golden-paths/model-serving.md
  - docs/ARCHITECTURE_DECISION_GUIDE.md
  - docs/production-readiness.md
  - docs/lineage-and-observability-contract.md
  - docs/disaster-recovery.md
- Pipeline setup:
  - ci/github-actions/
  - pipelines/
  - cd/argo/pipelines/
- Cloud deployment:
  - terraform/
  - cd/kubernetes/environments/
- Kubernetes patterns:
  - cd/kubernetes/_base/
  - cd/kubernetes/training/
  - cd/kubernetes/batch/
  - cd/kubernetes/README.md
- Security baseline:
  - policy/README.md
  - ci/github-actions/_shared/reusable-mlops-scan.yml
- FinOps baseline:
  - finops/README.md
  - monitoring/dashboards/model-health.json
- Advanced MLOps workflows:
  - online_learning/README.md
  - federated_learning/README.md
  - multi_cloud_serving/README.md
  - model_optimization/README.md
  - llmops/README.md
  - portal/README.md
- Production readiness and audit evidence:
  - docs/production-readiness.md
  - docs/maturity-roadmap.md
  - docs/disaster-recovery.md

## Triage Entrypoint Order

1. matching docs/golden-paths/*
2. domain README
3. implementation template files
