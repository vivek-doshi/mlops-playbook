# Repository Map

Generated from current workspace structure.

- Root: d:/projects/mlops-playbook
- Generated: 2026-05-30 00:22:59
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
├── batch
│   ├── jobs
│   │   ├── _job-schema.yaml
│   │   └── README.md
│   ├── runner
│   │   ├── batch_scorer.py
│   │   ├── downstream_notifier.py
│   │   ├── input_validator.py
│   │   └── output_quality_gate.py
│   └── README.md
├── cd
│   ├── argo
│   │   └── pipelines
│   │       ├── batch-inference-workflow.yaml
│   │       └── training-workflow.yaml
│   └── kubernetes
│       ├── _base
│       │   ├── deployment.yaml
│       │   ├── kustomization.yaml
│       │   └── service.yaml
│       ├── batch
│       │   ├── batch-cronjob.yaml
│       │   └── batch-job.yaml
│       ├── environments
│       │   ├── dev
│       │   │   ├── kustomization.yaml
│       │   │   ├── network-policy.yaml
│       │   │   └── resource-quota.yaml
│       │   ├── production
│       │   │   ├── kustomization.yaml
│       │   │   ├── network-policy.yaml
│       │   │   └── pdb.yaml
│       │   └── staging
│       │       ├── kustomization.yaml
│       │       ├── network-policy.yaml
│       │       └── resource-quota.yaml
│       └── training
│           ├── checkpointing-pvc.yaml
│           ├── pytorch-job.yaml
│           ├── ray-job.yaml
│           └── tf-job.yaml
├── ci
│   ├── dvc
│   │   └── dvc-pipeline.yml
│   └── github-actions
│       ├── _shared
│       │   └── reusable-mlops-scan.yml
│       ├── batch
│       │   ├── batch-quality-check.yml
│       │   ├── scheduled-batch.yml
│       │   └── trigger-batch-job.yml
│       ├── distributed-training
│       │   ├── distributed-train.yml
│       │   └── gpu-approval-gate.yml
│       ├── fairness
│       │   └── fairness-gate.yml
│       ├── finops
│       │   ├── cost-budget-check.yml
│       │   ├── monthly-cost-report.yml
│       │   └── weekly-cost-report.yml
│       ├── model-deployment
│       │   └── deploy.yml
│       ├── model-evaluation
│       │   └── evaluate.yml
│       ├── model-monitoring
│       │   └── drift-check.yml
│       ├── model-training
│       │   ├── continuous-training.yml
│       │   └── train.yml
│       ├── pipelines
│       │   ├── trigger-batch-inference.yml
│       │   └── trigger-training-pipeline.yml
│       └── promotion
│           ├── promote-dev.yml
│           ├── promote-production.yml
│           ├── promote-staging.yml
│           ├── promotion-gates.yml
│           └── rollback.yml
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
│   │   ├── ADR-ML-009-pre-commit-toolchain.md
│   │   ├── ADR-ML-014-multi-env-strategy.md
│   │   ├── ADR-ML-015-fairness-framework.md
│   │   ├── ADR-ML-016-distributed-training.md
│   │   ├── ADR-ML-017-pipeline-orchestration.md
│   │   └── ADR-ML-018-batch-inference.md
│   ├── golden-paths
│   │   ├── batch-inference.md
│   │   ├── data-versioning.md
│   │   ├── distributed-training.md
│   │   ├── experiment-tracking.md
│   │   ├── fairness-and-explainability.md
│   │   ├── ml-cost-attribution.md
│   │   ├── mlops-workflow.md
│   │   ├── model-monitoring.md
│   │   ├── model-registry.md
│   │   ├── model-serving.md
│   │   ├── model-training-pipeline.md
│   │   ├── multi-env-promotion.md
│   │   └── pipeline-orchestration.md
│   ├── guides
│   │   ├── feature-store-patterns.md
│   │   └── gpu-cost-governance.md
│   ├── model-cards
│   │   └── fraud-detection-model-card.md
│   └── local-setup.md
├── dvc
│   ├── pipeline-templates
│   │   └── train-eval-deploy.yaml
│   └── remote-storage
│       ├── azure.remote.sample
│       ├── gcs.remote.sample
│       ├── README.md
│       └── s3.remote.sample
├── fairness
│   ├── evaluate.py
│   ├── explainability.py
│   └── README.md
├── feature-store
│   └── feast
│       ├── feature_store.yaml
│       ├── README.md
│       └── repo.py
├── finops
│   ├── alerts
│   │   └── ml-cost-alerts.yaml
│   ├── budgets
│   │   └── _budget-schema.yaml
│   ├── dashboards
│   │   └── ml-cost-attribution.json
│   ├── data
│   │   └── instance-rates.yaml
│   ├── reports
│   │   └── README.md
│   ├── scripts
│   │   ├── ml-cost-attribution.py
│   │   ├── monthly-cost-report.py
│   │   └── weekly-cost-report.py
│   └── README.md
├── mlflow
│   ├── metadata-store
│   │   ├── client.py
│   │   ├── README.md
│   │   └── schema.sql
│   ├── model-registry
│   │   └── README.md
│   └── tracking-server
│       ├── .env.example
│       ├── docker-compose.yml
│       └── README.md
├── monitoring
│   ├── alerts
│   │   └── drift-alerts.yaml
│   ├── batch
│   │   └── batch-alerts.yaml
│   ├── dashboards
│   │   ├── model-health.json
│   │   └── README.md
│   ├── evidently
│   │   ├── drift_report.py
│   │   └── README.md
│   ├── fairness
│   │   └── fairness-alerts.yaml
│   ├── prometheus
│   ├── slos
│   │   └── vllm-serving-slo.yaml
│   └── README.md
├── pipelines
│   ├── components
│   │   ├── data_ingestion
│   │   │   └── component.py
│   │   ├── deployment
│   │   │   └── component.py
│   │   ├── evaluation
│   │   │   └── component.py
│   │   ├── preprocessing
│   │   │   └── component.py
│   │   ├── registration
│   │   │   └── component.py
│   │   └── training
│   │       └── component.py
│   ├── batch_inference_pipeline.py
│   ├── README.md
│   ├── retraining_pipeline.py
│   └── training_pipeline.py
├── policy
│   ├── data-governance
│   │   ├── pii-model-checklist.md
│   │   └── README.md
│   ├── environments
│   │   ├── dev-policy.yaml
│   │   ├── production-policy.yaml
│   │   └── staging-policy.yaml
│   ├── fairness
│   │   ├── _fairness-config-schema.yaml
│   │   ├── example-fairness-config.yaml
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
│   │   ├── README.md
│   │   └── shadow-deployment.yaml
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
│   ├── gpu-cluster
│   │   └── main.tf
│   ├── ray-cluster
│   │   ├── main.tf
│   │   └── variables.tf
│   └── vertex-pipelines
│       ├── main.tf
│       └── variables.tf
├── training
│   ├── kubeflow
│   │   ├── train_pytorch.py
│   │   └── train_tf.py
│   ├── ray
│   │   ├── checkpoint_callback.py
│   │   └── train_distributed.py
│   └── README.md
├── .pre-commit-config.yaml
├── GETTING_STARTED.md
├── Makefile
├── README.md
└── Taskfile.yml
```
