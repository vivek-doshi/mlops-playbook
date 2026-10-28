# Repository Intelligence Review - 2026-08-31

## Outcome

Reviewed `.ai/` as the repository-intelligence source of truth. The foundation is strong: it includes architecture context, coding and security standards, MLOps-specific routing, reusable skills, a topology placeholder, and durable session records.

## Integrity Findings

- `.ai/retrieval/` still includes generic platform routes that do not exist in this repository, including `docker/`, `security/`, `secops/`, `observability/`, `notifications/`, and `cd/targets/`.
- Canonical first-read files are missing: `docs/ARCHITECTURE_DECISION_GUIDE.md`, `ci/README.md`, `cd/README.md`, `terraform/README.md`, and `cd/kubernetes/README.md`.
- Broken local references include `cd/kubernetes/promotion/`, `docs/diagrams/README.md`, `docs/runbooks/README.md`, and `monitoring/dashboards/ml-cost-attribution.json`.
- `workflow-to-files.yaml` contains a duplicate `guardrails` key in `mlops_adr_review`; YAML parsers retain only the final value.
- `.ai/skills/README.md` is missing, although each skill directory contains a `SKILL.md`.
- The Integration Bridge naming is inconsistent: `.ai/` references `cicd-reference`, while the root README identifies `devops-playbook`.

## Recommended Next Steps

1. Make the routing corpus MLOps-only and validate all referenced paths in CI.
2. Add or redirect the five canonical entrypoints to real MLOps onboarding documents.
3. Replace the topology placeholder with ownership, dependency, and platform-boundary diagrams.
4. Add a skills catalog that defines triggers, inputs, outputs, and verification requirements.
5. Define a machine-readable Integration Bridge contract with versioning and compatibility checks against `devops-playbook`.
6. Establish freshness metadata and review cadence for `.ai/` context and retrieval artifacts.