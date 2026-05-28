---
name: Senior MLOps Architect
description: Architecture and lifecycle governance skill for this MLOps playbook repository.
---

## Purpose

Use this skill for MLOps architecture decisions, lifecycle standards, and cross-repo integration with the platform foundation.

## Use This Skill When

- Designing experiment tracking, model registry, and serving topology.
- Choosing defaults for data versioning, model serving, and drift monitoring.
- Defining CI/CD pathways for train, evaluate, approve, and deploy.
- Enforcing governance boundaries between platform and MLOps layers.

## Repository Context To Read First

1. .ai/context/repo-summary.md
2. .ai/context/project_details.md
3. README.md
4. docs/golden-paths/
5. policy/

## MLOps Architecture Rules

- Keep platform provisioning in the platform repository.
- Keep ML lifecycle tooling in this repository.
- Require promotion gates before production model serving.
- Ensure experiment and dataset lineage are reproducible.
- Treat monitoring and drift response as first-class operational flows.

## Expected Outputs

- Recommended architecture path with rationale.
- Exact files to create or modify.
- Governance and risk notes.
- Validation checklist before rollout.
