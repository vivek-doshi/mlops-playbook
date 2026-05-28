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
        lint format security-scan pre-commit \
        tf-fmt tf-validate tf-plan-sagemaker tf-plan-vertex \
        docker-build-mlflow \
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
		pyarrow

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

## ─────────────────────────────────────────────────────────────────────────────
## Code Quality — Lint, Format, Security
## ─────────────────────────────────────────────────────────────────────────────

format: ## Auto-format Python code with Black + isort
	black monitoring/ scripts/
	isort --profile black monitoring/ scripts/

lint: ## Lint Python code with Ruff (fast flake8 replacement)
	ruff check monitoring/ scripts/

security-scan: ## Run Bandit security scan on Python source files
	bandit -r monitoring/ scripts/ --severity-level medium

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

tf-plan-sagemaker: ## Plan AWS SageMaker Terraform changes (requires AWS creds)
	cd terraform/aws-sagemaker && terraform plan

tf-plan-vertex: ## Plan GCP Vertex AI Terraform changes (requires GCP creds)
	cd terraform/gcp-vertex-ai && terraform plan

## ─────────────────────────────────────────────────────────────────────────────
## Cleanup
## ─────────────────────────────────────────────────────────────────────────────

clean: ## Remove generated reports, __pycache__, and .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf reports/
	@echo "✓ Clean complete."
