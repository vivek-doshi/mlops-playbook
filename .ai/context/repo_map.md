# Repository Map

Generated from current workspace structure.

- Root: d:/projects/mlops-playbook
- Generated: 2026-05-28 14:24:04
- Exclusions: .ai/, .git/, .github/prompts/, .github/skills/, .kiro/, catalog/scripts/__pycache__/, finops/scripts/__pycache__/, secops/compliance/scripts/__pycache__/, website/

```text
.
├── .github
│   ├── copilot-instructions.md
│   └── copilot-instructions-mlops.md
├── ci
│   ├── dvc
│   │   └── dvc-pipeline.yml
│   └── github-actions
│       ├── _shared
│       │   └── reusable-mlops-scan.yml
│       ├── model-deployment
│       │   └── deploy.yml
│       ├── model-evaluation
│       │   └── evaluate.yml
│       ├── model-monitoring
│       │   └── drift-check.yml
│       └── model-training
│           └── train.yml
├── docs
│   ├── decisions
│   │   ├── ADR-ML-001-experiment-tracking.md
│   │   ├── ADR-ML-002-data-versioning.md
│   │   └── ADR-ML-003-model-serving.md
│   ├── golden-paths
│   │   ├── data-versioning.md
│   │   ├── experiment-tracking.md
│   │   ├── mlops-workflow.md
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
│   ├── alerts
│   │   └── drift-alerts.yaml
│   ├── dashboards
│   │   ├── model-health.json
│   │   └── README.md
│   ├── evidently
│   │   ├── drift_report.py
│   │   └── README.md
│   ├── prometheus
│   └── README.md
├── policy
│   ├── data-governance
│   │   ├── pii-model-checklist.md
│   │   └── README.md
│   ├── model-approval
│   │   ├── approved-versions.yaml
│   │   └── README.md
│   └── README.md
├── scripts
│   ├── bootstrap.ps1
│   ├── bootstrap.sh
│   └── generate-repo-map.ps1
├── serving
│   ├── torchserve
│   │   ├── config.properties
│   │   └── README.md
│   ├── triton
│   │   ├── config.pbtxt.example
│   │   └── README.md
│   ├── vllm
│   │   ├── docker-compose.yml
│   │   └── README.md
│   └── README.md
├── terraform
│   ├── aws-sagemaker
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── gcp-vertex-ai
│   │   ├── main.tf
│   │   └── variables.tf
│   └── gpu-cluster
│       └── main.tf
├── GETTING_STARTED.md
└── README.md
```
