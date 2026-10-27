# Instructions

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-10-27
**Source of Truth**: .ai/instructions/
**Depends On**: .ai/context/, .ai/retrieval/
---

This directory contains AI agent instructions for working with this repository.

## Current Instructions

### Coding Standards
- [coding-standards.md](coding-standards.md) - Code quality standards and conventions

### Documentation Rules
- [documentation-rules.md](documentation-rules.md) - Documentation writing guidelines

### Engineering Principles
- [engineering-principles.md](engineering-principles.md) - Engineering philosophy and practices

### Kubernetes Rules
- [kubernetes-rules.md](kubernetes-rules.md) - Kubernetes-specific guidelines

### Security Rules
- [security-rules.md](security-rules.md) - Security best practices

### Terraform Rules
- [terraform-rules.md](terraform-rules.md) - Infrastructure as Code guidelines

## Routing

Use `.ai/retrieval/task-routing.md` for human-readable intent routing and the structured maps in `.ai/retrieval/` for domain and workflow selection. Shared platform requests belong to the external `devops-playbook` integration boundary; do not imply that this repository owns those platform implementations.

## Navigation

- Context files: [../context/](../context/)
- Retrieval files: [../retrieval/](../retrieval/)
- Session notes: [../session/](../session/)
- Skills: [../skills/](../skills/)
