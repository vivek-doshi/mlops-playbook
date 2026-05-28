# Topology Context

Place topology maps for repository domains, ownership boundaries, and dependency relationships.

## Integration Bridge

The two repos are not islands. You create a deliberate, documented dependency.

- Platform repository (`cicd-reference`) provides shared primitives.
- This repository consumes those primitives and implements ML lifecycle workflows.

Suggested contents:

- folder ownership map
- pipeline dependency graph
- control-plane vs data-plane boundaries
- platform repo vs mlops repo responsibility split
