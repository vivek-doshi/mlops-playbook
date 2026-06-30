# Repository Map

Generated from current workspace structure.

- Root: d:/personal/projects/mlops-playbook
- Generated: 2026-07-01 00:19:37
- Exclusions: .ai/, .git/, .github/prompts/, .github/skills/, .kiro/, catalog/scripts/__pycache__/, finops/scripts/__pycache__/, secops/compliance/scripts/__pycache__/, website/

```text
.
├── .devcontainer
│   ├── devcontainer.json
│   └── devcontainer-lock.json
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   ├── feature_request.yml
│   │   └── model_quality_issue.yml
│   ├── workflows
│   │   └── deploy-website.yml
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
│   ├── kubernetes
│   │   ├── _base
│   │   │   ├── deployment.yaml
│   │   │   ├── kustomization.yaml
│   │   │   └── service.yaml
│   │   ├── batch
│   │   │   ├── batch-cronjob.yaml
│   │   │   └── batch-job.yaml
│   │   ├── environments
│   │   │   ├── dev
│   │   │   │   ├── kustomization.yaml
│   │   │   │   ├── network-policy.yaml
│   │   │   │   └── resource-quota.yaml
│   │   │   ├── production
│   │   │   │   ├── kustomization.yaml
│   │   │   │   ├── network-policy.yaml
│   │   │   │   └── pdb.yaml
│   │   │   └── staging
│   │   │       ├── kustomization.yaml
│   │   │       ├── network-policy.yaml
│   │   │       └── resource-quota.yaml
│   │   ├── portal
│   │   │   ├── deployment.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── network-policy.yaml
│   │   │   └── service.yaml
│   │   └── training
│   │       ├── checkpointing-pvc.yaml
│   │       ├── pytorch-job.yaml
│   │       ├── ray-job.yaml
│   │       └── tf-job.yaml
│   └── README.md
├── ci
│   ├── azure-ml
│   │   └── train-job.yaml
│   ├── dvc
│   │   └── dvc-pipeline.yml
│   ├── github-actions
│   │   ├── _shared
│   │   │   └── reusable-mlops-scan.yml
│   │   ├── batch
│   │   │   ├── batch-quality-check.yml
│   │   │   ├── scheduled-batch.yml
│   │   │   └── trigger-batch-job.yml
│   │   ├── distributed-training
│   │   │   ├── distributed-train.yml
│   │   │   └── gpu-approval-gate.yml
│   │   ├── fairness
│   │   │   └── fairness-gate.yml
│   │   ├── federated
│   │   │   ├── federated-eval.yml
│   │   │   └── federated-train.yml
│   │   ├── finops
│   │   │   ├── cost-budget-check.yml
│   │   │   ├── monthly-cost-report.yml
│   │   │   └── weekly-cost-report.yml
│   │   ├── llmops
│   │   │   ├── evaluate-llm.yml
│   │   │   ├── fine-tune.yml
│   │   │   ├── prompt-validate.yml
│   │   │   └── rlhf-train.yml
│   │   ├── model-cards
│   │   │   └── generate-card.yml
│   │   ├── model-deployment
│   │   │   └── deploy.yml
│   │   ├── model-evaluation
│   │   │   └── evaluate.yml
│   │   ├── model-monitoring
│   │   │   └── drift-check.yml
│   │   ├── model-optimization
│   │   │   ├── benchmark.yml
│   │   │   └── optimize.yml
│   │   ├── model-training
│   │   │   ├── continuous-training.yml
│   │   │   └── train.yml
│   │   ├── multi-cloud
│   │   │   ├── deploy-multicloud.yml
│   │   │   └── failover-test.yml
│   │   ├── online-learning
│   │   │   ├── online-rollback.yml
│   │   │   └── online-update.yml
│   │   ├── pipelines
│   │   │   ├── trigger-batch-inference.yml
│   │   │   └── trigger-training-pipeline.yml
│   │   └── promotion
│   │       ├── promote-dev.yml
│   │       ├── promote-production.yml
│   │       ├── promote-staging.yml
│   │       ├── promotion-gates.yml
│   │       └── rollback.yml
│   └── README.md
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
│   │   ├── ADR-ML-018-batch-inference.md
│   │   ├── ADR-ML-019-online-learning.md
│   │   ├── ADR-ML-020-multi-cloud-serving.md
│   │   ├── ADR-ML-021-model-optimization.md
│   │   ├── ADR-ML-022-llmops.md
│   │   ├── ADR-ML-023-self-service-portal.md
│   │   ├── ADR-ML-024-federated-learning.md
│   │   └── README.md
│   ├── golden-paths
│   │   ├── batch-inference.md
│   │   ├── data-versioning.md
│   │   ├── distributed-training.md
│   │   ├── experiment-tracking.md
│   │   ├── fairness-and-explainability.md
│   │   ├── federated-learning.md
│   │   ├── llmops.md
│   │   ├── ml-cost-attribution.md
│   │   ├── mlops-workflow.md
│   │   ├── model-monitoring.md
│   │   ├── model-optimization.md
│   │   ├── model-registry.md
│   │   ├── model-serving.md
│   │   ├── model-training-pipeline.md
│   │   ├── multi-cloud-serving.md
│   │   ├── multi-env-promotion.md
│   │   ├── online-learning.md
│   │   ├── pipeline-orchestration.md
│   │   └── self-service-portal.md
│   ├── guides
│   │   ├── concepts.md
│   │   ├── feature-store-patterns.md
│   │   └── gpu-cost-governance.md
│   ├── model-cards
│   │   └── fraud-detection-model-card.md
│   ├── local-setup.md
│   └── README.md
├── dvc
│   ├── pipeline-templates
│   │   └── train-eval-deploy.yaml
│   ├── remote-storage
│   │   ├── azure.remote.sample
│   │   ├── gcs.remote.sample
│   │   ├── README.md
│   │   └── s3.remote.sample
│   └── README.md
├── fairness
│   ├── evaluate.py
│   ├── explainability.py
│   └── README.md
├── feature-store
│   ├── feast
│   │   ├── feature_store.yaml
│   │   ├── README.md
│   │   └── repo.py
│   └── README.md
├── federated_learning
│   ├── aggregation
│   │   ├── __init__.py
│   │   ├── fedavg.py
│   │   └── fedprox.py
│   ├── privacy
│   │   ├── __init__.py
│   │   └── dp_wrapper.py
│   ├── __init__.py
│   ├── coordinator.py
│   ├── party.py
│   └── README.md
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
├── llmops
│   ├── evaluation
│   │   ├── benchmarks
│   │   │   ├── commonsense_qa.yaml
│   │   │   └── summarisation.yaml
│   │   ├── golden_dataset
│   │   │   └── README.md
│   │   ├── __init__.py
│   │   └── harness.py
│   ├── fine_tuning
│   │   ├── __init__.py
│   │   ├── full_fine_tune.py
│   │   ├── lora_trainer.py
│   │   ├── qlora_trainer.py
│   │   └── trainer_config.py
│   ├── prompts
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   └── schema.yaml
│   ├── rlhf
│   │   ├── __init__.py
│   │   ├── ppo_trainer.py
│   │   ├── preference_dataset.py
│   │   └── reward_model.py
│   ├── __init__.py
│   └── README.md
├── mlflow
│   ├── metadata-store
│   │   ├── client.py
│   │   ├── README.md
│   │   └── schema.sql
│   ├── model-registry
│   │   └── README.md
│   ├── tracking-server
│   │   ├── .env.example
│   │   ├── docker-compose.yml
│   │   └── README.md
│   └── README.md
├── model_optimization
│   ├── distillation
│   │   ├── student_configs
│   │   │   └── README.md
│   │   ├── __init__.py
│   │   └── trainer.py
│   ├── targets
│   │   ├── cpu.yaml
│   │   ├── cuda-a100.yaml
│   │   ├── cuda-h100.yaml
│   │   ├── triton-onnx.yaml
│   │   └── triton-trt.yaml
│   ├── __init__.py
│   ├── benchmark.py
│   ├── pipeline.py
│   ├── pruning.py
│   ├── quantisation.py
│   └── README.md
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
│   ├── multi-cloud
│   │   └── cross-cloud-alerts.yaml
│   ├── online-learning
│   │   └── online-learning-alerts.yaml
│   ├── slos
│   │   ├── _defaults.yaml
│   │   ├── README.md
│   │   ├── slo-template.yaml
│   │   └── vllm-serving-slo.yaml
│   └── README.md
├── multi_cloud_serving
│   ├── routing-config
│   │   ├── _config-schema.yaml
│   │   └── README.md
│   ├── __init__.py
│   ├── health_check.py
│   ├── README.md
│   ├── registry.py
│   └── router.py
├── online_learning
│   ├── consumers
│   │   ├── __init__.py
│   │   ├── kafka_consumer.py
│   │   ├── kinesis_consumer.py
│   │   └── pubsub_consumer.py
│   ├── __init__.py
│   ├── consumer.py
│   ├── README.md
│   ├── rollback.py
│   ├── updater.py
│   └── validator.py
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
├── portal
│   ├── backend
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── budgets.py
│   │   │   ├── deployments.py
│   │   │   ├── models.py
│   │   │   └── notifications.py
│   │   ├── __init__.py
│   │   ├── github_client.py
│   │   ├── k8s_client.py
│   │   ├── main.py
│   │   ├── mlflow_client.py
│   │   └── requirements.txt
│   ├── frontend
│   │   ├── src
│   │   │   ├── pages
│   │   │   │   ├── Budgets.tsx
│   │   │   │   ├── CostDashboard.tsx
│   │   │   │   ├── Deploy.tsx
│   │   │   │   ├── ModelDetail.tsx
│   │   │   │   └── ModelList.tsx
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── __init__.py
│   ├── Dockerfile
│   └── README.md
├── scripts
│   ├── bootstrap.ps1
│   ├── bootstrap.sh
│   ├── generate_model_card.py
│   ├── generate-repo-map.ps1
│   ├── model-card-template.md.j2
│   └── README.md
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
│   ├── azure-ml
│   │   ├── environments
│   │   │   ├── dev.tfvars
│   │   │   ├── production.tfvars
│   │   │   └── staging.tfvars
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── README.md
│   │   └── variables.tf
│   ├── gcp-vertex-ai
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── gpu-cluster
│   │   └── main.tf
│   ├── portal
│   │   └── main.tf
│   ├── ray-cluster
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── vertex-pipelines
│   │   ├── main.tf
│   │   └── variables.tf
│   └── README.md
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
