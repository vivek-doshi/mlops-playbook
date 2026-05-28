# Policy

Three policy domains govern model lifecycle and data handling in this repository.

| Domain | Directory | Purpose |
|--------|-----------|---------|
| Model approval | `policy/model-approval/` | Gates model promotion from Staging to Production |
| Data governance | `policy/data-governance/` | Data classification, PII rules, retention |
| Infrastructure policy | `devops-playbook/policy/kyverno/` | Kubernetes resource limits, GPU quotas |

---

## How Policies Are Enforced

### Model approval (this repo)

Model promotion to Production requires all three conditions in the approval gate:

1. Accuracy on the held-out test set meets or exceeds the registered threshold.
2. Dataset drift score is below 0.3 (checked by `monitoring/evidently/drift_report.py`).
3. DVC data hash logged on the training run matches the hash in the model registry tag.

The approval gate is implemented in `ci/github-actions/model-evaluation/evaluate.yml`
and documented in `policy/model-approval/README.md`.

### Data governance (this repo)

All datasets must be classified before use in training. PII datasets require
additional review steps documented in `policy/data-governance/README.md`.

### Infrastructure policy (platform repo)

Kubernetes-level enforcement (GPU resource limits, required labels, network policies)
is maintained in `devops-playbook/policy/kyverno/`. These policies run as admission
webhook checks on every `kubectl apply`.

---

## Related

- `policy/model-approval/README.md` — model promotion requirements
- `policy/model-approval/approved-versions.yaml` — approval registry
- `policy/data-governance/README.md` — data classification and PII rules
- `policy/data-governance/pii-model-checklist.md` — PII model promotion checklist
- `devops-playbook/policy/kyverno/` — Kubernetes infrastructure policies
