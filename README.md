🚀 MLOps Playbook

A production-ready starter template for building, deploying, and maintaining machine learning systems at scale.

📖 Overview

The MLOps Playbook is an opinionated, modular, and extensible framework designed to help engineers quickly bootstrap end-to-end machine learning systems.

It provides a structured foundation covering the entire ML lifecycle — from data ingestion to model deployment and monitoring — enabling teams to focus on solving business problems instead of setting up infrastructure from scratch.

🎯 Purpose

Building ML systems in production is significantly more complex than traditional software systems due to:

Dependency on data + code + models
Non-deterministic training workflows
Continuous retraining requirements
Model performance degradation over time

This playbook aims to:

🧩 Eliminate the “blank project” problem
⚙️ Provide reusable, production-ready templates
🔁 Standardize ML lifecycle workflows
🚀 Accelerate development and deployment of ML systems
📉 Reduce common MLOps pitfalls
🏗️ Core Principles
Modular Design – Each component can be swapped or extended independently
Reproducibility First – Experiments and pipelines are fully traceable
Production-Oriented – Designed with real-world deployment in mind
Tool-Agnostic (but opinionated) – Provides recommended stacks without locking you in
Scalable by Default – Works for both small projects and large systems
🧠 What This Playbook Covers
🔹 Data Layer
Data ingestion pipelines (batch/streaming)
Data validation & schema checks
Data versioning strategies
🔹 Experimentation
Experiment tracking
Feature engineering patterns
Reproducible training workflows
🔹 Training
End-to-end training pipelines
Hyperparameter tuning
Model versioning & registry
🔹 Deployment
Batch inference pipelines
Real-time inference APIs
Containerization & orchestration
🔹 Monitoring
Data drift detection
Model performance tracking
Alerting & observability
📂 Project Structure

mlops-playbook/
│
├── data/               # Raw & processed datasets
├── src/                # Core ML code (training, features, inference)
├── pipelines/          # Training & inference pipelines
├── models/             # Saved models & artifacts
├── outputs/            # Offline batch prediction outputs
├── experiments/        # Experiment tracking metadata & run reports
├── deployment/         # Docker, K8s, serving configs
├── monitoring/         # Drift monitoring reports & Grafana/Prometheus configs
├── configs/            # Config-driven workflows
├── notebooks/          # Exploration & prototyping notebooks
└── README.md


⚙️ Key Features
✅ Plug-and-play ML pipeline templates
✅ Built-in experiment tracking integration
✅ Production-ready API serving (FastAPI)
✅ Dockerized environment setup
✅ CI/CD-ready structure for ML workflows
✅ Monitoring hooks for drift & performance
✅ Config-driven pipeline execution
## Architecture

The standard ML pipeline flow in this repository is:
`ingest → validate → train (+ tune) → register → serve → monitor → drift alert`

🧰 Recommended Tech Stack
🟢 Beginner
Scikit-learn
FastAPI
Docker
🔵 Intermediate
MLflow (Tracking & Registry)
PyTorch / XGBoost
DVC
Airflow / Prefect
Kubernetes
Prometheus + Grafana
Evidently
🔴 Advanced (Production)
Kubeflow Pipelines
Feast (Feature Store)
KServe / Seldon

🚀 Getting Started
# Clone the repository
git clone https://github.com/vivek-doshi/mlops-playbook

# Navigate to project
cd mlops-playbook

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (one-time setup)
make pre-commit-install

# Run data ingestion pipeline
python pipelines/data_ingestion.py

# Run training pipeline (This must be run to generate model artifacts in `models/` before inference)
python pipelines/training_pipeline.py

# Or use Make to run end-to-end:
make run-all
make serve

# In another terminal, generate an experiment report and check for drift
make report
make monitor

## Docker Image

The CI pipeline automatically builds and pushes the inference image to GitHub Container Registry on every push to `main`.

```bash
# Pull the latest image
docker pull ghcr.io/vivek-doshi/mlops-playbook:latest

# Run the inference API
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  ghcr.io/vivek-doshi/mlops-playbook:latest
```

## Alternatively, using Docker
```bash
# Important: ensure training pipeline is run first to generate models in models/
python pipelines/training_pipeline.py

docker-compose up --build
```

## Monitoring

- Start the monitoring stack with `make monitoring-up` (requires Docker Compose).
- Access Grafana at `http://localhost:3000` (credentials: `admin`/`admin`). A pre-built MLOps dashboard is included out of the box.
- Prometheus scrapes `/metrics` directly from the inference API.
- Custom metrics tracked: prediction count, prediction latency, class distribution, and model load status.

## Phase 3 Features

- **Optuna Hyperparameter Tuning:** Automated hyperparameter search integrated into the training pipeline.
- **Evidently Drift Detection:** Robust drift detection monitoring that produces HTML reports.
- **Prometheus & Grafana:** Containerised observability stack with a custom ML dashboard.
- **MLflow Model Registry:** Automated promotion of models to "Production" based on configurable accuracy thresholds.
- **GHCR Docker CI/CD:** GitHub Actions workflow that automatically builds and pushes the Docker inference image to GHCR.
- **Kubernetes HPA:** HorizontalPodAutoscaler manifests with dynamic resource requests and probes.
- **Batch Prediction API:** New `/predict/batch` endpoint and an offline batch scoring pipeline.
- **Experiment Reports:** Command to automatically generate `runs_summary.md` comparing MLflow experiments.

🧪 Example Use Case

This playbook includes a reference implementation (e.g., churn prediction / fraud detection) demonstrating:

Data ingestion → preprocessing → training
Model evaluation & registration
API-based deployment
Monitoring & drift detection
⚠️ Common Pitfalls Addressed
Data leakage
Train/serve skew
Lack of reproducibility
Silent model performance degradation
Poor experiment tracking
🤝 Contribution

Contributions are welcome!

You can:

Add new templates (pipelines, deployments, monitoring)
Improve documentation
Integrate new tools/frameworks
📌 Who Is This For?
ML Engineers
Data Scientists moving to production
Backend/DevOps Engineers entering ML
Teams building scalable ML systems


📄 License
Apache 2.0

⭐ Final Note

This playbook is not just about running models — it’s about operationalizing machine learning reliably and at scale.
