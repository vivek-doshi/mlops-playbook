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

train-hydra: ## Run training pipeline with Hydra config
	PYTHONPATH=. $(PYTHON) pipelines/training_pipeline_hydra.py

serve: ## Start the inference API (requires trained model)
	PYTHONPATH=. uvicorn src.inference.api:app --reload --host 0.0.0.0 --port 8000

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

clean: ## Remove generated artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f mlops.log app.log
	rm -f mlruns.db

clean-models: ## Remove trained model artifacts (forces retrain)
	rm -f models/*.pkl models/*.joblib
	@echo "Model artifacts removed. Run 'make train' to regenerate."

run-all: ingest train ## Run full pipeline end-to-end (ingest → train)
