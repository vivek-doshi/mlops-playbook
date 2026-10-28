# Repository Intelligence Improvements

## Priority 0 - Make `.ai` Trustworthy [Done]

Completed 2026-08-31.

- Replaced stale platform-as-local routes in `.ai/context/`, `.ai/instructions/`, and `.ai/retrieval/` with valid MLOps paths.
- Marked platform capabilities as external `devops-playbook` dependencies.
- Corrected the duplicate `guardrails` key in the workflow routing manifest.
- Updated routing metadata and repository context to reflect the current repository structure.

## Priority 1 - Add missing agent entrypoints [Done]

Completed 2026-09-27.

The expected agent entrypoints now exist:

docs/ARCHITECTURE_DECISION_GUIDE.md
ci/README.md
cd/README.md
terraform/README.md
cd/kubernetes/README.md
These entrypoints prevent agents from starting at nonexistent files before reaching the genuinely useful golden paths.

## Priority 2: Operationalize the intelligence [Done]

Completed 2026-09-03.

- Created CI validation script in `.github/workflows/validate-intelligence-paths.yml` that checks every local path referenced from context, retrieval, and instructions.
- Added owner, last-reviewed, source-of-truth, and depends-on metadata to all canonical context documents:
  - [architecture-overview.md](.ai/context/architecture-overview.md)
  - [glossary.md](.ai/context/glossary.md)
  - [project_details.md](.ai/context/project_details.md)
  - [repo-summary.md](.ai/context/repo-summary.md)
- Added metadata to all retrieval documents:
  - [bounded-contexts.md](.ai/retrieval/bounded-contexts.md)
  - [canonical-files.md](.ai/retrieval/canonical-files.md)
  - [common-workflows.md](.ai/retrieval/common-workflows.md)
  - [entrypoints.md](.ai/retrieval/entrypoints.md)
  - [file-selection-guide.md](.ai/retrieval/file-selection-guide.md)
  - [retrieval-priority.md](.ai/retrieval/retrieval-priority.md)
  - [retrieval-rules.md](.ai/retrieval/retrieval-rules.md)
  - [search-hints.md](.ai/retrieval/search-hints.md)
  - [task-routing.md](.ai/retrieval/task-routing.md)
- Created skills catalog in `.ai/skills/SKILL-CATALOG.md` documenting each skill's trigger phrases, required inputs, outputs, and validation commands.
- Created monthly stale-reference check workflow in `.github/workflows/stale-reference-check.yml` with freshness SLA enforcement.
- Set up CI validation on every structural PR and monthly automated stale-reference check.

Completed 2026-09-04.

Priority 3: Strengthen the Integration Bridge [Done]

- Created repository responsibility map in [docs/topology/INTEGRATION-BRIDGE.md](docs/topology/INTEGRATION-BRIDGE.md) documenting devops-playbook versus this repository responsibilities.
- Created executable dependency matrix in [docs/topology/DEPENDENCY-MATRIX.md](docs/topology/DEPENDENCY-MATRIX.md) with required platform primitives, versions, and configuration inputs.
- Created MLOps control-plane/data-plane diagram in [docs/topology/CONTROL-PLANES.md](docs/topology/CONTROL-PLANES.md) showing governance and execution layers.
- Created compatibility contract in [docs/topology/COMPATIBILITY-CONTRACT.md](docs/topology/COMPATIBILITY-CONTRACT.md) with platform manifest requirements and compatibility matrix.
- Created CI check for platform manifest compatibility in `.github/workflows/platform-compatibility.yml` validating platform version and required features.
- Turned "not islands" from a principle into an enforceable interface with CI enforcement.

Priority 4: Improve routing quality [Done]

Completed 2026-09-04.

- Created routing quality documentation in [docs/topology/ROUTING-QUALITY.md](docs/topology/ROUTING-QUALITY.md) describing routing quality improvements.
- Updated [task-routing.md](.ai/retrieval/task-routing.md) with MLOps-Specific Routing - Newer Domains section and Generic Platform Routing section.
- Split generic platform workflows from MLOps workflows.
- Added intent coverage for the repo's actual newer domains: batch inference, pipeline orchestration, distributed training, feature store, fairness, online learning, federated learning, multi-cloud serving, and model optimization.

## Priority 5: Production hardening [In progress - 2026-10-28]

Completed in this hardening pass:

- Made production deployment and lineage checks fail closed.
- Added a machine-readable model approval gate contract.
- Added OIDC authentication, role checks, explicit CORS, and audit logging to the portal.
- Added portal/policy tests and pull-request YAML/Python validation.
- Replaced the production serving overlay's mutable image tag with a verified digest replacement.
- Added model inventory, risk-tier review, label-delay alerts, release strategy guidance,
  supply-chain requirements, lineage/observability contracts, and disaster-recovery standards.
- Standardized topology references on the external `devops-playbook` platform repository.

Remaining environment-specific evidence:

- Configure the production OIDC tenant, groups, and allowed origins.
- Generate and verify SBOMs, signatures, and build provenance in the release platform.
- Run staging canary/blue-green, restore, failover, and champion/challenger exercises.
- Retain signed evidence and complete the maturity checklist before claiming production readiness.

## CI hardening follow-up - 2026-10-28

- Added [`docs/topology/platform-manifest.yaml`](topology/platform-manifest.yaml)
  as the local reference for the `devops-playbook/manifest.yaml` contract.
- Updated the platform compatibility workflow to download the authoritative
  existing manifest through the GitHub Contents API instead of cloning the
  platform repository and requiring a local copy.
- Added a pytest path bootstrap and aligned CI with `python -m pytest` so the
  `portal` package is importable on GitHub-hosted runners.
- Updated portal dependencies, including FastAPI/Starlette, PyJWT,
  cryptography, protobuf transitives, MLflow, and the Kubernetes client.
- Audited the resolved wheel dependency closure with `pip-audit`; no known
  vulnerabilities were reported.