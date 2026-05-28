# MLOps Playbook Repository Brief

## What This Repository Is

This repository is the ML lifecycle layer for an engineering organization using a separate platform foundation repository.
It standardizes how teams run experiments, version data, register models, serve models, and monitor drift in production.

## Integration Bridge Contract

The two repos are not islands. You create a deliberate, documented dependency.

- Platform prerequisites are consumed from `cicd-reference`.
- ML lifecycle workflows are implemented and governed here.

## Current Focus Areas

- Experiment tracking and model lineage with MLflow.
- Data and artifact versioning with DVC remote storage patterns.
- Promotion gates from model evaluation to registry and deployment.
- Serving patterns for Triton, TorchServe, and vLLM.
- Drift and performance monitoring with Evidently and Prometheus.

## Target Audience

- ML platform engineers building reusable lifecycle standards.
- Applied ML teams shipping reproducible training and deployment pipelines.
- DevOps and SRE teams integrating ML services with production controls.
- Governance teams enforcing model approval and data policy boundaries.

## Key Repository Domains

- `docs/`: golden paths and guides for MLOps operations.
- `ci/`: train, evaluate, and deploy workflow templates.
- `terraform/`: cloud-specific AI service starter configurations.
- `mlflow/`: tracking server and registry integration patterns.
- `dvc/`: remote storage and pipeline templates.
- `serving/`: runtime serving stacks.
- `monitoring/`: drift and metrics integration points.
- `policy/`: model-approval and data-governance controls.

## Suggested Navigation

1. Read `README.md` for integration boundary and prerequisites.
2. Start from `docs/golden-paths/`.
3. Configure MLflow and DVC.
4. Wire CI train/evaluate/deploy with approval gates.