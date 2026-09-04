# Retrieval Context

Place retrieval indexes, source maps, and search metadata used by assistant workflows.

Suggested contents:

- repository index manifests
- embeddings metadata references
- chunking configuration notes

## Current Retrieval Files

### Priority Files
- [retrieval-priority.md](retrieval-priority.md) - Priority order for selecting files during assistant retrieval
- [retrieval-rules.md](retrieval-rules.md) - Rules for reliable, low-noise, high-signal retrieval

## Routing Quality Improvements (2026-09-04)

The retrieval system has been strengthened to:

1. **Split generic platform workflows from MLOps workflows**
   - MLOps routing focuses on ML lifecycle workflows
   - Generic platform routing focuses on infrastructure and operational workflows

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
- Instructions files: [../instructions/](../instructions/)
- Session notes: [../session/](../session/)
- Skills: [../skills/](../skills/)
