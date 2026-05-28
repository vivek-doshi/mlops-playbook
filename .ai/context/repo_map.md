# Repository Map

Generated from current workspace structure.

- Root: d:/projects/mlops-playbook
- Generated: 2026-05-28 13:39:31
- Exclusions: .ai/, .git/, .github/prompts/, .github/skills/, .kiro/, catalog/scripts/__pycache__/, finops/scripts/__pycache__/, secops/compliance/scripts/__pycache__/, website/

```text
.
├── .github
│   └── copilot-instructions.md
├── ci
│   ├── dvc
│   │   └── dvc-pipeline.yml
│   └── github-actions
│       ├── model-deployment
│       │   └── deploy.yml
│       ├── model-evaluation
│       │   └── evaluate.yml
│       └── model-training
│           └── train.yml
├── docs
│   ├── golden-paths
│   │   ├── data-versioning.md
│   │   ├── experiment-tracking.md
│   │   ├── model-monitoring.md
│   │   ├── model-registry.md
│   │   ├── model-serving.md
│   │   └── model-training-pipeline.md
│   └── guides
│       ├── feature-store-patterns.md
│       └── gpu-cost-governance.md
├── dvc
│   ├── pipeline-templates
│   │   └── train-eval-deploy.yaml
│   └── remote-storage
│       ├── azure.remote.sample
│       ├── gcs.remote.sample
│       ├── README.md
│       └── s3.remote.sample
├── mlflow
│   ├── model-registry
│   │   └── README.md
│   └── tracking-server
│       ├── .env.example
│       ├── docker-compose.yml
│       └── README.md
├── monitoring
│   ├── evidently
│   └── prometheus
├── policy
│   ├── data-governance
│   └── model-approval
├── scripts
│   ├── bootstrap.ps1
│   ├── bootstrap.sh
│   └── generate-repo-map.ps1
├── serving
│   ├── torchserve
│   ├── triton
│   └── vllm
├── terraform
│   ├── aws-sagemaker
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── gcp-vertex-ai
│   │   ├── main.tf
│   │   └── variables.tf
│   └── gpu-cluster
│       └── main.tf
└── README.md
```
