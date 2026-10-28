---
name: Senior DevOps Architect
description: Platform-integration architecture skill for this MLOps playbook repository.
---

## Purpose

Use this skill for MLOps solution architecture, platform-boundary decisions, CI/CD topology, and production guardrail design in this repository.

## Use This Skill When

- Designing MLOps delivery flows across ci/, cd/, terraform/, and serving/.
- Integrating this repository's ML lifecycle workflows with the external devops-playbook platform.
- Defining production-grade defaults and organizational golden paths.
- Planning cross-domain integrations across policy/, monitoring/, and finops/.

## Repository Context To Read First

1. .ai/instructions/engineering-principles.md
2. .ai/context/repo-summary.md
3. .ai/context/architecture-overview.md
4. docs/ARCHITECTURE_DECISION_GUIDE.md
5. docs/golden-paths/

## Architecture Rules

- Prefer clarity and standardization over custom abstractions.
- Route teams through documented golden paths.
- Require security, policy, and cost guardrails in production paths.
- Keep templates cloud-targeted but convention-aligned.
- Favor reusable modules, shared workflows, and explicit runtime constraints.

## Expected Outputs

- A recommended architecture path with rationale.
- Exact file targets to copy/edit.
- Risk notes and guardrail checks.
- Validation checklist before merge or deployment.
