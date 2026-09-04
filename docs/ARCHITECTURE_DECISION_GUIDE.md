# Architecture Decision Guide

## Purpose and Scope

This guide documents architectural decisions made for the MLOps platform, including:

- **Model Training**: Distributed training patterns, checkpoint strategies, and resource allocation
- **Serving Architecture**: Triton, TorchServe, vLLM, and multi-cloud serving patterns
- **Pipeline Orchestration**: CI/CD workflows, Argo-based execution, and Kubernetes manifests
- **Data Governance**: Fairness, explainability, federated learning, and privacy patterns
- **Monitoring & FinOps**: Drift detection, cost attribution, and operational dashboards

## Key Architectural Patterns

### Training Patterns

- **Distributed Training**: Ray, PyTorchJob, and TFJob orchestration
- **Checkpoint Management**: Periodic saves with distributed coordination
- **Resource Allocation**: GPU cluster provisioning and workload scheduling

### Serving Architecture

- **Model Serving**: Triton, TorchServe, and vLLM deployment patterns
- **Multi-Cloud Serving**: AWS SageMaker, Azure ML, and GCP Vertex AI
- **Inference Patterns**: Batch inference, online serving, and multi-cloud routing

### Pipeline Orchestration

- **CI Workflows**: GitHub Actions templates for training, evaluation, and promotion
- **CD Workflows**: Argo pipelines and Kubernetes manifests for deployment
- **Pipeline Templates**: DVC-based training pipelines with promotion gates

### Data Governance

- **Fairness & Explainability**: Fairlearn metrics and SHAP-based analysis
- **Federated Learning**: Privacy-preserving distributed training
- **Privacy Patterns**: Differential privacy and secure aggregation

### Monitoring & FinOps

- **Drift Detection**: Evidently-based monitoring and Prometheus integration
- **Cost Attribution**: ML-cost-attribution dashboards and budget controls
- **Operational Dashboards**: Multi-cloud monitoring and alerting

## Decision History

Recent decisions include:

- **2026-08**: MLOps-specific routing manifest created
- **2026-08**: Platform capabilities marked as external dependencies
- **2026-08**: Integration bridge principles established

## Related Resources

- Golden paths: See [mlops-workflow.md](mlops-workflow.md) for end-to-end workflows
- CI workflows: See [ci/github-actions/](../ci/github-actions/)
- CD workflows: See [cd/argo/pipelines/](../cd/argo/pipelines/)
- Infrastructure: See [terraform/](../terraform/)
