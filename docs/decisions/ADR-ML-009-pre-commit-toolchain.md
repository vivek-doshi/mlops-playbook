# ADR-ML-009: Pre-commit Hooks and Code Quality Toolchain

**Status:** Accepted
**Date:** 2024-11-15
**Authors:** ML Platform Team
**Reviewers:** @ml-approvers

---

## Context

ML repositories accumulate technical debt faster than typical software projects because:

- **Notebooks** produce large JSON diffs that obscure meaningful code changes in PR reviews.
- **Credentials** (API keys, HuggingFace tokens, cloud credentials) are accidentally committed in config files, notebooks, and training scripts.
- **Inconsistent formatting** (Black vs autopep8 vs manual) causes noisy diffs and merge conflicts.
- **Security vulnerabilities** in ML dependencies (numpy, PyTorch, transformers) are frequently published — unpatched packages stay in `requirements.txt` for months without automated scanning.
- **Terraform drift** — IaC files that are not formatted (`terraform fmt`) or valid (`terraform validate`) cause CI failures that block deployments.

Shift-left enforcement (catching issues at commit time, before CI) reduces the feedback loop from minutes to seconds and prevents known issues from ever reaching the PR queue.

---

## Decision

We will use **pre-commit** (the Python framework at pre-commit.com) with a curated hook set defined in `.pre-commit-config.yaml`.

Hook inventory:

| Hook | Tool | Version | Purpose |
|------|------|---------|---------|
| `trailing-whitespace` | pre-commit-hooks | - | Universal hygiene |
| `check-yaml` | pre-commit-hooks | - | Catch malformed YAML before CI |
| `check-json` | pre-commit-hooks | - | Catch malformed JSON (dashboards, configs) |
| `check-added-large-files` | pre-commit-hooks | 10 MB limit | Block accidental model binary commits |
| `no-commit-to-branch` | pre-commit-hooks | `main`, `master` | Enforce branch workflow |
| `detect-private-key` | pre-commit-hooks | - | Block PEM/SSH keys |
| `black` | psf/black | 24.4.2 | Python formatting (PEP 8 compliant) |
| `isort` | PyCQA/isort | 5.13.2 | Import sorting (Black-compatible profile) |
| `ruff` | astral-sh/ruff | 0.4.7 | Linting + `--fix` auto-correction |
| `bandit` | PyCQA/bandit | 1.7.8 | Security linting (medium+ severity) |
| `detect-secrets` | Yelp/detect-secrets | 1.5.0 | Entropy-based secret detection with baseline |
| `terraform_fmt` | antonbabenko/pre-commit-terraform | 1.90.0 | Terraform formatting |
| `terraform_validate` | antonbabenko/pre-commit-terraform | 1.90.0 | Terraform syntax validation |
| `terraform_trivy` | antonbabenko/pre-commit-terraform | 1.90.0 | IaC security scan (HIGH/CRITICAL) |
| `actionlint` | rhysd/actionlint | 1.7.1 | GitHub Actions YAML schema validation |
| `markdownlint` | igorshubovych/markdownlint-cli | 0.41.0 | Markdown style (with `--fix`) |

Formatter choice rationale: **Black** (opinionated, no config debates) + **isort** (import order, Black-compatible) + **Ruff** (fast linter, replaces flake8 + pyupgrade + dozens of other plugins in a single tool).

---

## Alternatives Considered

### pylint + flake8 + autopep8
- **Pros:** pylint is highly configurable and catches semantic issues Black/Ruff miss.
- **Cons:** Three separate tools with overlapping concerns and conflicting configuration. autopep8 formatting is less opinionated than Black — formatting debates continue. pylint runtime is 5–10× slower than Ruff for large codebases. Not worth the complexity delta vs. Ruff.

### flake8 alone (no formatter)
- **Cons:** Linting without autofix means developers must manually correct flagged lines — slow feedback loop. Ruff covers all of flake8's default rules plus 400+ additional rules and auto-fixes many of them.

### prospector / wemake-python-styleguide
- **Cons:** Extremely strict; produces hundreds of warnings on any existing codebase. Good for greenfield strict projects; counterproductive for a playbook repo where examples intentionally show patterns rather than production-hardened code.

### SonarQube
- **Pros:** Rich dashboard; historical trend analysis.
- **Cons:** Requires a SonarQube server (or SonarCloud subscription). Per-scan cost. Pre-commit hooks run offline and cost nothing. SonarQube is a complementary tool for mature projects, not a replacement for developer-local linting.

---

## Consequences

**Positive:**
- Secrets and private keys cannot reach GitHub history — `detect-secrets` with a committed `.secrets.baseline` blocks new secrets while acknowledging known test values.
- `no-commit-to-branch main` enforces the PR workflow — direct pushes to `main` are blocked at the client side (in addition to branch protection rules on GitHub).
- `bandit` scans `monitoring/` and `scripts/` — the highest-risk paths for hardcoded credentials and unsafe subprocess calls.

**Negative:**
- Pre-commit hooks add 2–5 seconds to every commit. On slow machines or large files, `black` + `ruff` can take up to 15 seconds.
- `detect-secrets` produces false positives on base64-encoded model weights in config files. These must be added to `.secrets.baseline` via `detect-secrets scan > .secrets.baseline`.
- `terraform_validate` requires `terraform init` to have been run first — hooks will fail on a fresh clone before `task setup` is complete.

**Neutral:**
- The CI pipeline (`_shared/reusable-mlops-scan.yml`) runs `pip-audit` and `gitleaks` as a second defence layer — pre-commit is the first defence, CI is the second. Neither replaces the other.

---

## Review Triggers

Re-evaluate if:
- The team adopts `uv` as the Python package manager — Ruff and Black would still apply, but the install mechanism for pre-commit hooks would change.
- A notebook-first workflow is adopted — `nbstripout` and `nbqa` hooks should be added to clean notebook outputs before commit.
