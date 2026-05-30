# Session: MLOps Concepts Guide Creation

**Date:** 2026-05-30  
**Type:** Documentation creation (new guide)

## Objective
Create `docs/guides/concepts.md` to explain all core MLOps concepts used in this repository, starting with MLOps introduction and lifecycle steps, then detailing repository-specific concepts with examples.

## Deliverable
- Added new guide: `docs/guides/concepts.md`

## Content Summary
- Introduced MLOps definition and closed-loop lifecycle.
- Documented lifecycle steps:
  1. problem definition and success metrics
  2. data versioning and lineage
  3. training and experiment tracking
  4. evaluation/governance/approval gates
  5. serving and runtime selection
  6. monitoring/drift/SLOs
  7. retraining and continuous improvement
- Added repository-aligned concept sections for:
  - CI/CD for ML
  - batch inference
  - pipeline orchestration
  - fairness and explainability
  - feature store patterns
  - FinOps for ML
  - distributed training
  - multi-cloud portability
- Included concrete examples with repository file references throughout.

## Link Validation for Website
- Validated all markdown links in `docs/guides/concepts.md` against existing repo paths.
- Corrected one path mismatch:
  - from `monitoring/dashboards/ml-cost-attribution.json`
  - to `finops/dashboards/ml-cost-attribution.json`
- Final status: all internal links resolve.

## Repo Intelligence Updates
- Updated `.ai/context/repo-summary.md` to include concepts guide capability.
- Updated `.ai/retrieval/workflow-to-files.yaml` to include `docs/guides/concepts.md` in frontend/docs entrypoints.
