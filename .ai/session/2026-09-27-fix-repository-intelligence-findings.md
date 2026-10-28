# Repository Intelligence Findings Fix

Date: 2026-09-27

- Repaired intelligence path validation so missing references fail CI.
- Removed the invalid duplicate shell branch from stale-reference validation and enforced metadata freshness across non-generated intelligence documents.
- Made platform compatibility checks fail closed, validate local minimum and maximum contract versions, required features, and component minimum versions.
- Corrected newer-domain routing paths to match repository directory names.
- Regenerated `.ai/context/repo_map.md` from the current workspace.
- Updated `docs/improvements.md` to mark agent entrypoints complete.

Validation performed:

- `git diff --check`
- Metadata coverage check for 22 intelligence documents
- Route target existence check
- Repository map root and topology check
- Workflow YAML parsing attempted; local Python needed explicit UTF-8 decoding for the repository's workflow encoding.
