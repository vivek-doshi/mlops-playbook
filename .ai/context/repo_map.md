# Repository Map

Generated from current workspace structure.

- Root: d:/projects/mlops-playbook
- Generated: 2026-05-28 15:00:55
- Exclusions: .ai/, .git/, .github/prompts/, .github/skills/, .kiro/, catalog/scripts/__pycache__/, finops/scripts/__pycache__/, secops/compliance/scripts/__pycache__/, website/

```text
.
├── .devcontainer
│   └── devcontainer.json
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   ├── feature_request.yml
│   │   └── model_quality_issue.yml
│   ├── CODEOWNERS
│   ├── copilot-instructions.md
│   ├── dependabot.yml
│   └── PULL_REQUEST_TEMPLATE.md
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
│   │   ├── ADR-ML-003-model-serving.md
│   │   ├── ADR-ML-004-drift-monitoring.md
│   │   ├── ADR-ML-005-ci-cd-platform.md
│   │   ├── ADR-ML-006-infrastructure-terraform.md
│   │   ├── ADR-ML-007-dev-container.md
│   │   ├── ADR-ML-008-model-approval-policy.md
│   │   └── ADR-ML-009-pre-commit-toolchain.md
│   ├── golden-paths
│   │   ├── data-versioning.md
│   │   ├── experiment-tracking.md
│   │   ├── mlops-workflow.md
│   │   ├── model-monitoring.md
│   │   ├── model-registry.md
│   │   ├── model-serving.md
│   │   └── model-training-pipeline.md
│   ├── guides
│   │   ├── feature-store-patterns.md
│   │   └── gpu-cost-governance.md
│   └── local-setup.md
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
├── .pre-commit-config.yaml
├── GETTING_STARTED.md
├── Makefile
├── README.md
└── Taskfile.yml
```
