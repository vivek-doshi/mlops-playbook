# Contributing to MLOps Playbook

Thank you for contributing. This is a starter template — contributions should make it
**clearer, more correct, or more useful for engineers building production ML systems**.

---

## Setup

```bash
git clone https://github.com/vivek-doshi/mlops-playbook
cd mlops-playbook
python -m venv .venv && source .venv/bin/activate
make install
make pre-commit-install
```

## Workflow

1. Fork the repo and create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes (see coding standards below)
3. Run `make lint` and `make test` — both must pass
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new functionality
   - `fix:` bug fixes
   - `docs:` documentation only
   - `refactor:` code change with no behaviour change
   - `test:` test additions or fixes
   - `chore:` tooling, deps, config
5. Open a PR against `main` with a clear description of what and why

## Coding Standards

- Python 3.12+, type hints on all functions
- PEP8, max line length 127
- `logging` not `print`
- Config-driven — no hardcoded paths or values
- Every new module needs at least one unit test
- Pre-commit hooks must pass before pushing

## What Makes a Good Contribution

- Adds a **new MLOps pattern** (e.g. feature store integration, online learning, canary deployment)
- Fixes a **documented gap** (see `instruction-phase2.md`)
- Improves **developer experience** (Makefile targets, docs, examples)
- Keeps it **simple** — this is a learning template, not a framework

## What to Avoid

- Framework lock-in without a clear alternative documented
- Adding dependencies that don't have a strong reason
- Monolithic scripts
- Skipping tests
