---
# Pull Request Template — MLOps Playbook
#
# Fill in the sections below before requesting review.
# Delete sections that do not apply to this change.
# For minor doc fixes, you may skip the ML-specific sections.

## Summary

<!-- 1–3 sentences describing what this PR does and why. -->



## Type of Change

<!-- Check all that apply. -->

- [ ] New golden path / guide (docs only)
- [ ] CI pipeline change (training / evaluation / deployment / monitoring workflow)
- [ ] Serving infrastructure (Triton / TorchServe / vLLM config)
- [ ] Monitoring change (Evidently script, Prometheus alerts, Grafana dashboard)
- [ ] Policy or governance change (`policy/`)
- [ ] Infrastructure change (Terraform)
- [ ] MLflow tracking server change
- [ ] DVC pipeline / remote storage change
- [ ] Developer tooling (Makefile, Taskfile, pre-commit, devcontainer)
- [ ] Security fix
- [ ] Dependency update (Dependabot)
- [ ] Bug fix
- [ ] Refactor (no functional change)
- [ ] Website (gh pages)

---

## ML Lineage (Required for model changes)

<!-- Complete this section for any change that affects training, evaluation, or serving. -->

| Field | Value |
|-------|-------|
| MLflow Run ID | `mlflow://runs/<run-id>` |
| DVC Data Hash | `sha256:<hash>` |
| Model name (registry) | |
| Model version | |
| Target environment | dev / staging / production |

---

## Evaluation Gates

<!-- For model promotion PRs, confirm all three gates passed. -->

- [ ] **Accuracy gate** — accuracy meets or exceeds threshold tag from MLflow run
- [ ] **Drift gate** — Evidently drift score < 0.3 on holdout / production data
- [ ] **Lineage gate** — `dvc_data_hash` MLflow tag matches current `.dvc` hash

---

## Testing

- [ ] Ran `dvc repro` or individual pipeline stage locally — output matches expected
- [ ] Unit tests pass: `pytest` (or `make lint`)
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`
- [ ] For serving changes: smoke-tested health endpoint (`/v2/health/ready` or `/ping`)
- [ ] For monitoring changes: `make drift-check` ran successfully

---

## Security Checklist

- [ ] No secrets, credentials, or PII committed to this PR
- [ ] No model artifacts (`.pkl`, `.pt`, `.onnx`) larger than 500 MB committed — use DVC
- [ ] If PII-trained model: [PII model checklist](policy/data-governance/pii-model-checklist.md) completed and linked

---

## Documentation

- [ ] Relevant golden path updated (if behaviour changed)
- [ ] ADR created or updated (if a tool or architectural decision changed)
- [ ] GETTING_STARTED.md updated (if prerequisites or first-run steps changed)
- [ ] No docs update needed

---

## Reviewer Notes

<!-- Anything specific reviewers should focus on, or context they need. -->



---

## Linked Issues

<!-- Closes #<issue-number> -->
