# Architecture Overview

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-08-31
**Source of Truth**: docs/ARCHITECTURE_DECISION_GUIDE.md
**Depends On**: external devops-playbook repository
---

## System-Level Architecture

This repository is a production-oriented MLOps playbook. It implements the ML lifecycle layer on top of platform controls supplied by the external `devops-playbook` repository.

## High-Level Layers

### 1. Experiment, Data, And Registry Layer

- mlflow/ provides experiment tracking, model registry, and metadata patterns.
- dvc/ provides data versioning, remote storage examples, and pipeline templates.
- feature-store/ provides Feast integration patterns.

### 2. CI And Governance Layer

- ci/github-actions/ provides training, evaluation, deployment, monitoring, promotion, and shared security scan workflows.
- policy/ provides model approval, data governance, and fairness controls.
- fairness/ implements Fairlearn metrics and SHAP explainability analysis.

### 3. Delivery And Runtime Layer

- cd/kubernetes/ provides base, environment, training, batch, and promotion manifests.
- cd/argo/pipelines/ provides production workflow DAGs.
- terraform/ provides cloud-specific ML infrastructure starter configurations.
- serving/ provides Triton, TorchServe, and vLLM patterns.

### 4. Operations And Cost Layer

- monitoring/ provides drift detection, alert rules, SLOs, and Grafana dashboards.
- finops/ provides ML cost attribution, budgets, alerts, and reports.
- docs/runbooks/, docs/diagrams/, docs/golden-paths/, and docs/decisions/ provide operational guidance and architecture records.

### 5. ML Lifecycle Execution Layer

- pipelines/ contains local-mode pipeline runners (training, batch inference, drift-triggered retraining) and reusable step components under pipelines/components/.
- cd/argo/pipelines/ provides Argo Workflows DAG definitions for production execution on Kubernetes.
- batch/ implements MLflow pyfunc-based batch scoring with input validation, output quality gating, and downstream notification.
- training/ implements distributed training scripts for KubeRay (primary) and Kubeflow (secondary).
- fairness/ implements Fairlearn bias metrics and SHAP explainability analysis with CI enforcement.
- All pipeline pods carry four mandatory cost labels: cost-center, team, model-name, environment.

## Reference Flow

1. Choose a golden path and version data with DVC.
2. Train and track experiments with MLflow.
3. Evaluate model quality, lineage, fairness, and approval gates in CI.
4. Promote an approved model through Kubernetes environments.
5. Serve with Triton, TorchServe, or vLLM.
6. Monitor drift and serving SLOs, and enforce FinOps controls.

## Canonical Source Areas

- docs/ for architectural and procedural guidance.
- ci/, cd/, terraform/, mlflow/, dvc/, serving/, monitoring/, policy/, and finops/ for executable patterns.

## External Platform Dependencies

`devops-playbook` supplies Kubernetes cluster provisioning, base security controls, secrets management, OIDC federation, cluster-wide observability, and incident notification integrations. These are dependencies, not local paths in this repository.

## Documentation Navigation Anchors

- ADR index: `docs/decisions/README.md`
- Runbook index and authoring standard: `docs/runbooks/README.md`
- Diagram inventory: `docs/diagrams/README.md`
- Concepts guide: `docs/guides/concepts.md`
- Integration bridge: `docs/topology/INTEGRATION-BRIDGE.md`
- Dependency matrix: `docs/topology/DEPENDENCY-MATRIX.md`
- Control plane/data plane: `docs/topology/CONTROL-PLANES.md`
- Compatibility contract: `docs/topology/COMPATIBILITY-CONTRACT.md`
- Routing quality: `docs/topology/ROUTING-QUALITY.md`
