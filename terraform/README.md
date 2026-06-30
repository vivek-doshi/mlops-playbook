# Terraform Infrastructure Modules

## What this folder does

This folder contains infrastructure-as-code modules for cloud ML platforms and supporting runtime components.
It provides reproducible provisioning patterns for multi-cloud training, serving, portal, and pipeline infrastructure.

## Folder description and details

- `aws-sagemaker/`: AWS SageMaker-related infrastructure.
- `azure-ml/`: Azure ML workspace and environment patterns (with env tfvars).
- `gcp-vertex-ai/`: Vertex AI infrastructure foundations.
- `vertex-pipelines/`: pipeline-specific infra for Vertex orchestration.
- `gpu-cluster/`: GPU compute cluster infrastructure.
- `ray-cluster/`: Ray cluster infrastructure for distributed workloads.
- `portal/`: portal-supporting cloud infrastructure.

## How to use this as an individual component

1. Select a module directory, for example `terraform/azure-ml`.
2. Initialize Terraform in that directory: `terraform init`.
3. Select variables (`*.tfvars`) and review plan:
   - `terraform plan -var-file=environments/dev.tfvars`
4. Apply changes:
   - `terraform apply -var-file=environments/dev.tfvars`
5. Use separate state/workspaces per environment to avoid cross-environment drift.

## Inputs and outputs

- Inputs: cloud credentials, region/subscription settings, environment variables.
- Outputs: provisioned cloud resources required by CI/CD and runtime ML components.
