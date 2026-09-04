# Instructions

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

## Routing Quality Improvements (2026-09-04)

The routing system has been strengthened to:

1. **Split generic platform workflows from MLOps workflows**
   - MLOps routing focuses on ML lifecycle workflows (experiment tracking, data versioning, model registry, serving, monitoring, approval, governance)
   - Generic platform routing focuses on infrastructure and operational workflows (provisioning, k8s primitives, secrets, OIDC, policy, observability)

2. **Add intent coverage for newer domains**
   - Batch inference routing patterns
   - Pipeline orchestration routing patterns
   - Distributed training routing patterns
   - Feature store routing patterns
   - Fairness routing patterns
   - Online learning routing patterns
   - Federated learning routing patterns
   - Multi-cloud serving routing patterns
   - Model optimization routing patterns

## Navigation

- Context files: [../context/](../context/)
- Retrieval files: [../retrieval/](../retrieval/)
- Session notes: [../session/](../session/)
- Skills: [../skills/](../skills/)
