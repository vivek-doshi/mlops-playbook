# Terraform Infrastructure Modules for MLOps

## Purpose and Scope

This folder contains infrastructure-as-code modules for cloud ML platforms and supporting runtime components.
It provides reproducible provisioning patterns for multi-cloud training, serving, portal, and pipeline infrastructure.

## Folder Structure

- `aws-sagemaker/`: AWS SageMaker infrastructure for training and serving
- `azure-ml/`: Azure ML workspace and environment patterns (with env tfvars)
- `gcp-vertex-ai/`: Vertex AI infrastructure foundations
- `vertex-pipelines/`: Pipeline-specific infra for Vertex orchestration
- `gpu-cluster/`: GPU compute cluster infrastructure
- `ray-cluster/`: Ray cluster infrastructure for distributed workloads
- `portal/`: Portal-supporting cloud infrastructure

## How to Use This as an Individual Component

1. **Select a module directory**, for example `terraform/azure-ml`
2. **Initialize Terraform in that directory**: `terraform init`
3. **Select variables (`*.tfvars`) and review plan**:
   - `terraform plan -var-file=environments/dev.tfvars`
4. **Apply changes**:
   - `terraform apply -var-file=environments/dev.tfvars`
5. **Use separate state/workspaces per environment to avoid cross-environment drift**

## Inputs and Outputs

- **Inputs**: Cloud credentials, region/subscription settings, environment variables
- **Outputs**: Provisioned cloud resources required by CI/CD and runtime ML components

## Related Resources

- Golden paths: See [docs/golden-paths/](../docs/golden-paths/)
- CI workflows: See [ci/github-actions/](../ci/github-actions/)
- CD workflows: See [cd/argo/pipelines/](../cd/argo/pipelines/)
