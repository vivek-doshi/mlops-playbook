# ADR-ML-007: Dev Containers as the Standardised Local Development Environment

**Status:** Accepted
**Date:** 2024-10-15
**Authors:** ML Platform Team
**Reviewers:** @ml-approvers

---

## Context

The MLOps Playbook requires a development environment with a specific, reproducible set of tools:

- Python 3.11 with 15+ Python packages (MLflow, DVC, Evidently, pytest, pre-commit, etc.)
- Terraform CLI (version-pinned)
- kubectl + Helm
- GitHub CLI
- AWS CLI and GCloud CLI
- Docker CLI (for starting the MLflow stack)
- GPU drivers for local inference testing (Triton, vLLM)

Without a standardised environment:
- New team members spend 2–4 hours on setup before writing their first commit.
- Different developers run different Python versions or package versions, causing "works on my machine" failures.
- Pre-commit hooks may behave differently across OS versions.
- GPU-accelerated serving tests require CUDA setup that is error-prone on all three operating systems.

---

## Decision

We will use **Dev Containers** (the open specification at containers.dev, VS Code + GitHub Codespaces compatible) as the standardised local development environment for this repository.

The Dev Container is defined in `.devcontainer/devcontainer.json`.

Key configuration choices:

| Decision | Value | Rationale |
|---------|-------|-----------|
| Base image | `mcr.microsoft.com/devcontainers/python:3.11` | Microsoft-maintained; ships with common dev tools; matches production Python version |
| Docker-in-Docker | v2, Docker Compose v2 | Needed to start MLflow stack (PostgreSQL + MinIO) from inside the container |
| Terraform | 1.8 via devcontainers/features | Version-pinned, avoids host Terraform conflicts |
| kubectl + Helm | via devcontainers/features | Serving deployment testing without host install |
| GPU passthrough | `"runArgs": ["--gpus", "all"]` | NVIDIA RTX 5070 available inside container; no separate CUDA install needed |
| Remote user | `vscode` (non-root) | Security best practice — containers should not run as root |
| VS Code format on save | black + isort + terraform fmt | Enforces code style without manual invocation |

---

## Alternatives Considered

### conda / mamba environments
- **Pros:** Industry-standard for data science. Handles C library dependencies (numpy, scipy, CUDA bindings) that `pip` sometimes struggles with.
- **Cons:** Environment definitions are not fully reproducible across OS — `conda env export` produces OS-specific lockfiles. Does not include non-Python tools (Terraform, kubectl, GitHub CLI). Does not solve GPU driver version consistency.

### virtualenv + requirements.txt (bare-metal)
- **Pros:** Lowest overhead; fastest cold start.
- **Cons:** No isolation of system-level tools. Python version drift over time. On-boarding each new OS type (Windows vs macOS vs Linux) requires separate documentation.

### Docker Compose (custom dev image, no Dev Container spec)
- **Pros:** Full Docker control; works without VS Code.
- **Cons:** No VS Code extension integration (IntelliSense, debugger, format-on-save). Engineers run commands inside `docker exec` rather than naturally in a terminal. Harder to onboard non-Docker-expert data scientists.

### GitHub Codespaces (cloud only)
- **Partly adopted:** The `.devcontainer/devcontainer.json` is fully Codespaces-compatible — teams can use Codespaces for quick contributions. However, GPU-accelerated local development (RTX 5070) requires the Dev Container running locally via Docker Desktop, not in a cloud Codespace (Codespaces GPU instances are available but expensive).

### Nix / Nix flakes
- **Pros:** Hermetic, reproducible builds. Works without Docker.
- **Cons:** Steep learning curve. Not widely known in ML teams. Poor Windows support without WSL. Not aligned with the platform team's current tooling.

---

## Consequences

**Positive:**
- First-time setup is `git clone` + `Reopen in Container` — typically under 5 minutes (after Docker layer caching).
- GPU passthrough works on Windows via WSL 2 + Docker Desktop, resolving the most common local inference testing friction.
- Dependabot monitors the Dev Container feature versions (tracked in `.github/dependabot.yml`).

**Negative:**
- Requires Docker Desktop (or Podman Desktop) — not all corporate environments allow Docker. Bare-metal path (`bootstrap.sh` / `bootstrap.ps1`) remains available as a fallback.
- First build is slow (~3–5 min) on a cold cache. Team members on low-bandwidth connections may find the image pull slow.

**Neutral:**
- The Dev Container spec is evolving. `devcontainer.json` format v2 (2023) added `hostRequirements.gpu` — used here for Codespaces GPU instance selection.

---

## Review Triggers

Re-evaluate if:
- The team standardises on JupyterHub or a managed notebook platform — cloud-hosted environments would supersede local Dev Containers for most interactive work.
- Docker Desktop licence changes affect team adoption — Podman Desktop is a drop-in replacement for the Dev Container spec.
