.PHONY: help install ingest train train-hydra serve test lint docker-build docker-up docker-down clean clean-models run-all

PYTHON := python
PIP    := pip
CONFIG := configs/config.yaml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

pre-commit-install: ## Install pre-commit hooks into git
	pre-commit install

install: ## Install all dependencies
	$(PIP) install -r requirements.txt

ingest: ## Run data ingestion pipeline
	PYTHONPATH=. $(PYTHON) pipelines/data_ingestion.py

train: ## Run training pipeline
	PYTHONPATH=. $(PYTHON) pipelines/training_pipeline.py --config $(CONFIG)

tune: ## Run training pipeline with Optuna tuning enabled
	PYTHONPATH=. $(PYTHON) -c \
		"import yaml; c=yaml.safe_load(open('$(CONFIG)')); c['tuning']['enabled']=True; \
		open('$(CONFIG)','w').write(yaml.dump(c))"
	PYTHONPATH=. $(PYTHON) pipelines/training_pipeline.py --config $(CONFIG)

train-hydra: ## Run training pipeline with Hydra config
	PYTHONPATH=. $(PYTHON) pipelines/training_pipeline_hydra.py

serve: ## Start the inference API (requires trained model)
	PYTHONPATH=. uvicorn src.inference.api:app --reload --host 0.0.0.0 --port 8000

list-models: ## List all registered models in MLflow registry
	PYTHONPATH=. $(PYTHON) -c \
		"from mlflow import MlflowClient; \
		[print(m.name) for m in MlflowClient().search_registered_models()]"

mlflow-ui: ## Open MLflow UI (tracking server)
	mlflow ui --backend-store-uri sqlite:///mlruns.db --host 0.0.0.0 --port 5000

report: ## Generate MLflow run summary report to experiments/runs_summary.md
	PYTHONPATH=. $(PYTHON) src/utils/run_report.py

test: ## Run all tests
	PYTHONPATH=. pytest tests/ -v

lint: ## Run flake8 linter
	flake8 src/ pipelines/ tests/ monitoring/ \
		--count --max-complexity=10 --max-line-length=127 --statistics

docker-build: ## Build the Docker image
	docker build -t mlops-inference:latest .

docker-up: ## Start all services via docker-compose
	docker-compose up --build

docker-down: ## Stop all docker-compose services
	docker-compose down

monitoring-up: ## Start Prometheus + Grafana monitoring stack
	docker-compose up -d prometheus grafana
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3000 (admin/admin)"

monitoring-down: ## Stop monitoring stack
	docker-compose stop prometheus grafana

clean: ## Remove generated artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f mlops.log app.log
	rm -f mlruns.db

clean-models: ## Remove trained model artifacts (forces retrain)
	rm -f models/*.pkl models/*.joblib
	@echo "Model artifacts removed. Run 'make train' to regenerate."

run-all: ingest train ## Run full pipeline end-to-end (ingest → train)

batch-ingest-train: ingest train ## Full pipeline: ingest + train (prerequisite for batch scoring)

batch-score: ## Run batch inference directly (no API needed)
	PYTHONPATH=. $(PYTHON) pipelines/batch_inference_pipeline.py \
		--input data/raw/dataset.csv \
		--output outputs/predictions.csv \
		--direct

batch-score-api: ## Run batch inference via running API
	PYTHONPATH=. $(PYTHON) pipelines/batch_inference_pipeline.py \
		--input data/raw/dataset.csv \
		--output outputs/predictions.csv \
		--api-url http://localhost:8000

monitor: ## Run drift detection monitoring pipeline
	PYTHONPATH=. $(PYTHON) pipelines/monitoring_pipeline.py \
		--reference data/raw/dataset.csv \
		--threshold 0.3
