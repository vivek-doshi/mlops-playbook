# Glossary
---
**Owner**: @mlops-team
**Last Reviewed**: 2026-08-31
**Source of Truth**: docs/glossary.md
**Depends On**: docs/decisions/
---
- ADR: Architecture Decision Record documented under docs/decisions/.
- CD: Continuous Delivery or Continuous Deployment templates under cd/.
- CI: Continuous Integration templates under ci/.
- ESO: External Secrets Operator for syncing external secret stores to Kubernetes.
- Falco: Runtime security detection used for container and node anomaly signals.
- FinOps: Operational and governance practices for cloud cost management.
- GitOps: Deployment model where cluster state is reconciled from Git.
- Golden Path: Opinionated, end-to-end implementation path with built-in guardrails.
- HPA: Horizontal Pod Autoscaler for scaling workloads on metrics.
- IaC: Infrastructure as Code, mainly Terraform and Pulumi in this repo.
- Infracost: Tooling for estimating Terraform cost impact in pull requests.
- Kyverno: Kubernetes policy engine for admission and governance rules.
- Loki: Log aggregation system used for operational and security investigations.
- OIDC: OpenID Connect federation used for short-lived cloud authentication.
- PDB: PodDisruptionBudget to protect service availability during disruptions.
- SBOM: Software Bill of Materials used for supply chain visibility.
- SAST: Static Application Security Testing integrated in pipeline templates.
- SLO: Service Level Objective used for reliability targets.
- VPA: Vertical Pod Autoscaler for rightsizing recommendations.
- Integration Bridge: Documentation in `docs/topology/` describing platform vs MLOps responsibilities and dependencies.
- Dependency Matrix: Documentation in `docs/topology/` showing platform primitives and MLOps component dependencies.
- Control Plane/Data Plane: Documentation in `docs/topology/` describing governance vs execution layers.
- Compatibility Contract: Documentation in `docs/topology/` defining platform version requirements.
- Routing Quality: Documentation in `docs/topology/` describing MLOps-specific routing patterns.
