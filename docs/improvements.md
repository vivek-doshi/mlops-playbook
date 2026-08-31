# Repository Intelligence Improvements

## Priority 0 - Make `.ai` Trustworthy [Done]

Completed 2026-08-31.

- Replaced stale platform-as-local routes in `.ai/context/`, `.ai/instructions/`, and `.ai/retrieval/` with valid MLOps paths.
- Marked platform capabilities as external `devops-playbook` dependencies.
- Corrected the duplicate `guardrails` key in the workflow routing manifest.
- Updated routing metadata and repository context to reflect the current repository structure.

## Deferred

Priority 1: Add missing agent entrypoints

Either create concise MLOps-specific versions or redirect these expected files to their existing equivalents:

docs/ARCHITECTURE_DECISION_GUIDE.md
ci/README.md
cd/README.md
terraform/README.md
cd/kubernetes/README.md
This prevents agents from starting at nonexistent files before reaching the genuinely useful golden paths.

Priority 2: Operationalize the intelligence

Add a CI validation script that checks every local path referenced from context, retrieval, and instructions.
Add owner, last-reviewed, source-of-truth, and depends-on metadata to context and retrieval documents.
Set a freshness SLA, such as review on every structural PR and a monthly automated stale-reference check.
Add a skills catalog documenting each skill’s trigger phrases, required inputs, outputs, and validation commands.
Priority 3: Strengthen the Integration Bridge

Replace the placeholder topology README with:

repository responsibility map: devops-playbook versus this repository
executable dependency matrix: required platform primitives, versions, configuration inputs
MLOps control-plane/data-plane diagram
compatibility contract and a CI check against the platform repo’s published manifest
This turns “not islands” from a principle into an enforceable interface.

Priority 4: Improve routing quality

Split generic platform workflows from MLOps workflows. The MLOps routes are strong; the inherited generic routes dilute them. Add intent coverage for the repo’s actual newer domains: batch inference, pipeline orchestration, distributed training, feature store, fairness, online learning, federated learning, multi-cloud serving, and model optimization.