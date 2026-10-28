# Retrieval Context

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-10-27
**Source of Truth**: .ai/retrieval/
**Depends On**: .ai/context/, .ai/instructions/
---

Place retrieval indexes, source maps, and search metadata used by assistant workflows.

Suggested contents:

- repository index manifests
- embeddings metadata references
- chunking configuration notes

## Current Retrieval Files

### Priority Files
- [retrieval-priority.md](retrieval-priority.md) - Priority order for selecting files during assistant retrieval
- [retrieval-rules.md](retrieval-rules.md) - Rules for reliable, low-noise, high-signal retrieval

## Routing Sources And Responsibilities

- `task-routing.md` is the human-readable intent index.
- `task-to-domain-map.yaml` maps broad task categories to repository domains.
- `workflow-to-files.yaml` gives detailed entrypoints, implementation files, and guardrails for common workflows.
- Keep these representations aligned when adding a workflow. Path targets are checked by the validator below.

## Routing Coverage

MLOps workflows are handled here. Requests for shared cluster, identity, secrets, or platform observability capabilities cross the Integration Bridge and should be routed to the documented external `devops-playbook` interfaces.

## Navigation

- Context files: [../context/](../context/)
- Instructions files: [../instructions/](../instructions/)
- Session notes: [../session/](../session/)
- Skills: [../skills/](../skills/)

## Path Validation

The GitHub Actions workflow `.github/workflows/validate-intelligence-paths.yml` runs `scripts/validate-intelligence-paths.py` to check local Markdown links and structured route targets. External `devops-playbook` references are intentionally not resolved against this repository.
