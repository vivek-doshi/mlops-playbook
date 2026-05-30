# Makefile — MLOps Playbook developer commands
#
# USAGE:
#   make help              # Show all available targets
#   make setup             # Install all dev dependencies
#   make mlflow-up         # Start the MLflow tracking stack
#   make train             # Run the DVC training pipeline
#   make drift-check       # Run Evidently drift report
#
# PREREQUISITES:
#   Python 3.11+, Docker, docker compose, DVC, kubectl (for deploy targets)
#
# BEGINNER NOTE:
#   A Makefile is a portable task runner. Each `target:` block defines a command.
#   Dependencies between targets are expressed as: `target: dep1 dep2`.
#   Run `make <target>` to execute it.

.DEFAULT_GOAL := help
.PHONY: help setup setup-dev clean \
        mlflow-up mlflow-down mlflow-logs mlflow-ps \
        dvc-pull dvc-push dvc-status dvc-repro \
        train evaluate drift-check \
        fairness-eval fairness-explain fairness-check \
        batch-score batch-run batch-validate \
        finops-report cost-daily cost-weekly cost-monthly \
        distributed-train \
        promote-dev promote-staging rollback \
        lint format security-scan pre-commit \
        tf-fmt \
        tf-validate-sagemaker tf-validate-vertex tf-validate-azure-ml \
        tf-validate-ray-cluster tf-validate-vertex-pipelines \
        tf-validate-azure tf-plan-azure \
        tf-plan-sagemaker tf-plan-vertex tf-plan-azure-ml \
        docker-build-mlflow \
        generate-model-card \
        ci-scan

# Colours for pretty help output
CYAN  := \033[0;36m
RESET := \033[0m

## ─────────────────────────────────────────────────────────────────────────────
## Help
## ─────────────────────────────────────────────────────────────────────────────

help: ## Show this help message
	@echo ""
	@echo "  MLOps Playbook — available targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-30s$(RESET) %s\n", $$1, $$2}'
	@echo ""

## ─────────────────────────────────────────────────────────────────────────────
## Setup
## ─────────────────────────────────────────────────────────────────────────────

setup: ## Install core Python dependencies (mlflow, dvc, evidently)
	pip install --upgrade pip
	pip install \
		mlflow==2.14.2 \
		dvc[s3,gcs,azure]>=3.0 \
		evidently>=0.4 \
		pandas \
		scikit-learn \
		pyarrow \
		fairlearn>=0.10 \
		shap>=0.44 \
		matplotlib>=3.8 \
		feast \
		"pyyaml>=6.0" \
		"requests>=2.31"

setup-dev: setup ## Install dev + pre-commit hooks on top of core deps
	pip install \
		pre-commit \
		black \
		isort \
		ruff \
		bandit \
		detect-secrets \
		pytest \
		pytest-cov
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✓ Dev environment ready. Run 'make pre-commit' to verify hooks."

secrets-baseline: ## Generate initial detect-secrets baseline (run once after setup)
	detect-secrets scan \
		--exclude-files '\.lock$$' \
		--exclude-files 'dvc/remote-storage/.*\.sample$$' \
		> .secrets.baseline
	@echo "✓ .secrets.baseline created. Commit this file to the repo."

## ─────────────────────────────────────────────────────────────────────────────
## MLflow Tracking Stack  (PostgreSQL + MinIO + MLflow)
## ─────────────────────────────────────────────────────────────────────────────

MLFLOW_DIR := mlflow/tracking-server

mlflow-up: ## Start MLflow tracking stack in the background
	@echo "Starting MLflow stack (PostgreSQL + MinIO + MLflow)..."
	@test -f $(MLFLOW_DIR)/.env || (echo "ERROR: Copy $(MLFLOW_DIR)/.env.example to $(MLFLOW_DIR)/.env first." && exit 1)
	docker compose -f $(MLFLOW_DIR)/docker-compose.yml up -d
	@echo "MLflow UI  → http://localhost:5000"
	@echo "MinIO UI   → http://localhost:9001"

mlflow-down: ## Stop and remove MLflow stack containers
	docker compose -f $(MLFLOW_DIR)/docker-compose.yml down

mlflow-logs: ## Tail MLflow server logs
	docker compose -f $(MLFLOW_DIR)/docker-compose.yml logs -f mlflow

mlflow-ps: ## Show running MLflow stack containers
	docker compose -f $(MLFLOW_DIR)/docker-compose.yml ps

## ─────────────────────────────────────────────────────────────────────────────
## DVC — Data Versioning
## ─────────────────────────────────────────────────────────────────────────────

DVC_REMOTE ?= s3    # Override with: make dvc-pull DVC_REMOTE=gcs

dvc-pull: ## Pull dataset and artifacts from DVC remote
	dvc pull --remote $(DVC_REMOTE)

dvc-push: ## Push new dataset versions and artifacts to DVC remote
	dvc push --remote $(DVC_REMOTE)

dvc-status: ## Show which DVC-tracked files differ from remote
	dvc status --remote $(DVC_REMOTE)

dvc-repro: ## Reproduce the full DVC pipeline (train → evaluate → deploy-candidate)
	dvc repro

## ─────────────────────────────────────────────────────────────────────────────
## ML Pipeline — Training, Evaluation, Drift Monitoring
## ─────────────────────────────────────────────────────────────────────────────

REFERENCE_DATA ?= data/reference/train_features.parquet
CURRENT_DATA   ?= data/current/today_features.parquet
DRIFT_REPORT   ?= reports/drift_report.html
DRIFT_THRESHOLD ?= 0.3

train: dvc-pull dvc-repro ## Pull data then run DVC training pipeline
	@echo "✓ Training complete. Check MLflow UI for the run."

evaluate: ## Run standalone model evaluation (requires MLFLOW_RUN_ID env var)
	@test -n "$(MLFLOW_RUN_ID)" || (echo "ERROR: Set MLFLOW_RUN_ID before running evaluate." && exit 1)
	python pipelines/evaluate.py --run-id $(MLFLOW_RUN_ID)

drift-check: ## Run Evidently drift report against current production data
	@mkdir -p reports
	python monitoring/evidently/drift_report.py \
		--reference $(REFERENCE_DATA) \
		--current   $(CURRENT_DATA) \
		--output    $(DRIFT_REPORT) \
		--threshold $(DRIFT_THRESHOLD)
	@echo "✓ Drift report written to $(DRIFT_REPORT)"

fairness-eval: ## Run fairlearn fairness evaluation (requires MLFLOW_RUN_ID and TEST_DATA env vars)
	@test -n "$(MLFLOW_RUN_ID)" || (echo "ERROR: Set MLFLOW_RUN_ID before running fairness-eval." && exit 1)
	@mkdir -p reports/fairness
	python -m fairness.evaluate \
		--model-uri models:/$(MODEL_NAME)/$(MODEL_VERSION) \
		--test-data $(TEST_DATA) \
		--config    policy/fairness/fraud-detection-fairness.yaml \
		--report-path reports/fairness/fairness_report.json
	@echo "✓ Fairness report written to reports/fairness/fairness_report.json"

fairness-explain: ## Generate SHAP explainability report (requires TEST_DATA env var)
	@mkdir -p reports/explainability
	python -m fairness.explainability \
		--model-uri models:/$(MODEL_NAME)/$(MODEL_VERSION) \
		--test-data $(TEST_DATA) \
		--output-dir reports/explainability/
	@echo "✓ Explainability report written to reports/explainability/"

fairness-check: ## Run fairness evaluation locally (requires MLFLOW_RUN_ID + MODEL_VERSION)
	@test -n "$(MLFLOW_RUN_ID)"   || (echo "ERROR: Set MLFLOW_RUN_ID before running fairness-check." && exit 1)
	@test -n "$(MODEL_VERSION)"   || (echo "ERROR: Set MODEL_VERSION before running fairness-check." && exit 1)
	@mkdir -p reports/fairness
	python -m fairness.evaluate \
		--model-uri   models:/$(MODEL_NAME)/$(MODEL_VERSION) \
		--test-data   $(TEST_DATA) \
		--config      policy/fairness/fraud-detection-fairness.yaml \
		--report-path reports/fairness/fairness_report.json
	@echo "✓ Fairness report written to reports/fairness/fairness_report.json"

distributed-train: ## Submit a distributed Ray training job (requires CONFIG + FRAMEWORK)
	@test -n "$(CONFIG)"    || (echo "ERROR: Set CONFIG (e.g. training/config/fraud-detection.yaml)." && exit 1)
	@test -n "$(FRAMEWORK)" || (echo "ERROR: Set FRAMEWORK (e.g. pytorch or sklearn)." && exit 1)
	ray job submit --working-dir . \
		-- python training/ray/train_distributed.py --config $(CONFIG)
	@echo "✓ Distributed training job submitted. Check Ray dashboard for status."

batch-score: ## Run batch inference scorer (requires BATCH_JOB_CONFIG env var)
	@test -n "$(BATCH_JOB_CONFIG)" || (echo "ERROR: Set BATCH_JOB_CONFIG (e.g. batch/jobs/fraud-detection-batch-job.yaml)." && exit 1)
	python batch/runner/batch_scorer.py --job-config $(BATCH_JOB_CONFIG)
	@echo "✓ Batch scoring complete."

batch-run: ## Run a one-shot batch inference job locally (requires JOB_CONFIG)
	@test -n "$(JOB_CONFIG)" || (echo "ERROR: Set JOB_CONFIG (e.g. batch/jobs/fraud-detection-batch-job.yaml)." && exit 1)
	python batch/runner/batch_scorer.py --job-config $(JOB_CONFIG)
	@echo "✓ Batch inference job complete."

batch-validate: ## Validate batch job config YAML against schema
	@test -n "$(JOB_CONFIG)" || (echo "ERROR: Set JOB_CONFIG to the batch job YAML to validate." && exit 1)
	python batch/runner/input_validator.py --schema batch/jobs/_job-schema.yaml --job-config $(JOB_CONFIG)
	@echo "✓ Batch job config is valid."

finops-report: ## Generate weekly ML cost report
	@mkdir -p reports/finops
	python finops/scripts/weekly-cost-report.py \
		--output reports/finops/weekly-cost-report.json
	@echo "✓ FinOps report written to reports/finops/weekly-cost-report.json"

cost-daily: ## Run daily cost attribution
	@mkdir -p reports/finops/daily
	python finops/scripts/ml-cost-attribution.py \
		--rates-file  finops/data/instance-rates.yaml \
		--output-path reports/finops/daily/cost-attribution.json \
		--lookback-hours 24
	@echo "✓ Daily cost attribution written to reports/finops/daily/cost-attribution.json"

cost-weekly: ## Generate weekly cost report
	@mkdir -p reports/finops
	python finops/scripts/weekly-cost-report.py \
		--output reports/finops/weekly-cost-report.json
	@echo "✓ Weekly cost report written to reports/finops/weekly-cost-report.json"

cost-monthly: ## Generate monthly chargeback report
	@mkdir -p reports/finops/monthly
	python finops/scripts/monthly-cost-report.py \
		--reports-dir finops/reports/daily/ \
		--output-dir  reports/finops/monthly/ \
		--budget-dir  finops/budgets/
	@echo "✓ Monthly chargeback report written to reports/finops/monthly/"

## ─────────────────────────────────────────────────────────────────────────────
## Code Quality — Lint, Format, Security
## ─────────────────────────────────────────────────────────────────────────────

format: ## Auto-format Python code with Black + isort
	black batch/ fairness/ finops/scripts/ monitoring/ pipelines/ scripts/
	isort --profile black batch/ fairness/ finops/scripts/ monitoring/ pipelines/ scripts/

lint: ## Lint Python code with Ruff (fast flake8 replacement)
	ruff check batch/ fairness/ finops/scripts/ monitoring/ pipelines/ scripts/

security-scan: ## Run Bandit security scan on Python source files
	bandit -r batch/ fairness/ finops/scripts/ monitoring/ pipelines/ scripts/ --severity-level medium

pre-commit: ## Run all pre-commit hooks against all files
	pre-commit run --all-files

ci-scan: ## Run the reusable CI security scan locally (pip-audit + detect-secrets)
	pip-audit --output json -o reports/pip-audit.json || true
	pip-audit --format columns
	detect-secrets scan --baseline .secrets.baseline

## ─────────────────────────────────────────────────────────────────────────────
## Terraform
## ─────────────────────────────────────────────────────────────────────────────

tf-fmt: ## Format all Terraform files
	terraform fmt -recursive terraform/

tf-validate-sagemaker: ## Validate AWS SageMaker Terraform module
	cd terraform/aws-sagemaker && terraform init -backend=false && terraform validate

tf-validate-vertex: ## Validate GCP Vertex AI Terraform module
	cd terraform/gcp-vertex-ai && terraform init -backend=false && terraform validate

tf-validate-azure-ml: ## Validate Azure ML Terraform module
	cd terraform/azure-ml && terraform init -backend=false && terraform validate

tf-validate-ray-cluster: ## Validate Ray cluster Terraform module
	cd terraform/ray-cluster && terraform init -backend=false && terraform validate

tf-validate-vertex-pipelines: ## Validate Vertex Pipelines Terraform module
	cd terraform/vertex-pipelines && terraform init -backend=false && terraform validate

tf-plan-sagemaker: ## Plan AWS SageMaker Terraform changes (requires AWS creds)
	cd terraform/aws-sagemaker && terraform plan

tf-plan-vertex: ## Plan GCP Vertex AI Terraform changes (requires GCP creds)
	cd terraform/gcp-vertex-ai && terraform plan

tf-validate-azure: tf-validate-azure-ml  ## Validate Azure ML Terraform module (alias for tf-validate-azure-ml)

tf-plan-azure: ## Plan Azure ML Terraform changes (requires Azure creds)
	cd terraform/azure-ml && terraform plan

## ─────────────────────────────────────────────────────────────────────────────
## Model Promotion and Rollback
## ─────────────────────────────────────────────────────────────────────────────

promote-dev: ## Trigger dev promotion workflow via gh CLI (requires MODEL_NAME + MODEL_VERSION)
	@test -n "$(MODEL_NAME)"    || (echo "ERROR: Set MODEL_NAME before promoting." && exit 1)
	@test -n "$(MODEL_VERSION)" || (echo "ERROR: Set MODEL_VERSION before promoting." && exit 1)
	gh workflow run promote-dev.yml \
		--field model_name=$(MODEL_NAME) \
		--field model_version=$(MODEL_VERSION)
	@echo "✓ Dev promotion workflow triggered for $(MODEL_NAME) v$(MODEL_VERSION)."

promote-staging: ## Trigger staging promotion workflow via gh CLI (requires MODEL_NAME + MODEL_VERSION)
	@test -n "$(MODEL_NAME)"    || (echo "ERROR: Set MODEL_NAME before promoting." && exit 1)
	@test -n "$(MODEL_VERSION)" || (echo "ERROR: Set MODEL_VERSION before promoting." && exit 1)
	gh workflow run promote-staging.yml \
		--field model_name=$(MODEL_NAME) \
		--field model_version=$(MODEL_VERSION)
	@echo "✓ Staging promotion workflow triggered for $(MODEL_NAME) v$(MODEL_VERSION)."

rollback: ## Trigger rollback workflow (requires MODEL_NAME + ENV + REASON)
	@test -n "$(MODEL_NAME)" || (echo "ERROR: Set MODEL_NAME before rolling back." && exit 1)
	@test -n "$(ENV)"        || (echo "ERROR: Set ENV (dev|staging|production) before rolling back." && exit 1)
	@test -n "$(REASON)"     || (echo "ERROR: Set REASON for the rollback." && exit 1)
	gh workflow run rollback.yml \
		--field model_name=$(MODEL_NAME) \
		--field environment=$(ENV) \
		--field reason="$(REASON)"
	@echo "✓ Rollback workflow triggered for $(MODEL_NAME) in $(ENV)."

## ─────────────────────────────────────────────────────────────────────────────
## Model Cards
## ─────────────────────────────────────────────────────────────────────────────

generate-model-card: ## Generate a model card (requires MODEL_NAME + MODEL_VERSION)
	@test -n "$(MODEL_NAME)"    || (echo "ERROR: Set MODEL_NAME before generating model card." && exit 1)
	@test -n "$(MODEL_VERSION)" || (echo "ERROR: Set MODEL_VERSION before generating model card." && exit 1)
	python scripts/generate_model_card.py \
		--model-name    $(MODEL_NAME) \
		--model-version $(MODEL_VERSION) \
		--output-dir    docs/model-cards/
	@echo "✓ Model card written to docs/model-cards/$(MODEL_NAME)/v$(MODEL_VERSION).md"



clean: ## Remove generated reports, __pycache__, and .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf reports/
	@echo "✓ Clean complete."
