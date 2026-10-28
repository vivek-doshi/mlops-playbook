# Repository Readiness Review - 2026-10-27

## Outcome

Reviewed the MLOps playbook positioning, `.ai/` context, routing, instructions, skills, generated map, and repository-facing README for accuracy, duplication, and presentation readiness.

The repository has a clear MLOps lifecycle purpose and a useful set of golden paths, templates, policies, and repository intelligence. The `.ai/` folder is substantial, but it is not fully current or internally consistent enough to treat as a reliable source of truth without follow-up.

## Findings

- The Integration Bridge dependency name is inconsistent. `.ai/context/repo-summary.md`, `.ai/context/project_details.md`, and `.ai/topology/README.md` refer to `cicd-reference`, while the root `README.md` and other current repository docs identify `devops-playbook`. The August 31 intelligence review already recorded this inconsistency.
- Some guidance points to paths that do not exist: `.ai/context/glossary.md` names `docs/glossary.md` as its source; `.ai/instructions/terraform-rules.md` recommends `terraform/aws-eks`, `terraform/azure-aks`, and `terraform/gcp-gke`; `.ai/instructions/kubernetes-rules.md` recommends `cd/kubernetes/_patterns`. The current repository uses other Terraform target folders and has no `_patterns` folder.
- The root README and `.ai/context/repo-summary.md` do not cover the repository's newer MLOps areas consistently. The root README's phase section ends at ADR-ML-018 although ADR-ML-019 through ADR-ML-024 exist. The summaries also omit several newer domains, making the public-facing scope appear behind the actual repository.
- `.ai/retrieval/workflow-to-files.yaml` and the prose routing guides overlap but are not equally comprehensive. The YAML includes a small set of lifecycle routes and predates newer domains; this creates multiple sources that can disagree about where users should start.
- Several context files repeat purpose, platform-boundary, and navigation information (`repo-summary.md`, `project_details.md`, and `architecture-overview.md`). `.ai/context/glossary.md` also overlaps with `terminology.md`. This is manageable, but increases drift unless one source is declared canonical and the others are kept deliberately concise.
- `.ai/skills/senior-devops-architect/SKILL.md` describes this project as a multi-cloud DevOps reference repository, which conflicts with the MLOps-playbook identity.
- `.ai/context/repo_map.md` records `d:/projects/mlops-playbook` as its root and a September 27 generation time. The root is machine-specific and does not match the current workspace.
- The intelligence path workflow checks a narrow set of colon-prefixed `.md` references; it does not comprehensively validate Markdown links, YAML route targets, or directory references in routing and instruction content. Its presence should not be treated as proof that all `.ai/` references are valid.

## Original Recommendations

1. Update or remove invalid path recommendations and add a real glossary source, or point the glossary context at an existing canonical document.
2. Bring the README and summary context up to date with implemented ADRs and newer MLOps domains; distinguish implemented examples from aspirational or optional patterns.
3. Choose canonical structured routing data and either generate or validate the overlapping prose and YAML maps from it.
4. Reduce duplicated overview material and establish clear ownership for purpose, architecture, and terminology.
5. Make repo-map output reproducible across machines by avoiding a developer-specific absolute root in committed output.
6. Expand path validation to parse the actual link and route formats used by the repository.

## Follow-up - Platform Repository Name

Standardized active `.ai/` references on `devops-playbook`, matching the root README and its platform repository link. The August 31 session note remains unchanged as a historical record of the inconsistency at that time.

## Follow-up - Remaining Findings

- Corrected stale glossary, Terraform, Kubernetes, incident-response, and dashboard paths; replaced nonexistent runbook/diagram references with current documentation and monitoring entrypoints.
- Updated the root README and repository context with the advanced lifecycle areas and ADR-ML-019 through ADR-ML-024.
- Clarified distinct roles for prose routing, broad domain mapping, and detailed workflow mapping; added missing LLMOps and self-service routes.
- Reduced duplicated project overview content and corrected the DevOps architect skill's repository description.
- Made generated repository-map roots portable and replaced the old link check with validation for local Markdown links and structured route targets.

## Validation and Scope

- Checked the relevant `.ai/context/`, `.ai/instructions/`, `.ai/retrieval/`, `.ai/skills/`, recent session notes, root README, validation workflows, and repository-map generator.
- `python scripts/validate-intelligence-paths.py` passed.
- Updated retrieval and GitHub Actions YAML files parsed successfully.
- `git diff --check` passed.
- No application code was changed and no application tests were run; this was a documentation and repository-intelligence review.
