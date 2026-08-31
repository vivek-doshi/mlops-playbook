# Canonical Files

Primary files and directories that should be consulted first for most tasks.

## Repository-Level Canonical Files

- README.md: Primary repository purpose, capabilities, and quick links.
- GETTING_STARTED.md: Fast path from need to file.
- docs/golden-paths/mlops-workflow.md: Canonical end-to-end lifecycle guide.
- docs/golden-paths/: End-to-end preferred workflows.

## Domain Canonical Files

- CI/CD: ci/github-actions/ and ci/github-actions/_shared/
- Infrastructure: terraform/<cloud-target>/
- Kubernetes and runtime delivery: cd/kubernetes/, cd/argo/, and serving/
- Security and policy: policy/ and ci/github-actions/_shared/reusable-mlops-scan.yml
- Cost governance: finops/
- Monitoring: monitoring/

## Canonical Runbook Areas

- docs/runbooks/: Supporting operations and procedures.

## Canonical Selection Rules

- Prefer README and top-level decision guides before deep file reads.
- Prefer golden paths for implementation tasks.
- Prefer target-specific folders only after domain and architecture are identified.
- Prefer reusable shared templates before stack-specific one-off templates.
