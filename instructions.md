# 🤖 instructions.md — AI Agent Guidelines for MLOps Playbook

## 🎯 Objective
You are an AI engineering agent responsible for building out the MLOps Playbook repository into a fully functional, production-ready system.

Your goal is to:
- Implement missing modules
- Maintain modularity and scalability
- Follow best practices in MLOps
- Ensure code is clean, testable, and reproducible

---

## 🧩 General Rules

1. Always follow a modular design
2. Prefer configuration over hardcoding
3. Ensure reproducibility (seed, logging, versioning)
4. Write clean, readable, and well-documented code
5. Avoid unnecessary complexity
6. Each component should be independently testable

---

## 📁 Tasks to Implement

### 1. Data Layer
- Implement data ingestion pipeline
- Add schema validation (Great Expectations or custom)
- Support versioning (DVC-compatible structure)

### 2. Feature Engineering
- Create reusable feature pipelines
- Ensure transformations are consistent for training & inference

### 3. Training Pipeline
- Build training pipeline script
- Add MLflow logging
- Save model artifacts with versioning

### 4. Experiment Tracking
- Integrate MLflow
- Log parameters, metrics, artifacts

### 5. Inference Service
- Build FastAPI service
- Add /predict endpoint
- Load latest production model

### 6. Deployment
- Create Dockerfile (multi-stage)
- Add docker-compose support
- Prepare Kubernetes manifests (optional)

### 7. Monitoring
- Implement basic logging
- Add placeholder for drift detection (Evidently)
- Track prediction distributions

### 8. CI/CD
- Add GitHub Actions workflow:
  - Lint
  - Test
  - Train pipeline
  - Build Docker image

---

## ⚙️ Coding Standards

- Language: Python 3.12+
- Use type hints
- Follow PEP8
- Use logging instead of print
- Use virtual environments

---

## 🔁 Pipeline Requirements

Each pipeline must:
- Be config-driven
- Log outputs and metrics
- Handle failures gracefully
- Be rerunnable

---

## 🧪 Testing

- Add unit tests for core modules
- Validate pipeline execution
- Mock external dependencies

---

## 📦 Deliverables

The final system must:
- Run end-to-end locally
- Be containerized
- Be deployable
- Be observable

---

## 🚫 Avoid

- Hardcoded paths
- Monolithic scripts
- Ignoring failures
- Skipping logging

---

## ✅ Success Criteria

- Fully functional ML pipeline
- Reproducible experiments
- Deployable inference API
- Basic monitoring in place

---

## 📌 Final Instruction

Prioritize simplicity first, then scalability.

Build something that works end-to-end before optimizing.
