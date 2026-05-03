# Understanding the Repository Structure

This repository is designed to simulate a production-ready Machine Learning system. It separates concerns into clear, logical folders so that data engineers, ML engineers, and data scientists can collaborate effectively.

Here is a breakdown of what each folder does in the MLOps lifecycle:

## `configs/`
**Purpose:** Configuration Management.
Instead of hardcoding file paths, model hyperparameters, or database connection strings in the Python code, all customizable settings live here. This allows you to change the behavior of the entire system (like turning hyperparameter tuning on or off) just by editing a YAML file.

## `data/`
**Purpose:** Data Storage.
This is where raw datasets (pulled from external sources) and processed datasets (ready for training) reside locally. In a real cloud environment, these files would typically reside in an S3 bucket or Google Cloud Storage, but having a local folder is useful for testing.

## `deployment/`
**Purpose:** Infrastructure as Code.
When a model is ready for the real world, it needs to be containerized and orchestrated. This folder contains Dockerfiles, Kubernetes manifests, or other configuration files required to run the APIs and services in a staging or production environment.

## `experiments/`
**Purpose:** Metadata and Run Reports.
Experiment tracking is vital in MLOps. This directory might contain SQLite databases for local MLflow tracking, run logs, or generated markdown reports that summarize different training experiments (so you know *why* a certain model was chosen).

## `models/`
**Purpose:** Artifact Storage.
After a model is trained, the physical files (like `.pkl` or `.onnx` files) are saved here. The inference APIs will look into this folder to load the model into memory. In a large system, this folder is replaced by a formal Model Registry (like MLflow Registry or AWS SageMaker).

## `monitoring/`
**Purpose:** Observability.
Once deployed, models degrade over time as real-world data changes (data drift). This folder contains configurations for tools like Prometheus, Grafana, and Evidently AI, which track model predictions, latency, and data distributions to alert you when retraining is needed.

## `notebooks/`
**Purpose:** Prototyping and Exploration.
Jupyter notebooks are great for data exploration (EDA), quickly testing new features, or visualizing data. However, code here is considered "draft" code. Production code must be migrated to the `src/` and `pipelines/` folders.

## `pipelines/`
**Purpose:** The Execution Glue.
These are executable scripts (`data_ingestion.py`, `training_pipeline.py`) that tie everything together. They pull configurations from `configs/`, call functions from `src/`, log metrics to `experiments/`, and save artifacts to `models/`. Think of them as the orchestrators of the ML lifecycle.

## `src/`
**Purpose:** Core Reusable Code.
This is the heart of the repository. It contains clean, well-tested Python modules that perform specific tasks.
*   **`src/data/`**: Logic for fetching, cleaning, and validating data (using Pydantic schemas).
*   **`src/features/`**: Feature engineering pipelines (handling missing values, scaling, encoding).
*   **`src/inference/`**: FastAPI endpoints that load the trained model and serve predictions.
*   **`src/models/`**: The actual algorithms (Random Forest, XGBoost) and training loops.
*   **`src/utils/`**: Helper functions like custom loggers or report generators.
