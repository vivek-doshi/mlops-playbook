# Architecture Decision Records

All ML lifecycle ADRs for the MLOps Playbook. ADRs are numbered ML-NNN and
record the context, decision, alternatives considered, consequences, and review
triggers for each architectural choice.

## Index

| ADR | Title | Status |
|---|---|---|
| [ADR-ML-001](ADR-ML-001-experiment-tracking.md) | MLflow as Experiment Tracking | Accepted |
| [ADR-ML-002](ADR-ML-002-data-versioning.md) | DVC for Data Versioning | Accepted |
| [ADR-ML-003](ADR-ML-003-model-serving.md) | Three-Runtime Serving Strategy | Accepted |
| [ADR-ML-004](ADR-ML-004-drift-monitoring.md) | Evidently AI for Drift Monitoring | Accepted |
| [ADR-ML-005](ADR-ML-005-ci-cd-platform.md) | GitHub Actions as CI/CD Platform | Accepted |
| [ADR-ML-006](ADR-ML-006-infrastructure-terraform.md) | Terraform for Infrastructure | Accepted |
| [ADR-ML-007](ADR-ML-007-dev-container.md) | Dev Containers for Local Development | Accepted |
| [ADR-ML-008](ADR-ML-008-model-approval-policy.md) | Three-Gate Model Approval Policy | Accepted |
| [ADR-ML-009](ADR-ML-009-pre-commit-toolchain.md) | Pre-commit Toolchain | Accepted |
| [ADR-ML-014](ADR-ML-014-multi-env-strategy.md) | Multi-Environment Promotion Strategy | Accepted |
| [ADR-ML-015](ADR-ML-015-fairness-framework.md) | Fairness & Explainability Framework | Accepted |
| [ADR-ML-016](ADR-ML-016-distributed-training.md) | Distributed Training Framework | Accepted |
| [ADR-ML-017](ADR-ML-017-pipeline-orchestration.md) | Pipeline Orchestration | Accepted |
| [ADR-ML-018](ADR-ML-018-batch-inference.md) | Batch Inference Architecture | Accepted |

## Numbering Gaps

ADR-ML-010 through ADR-ML-013 are reserved for Phase 1 items:

| Number | Reserved for |
|---|---|
| ADR-ML-010 | Continuous Training architecture |
| ADR-ML-011 | Feature store tool choice |
| ADR-ML-012 | Shadow deployment routing strategy |
| ADR-ML-013 | ML Metadata Store schema |

## Format

Use `ADR-ML-002-data-versioning.md` as the format template.
Required sections: Context, Decision, Alternatives Considered, Consequences, Review Triggers.

## New ADR Numbers

Phase 3 ADRs start at ADR-ML-019.
