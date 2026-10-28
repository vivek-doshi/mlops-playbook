# MLOps Playbook Project Brief

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-10-27
**Source of Truth**: README.md
**Depends On**: .ai/context/repo-summary.md, docs/topology/
---

This repository is the ML lifecycle layer for teams using the separate `devops-playbook` platform foundation. It provides opinionated golden paths, reusable implementation patterns, and operational guardrails; it is not a general-purpose platform provisioning repository.

## Responsibility Boundary

- `devops-playbook` provides shared platform capabilities such as cluster provisioning, identity, secrets, and baseline observability.
- This repository provides ML lifecycle workflows, including training, experiment tracking, data and model lineage, evaluation, promotion, serving, and monitoring.
- Cross-repository requirements are documented in `docs/topology/`. Use `.ai/context/repo-summary.md` for the maintained capability inventory.

## Intended Audience

- ML platform engineers defining reusable lifecycle standards.
- Applied ML teams building reproducible training and deployment workflows.
- DevOps and SRE teams integrating ML services with platform controls.
- Governance teams responsible for model approval and data policies.

## Navigation

1. Start with `README.md` and `GETTING_STARTED.md`.
2. Choose the relevant workflow in `docs/golden-paths/`.
3. Use domain READMEs and templates for implementation details.
4. Consult `docs/topology/` when a workflow crosses the platform boundary.
