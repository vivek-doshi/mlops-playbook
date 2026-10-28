# Production Readiness Standard

This document defines the minimum evidence required before a model or MLOps
component is described as production-ready. The repository contains reference
implementations at different maturity levels; a folder existing in the
repository is not, by itself, production evidence.

## Maturity labels

Every workflow or domain should be described using one of these labels:

- **Reference**: architecture or starter pattern; not validated end to end.
- **Validated locally**: the documented local command succeeds.
- **Validated in CI**: automated tests and manifest checks run on pull requests.
- **Validated in staging**: deployed and exercised in a representative staging environment.
- **Production-ready**: staging evidence, security review, rollback evidence, SLO ownership,
  and operational runbooks are complete.
- **Platform integration required**: depends on `devops-playbook` capabilities not supplied here.

The repository should not label a component Production-ready until the required
environment-specific evidence below is attached to the release.

## Required production evidence

### Reproducibility and lineage

- Source commit, dependency lock, container digest, dataset hash, feature snapshot,
  training run ID, model artifact digest, and deployment ID are recorded.
- Missing lineage fields block promotion.
- Dataset, job, and run events should be emitted using the OpenLineage contract.

### Quality and responsible AI

- Model performance, data quality, drift, fairness, explainability, and security gates pass.
- A model card identifies intended use, prohibited use, owner, data classification,
  limitations, monitoring, and review date.
- High-impact use cases require documented human oversight and escalation.

### Release and runtime safety

- Images are referenced by immutable digest and signed.
- Deployments use canary, blue/green, or shadow evaluation where risk warrants it.
- A tested rollback plan exists and the previous model remains available.
- Production promotion is fail-closed and requires human approval.

### Operations and reliability

- SLOs define availability, latency, error rate, model quality, and alert ownership.
- OpenTelemetry metrics, logs, and traces include `model_version`, `deployment_id`,
  `feature_set_version`, `source_commit`, and `request_id`.
- Label delay, feature freshness, prediction volume, and business KPIs are monitored.
- Alerts link to a runbook with detection, investigation, remediation, and post-incident steps.

### Security and supply chain

- OIDC or workload identity is used instead of long-lived cloud credentials.
- Portal actions require enterprise authentication and role-based authorization.
- Dependencies are locked and vulnerability-scanned.
- SBOM, signed image, and build provenance are retained with the release.
- GitHub Actions are pinned to immutable commit SHAs for high-trust repositories.

### Resilience and recovery

- RTO and RPO are documented for MLflow, object storage, model registry, feature store,
  secrets, monitoring, and serving.
- Backup restore is tested on a schedule.
- Multi-region or multi-cluster failover is tested where the business requires it.
- Recovery evidence is retained with the release or disaster-recovery exercise.

## Required platform boundary

This repository supplies ML lifecycle controls. `devops-playbook` must supply and
prove cluster, identity, secrets, admission policy, base observability, and incident
notification controls before an integrated deployment can claim production readiness.

## Review cadence

- Model owners review model cards and risk classification at least quarterly.
- Security and supply-chain controls are reviewed monthly.
- SLO and cost evidence is reviewed monthly.
- Disaster recovery restore evidence is reviewed at least quarterly.
