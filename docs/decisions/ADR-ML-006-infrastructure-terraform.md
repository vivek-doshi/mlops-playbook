# ADR-ML-006: Terraform for ML Infrastructure Provisioning

**Status:** Accepted
**Date:** 2024-10-01
**Authors:** ML Platform Team
**Reviewers:** @ml-approvers, @platform-infra-team

---

## Context

The MLOps platform requires cloud infrastructure across three providers:

- **AWS SageMaker** — managed training and batch inference for teams with existing AWS footprint.
- **GCP Vertex AI** — managed training and online prediction for teams in the Google Cloud ecosystem.
- **GPU cluster** — shared Kubernetes GPU node pool consumed by serving deployments (Triton, TorchServe, vLLM).

Infrastructure must be:
- Reproducible across dev, staging, and production environments.
- Auditable — changes tracked in Git, reviewed via PR, approved before apply.
- Aligned with the platform repository (`devops-playbook`) which already standardises on Terraform.
- Destroyable — dev environments should be cheap to spin up and tear down.

---

## Decision

We will use **Terraform** (HashiCorp, MPL-2.0) for all ML infrastructure provisioning in this repository.

Module layout:

| Module | Path | Provider |
|--------|------|---------|
| AWS SageMaker | `terraform/aws-sagemaker/` | `hashicorp/aws` |
| GCP Vertex AI | `terraform/gcp-vertex-ai/` | `hashicorp/google` |
| Azure ML | `terraform/azure-ml/` | `hashicorp/azurerm` |
| GPU cluster (reference) | `terraform/gpu-cluster/` | Consumes platform module |

Conventions:

| Convention | Rationale |
|-----------|-----------|
| Each cloud target is a separate module | Enables `terraform plan` per target without cross-provider state entanglement |
| `variables.tf` for all inputs | No hardcoded resource names; safe to commit |
| `outputs.tf` for all IDs | Downstream consumers (serving deploy scripts) reference outputs, not hardcoded strings |
| Backend state in remote (S3/GCS) | Defined in platform repo; this repo references via `terraform_remote_state` |
| `terraform fmt -recursive` in pre-commit | Enforced formatting before every commit |
| `terraform validate` in CI | Syntax validation on every PR via `actionlint`-checked workflows |

---

## Alternatives Considered

### Pulumi
- **Pros:** Full programming language support (Python/TypeScript/Go) — familiar to ML engineers already writing Python. Rich type system. Native async support.
- **Cons:** The platform repository uses Terraform; diverging IaC tools would require ML engineers to maintain Pulumi state backends separately and learn a second tool. Not justified at current infrastructure complexity.

### AWS CDK / GCP Deployment Manager
- **Pros:** Cloud-native, tightly integrated with respective cloud consoles.
- **Cons:** Cloud-provider lock-in at the IaC layer. Multi-cloud capability (AWS + GCP simultaneously) is a hard requirement for our heterogeneous team environments.

### Ansible
- **Pros:** Excellent for configuration management of existing infrastructure.
- **Cons:** Not designed for declarative cloud resource provisioning. No state management equivalent to Terraform's plan/apply/destroy cycle. Not idiomatic for cloud resource lifecycle.

### Helm (for GPU cluster only)
- **Partly adopted:** Helm charts are used for application deployments (serving workloads) by the platform repository. Terraform manages the underlying node pool and cluster config; Helm manages what runs on it. Not either/or.

---

## Consequences

**Positive:**
- Unified IaC tooling across platform and ML repositories reduces cognitive load.
- `terraform plan` output in PRs provides a concrete diff of infra changes before merge.
- Modular structure allows teams to adopt only the cloud target they need.

**Negative:**
- Terraform state must be initialised before `plan`/`apply`. First-time users must run `terraform init` with access to the remote state backend — adds onboarding friction.
- The GPU cluster module is a documentation-as-code stub that delegates to the platform module. Changes to the platform module may require corresponding updates here.

**Neutral:**
- Provider version pins in `required_providers` blocks are managed by Dependabot (see `.github/dependabot.yml`) — weekly PRs keep providers current without manual tracking.
- **Azure GPU quota lead time**: NDv4 (`Standard_ND96asr_v4`) and NDv5 (`Standard_ND96isr_H100_v5`) series are restricted SKUs in most Azure regions. Quota increases require a support ticket and typically take **1–4 weeks** to approve. Teams planning production GPU training on Azure should open the quota request at project kickoff, not at deployment time. The `gpu_cluster_max_nodes` variable in `terraform/azure-ml/variables.tf` is validated to a maximum of 16, which aligns with typical enterprise quota limits after approval and prevents accidental over-allocation during initial provisioning.

---

## Review Triggers

Re-evaluate if:
- The team moves to a GitOps-heavy model (Flux/ArgoCD for everything) — Crossplane might replace Terraform for in-cluster resource provisioning.
- OpenTofu (the Terraform fork) becomes the team's preferred open-source alternative following HashiCorp's BSL licence change in 2023.
