# Data Version Control (DVC)

## What this folder does

This folder provides DVC templates and remote-storage examples for reproducible ML pipelines.
It helps teams version data and model artifacts independently from source code while preserving lineage.

## Folder description and details

- `pipeline-templates/`: reusable DVC pipeline definitions for train-eval-deploy flow.
- `remote-storage/`: sample remote backends (`s3`, `gcs`, `azure`) for DVC artifact storage.

## How to use this as an individual component

1. Initialize DVC in your project root: `dvc init`.
2. Use a remote sample from `dvc/remote-storage/` as a starting point.
3. Configure your remote in `.dvc/config` (or `.dvc/config.local` for secrets).
4. Adapt `dvc/pipeline-templates/train-eval-deploy.yaml` to your command graph.
5. Run pipeline stages:
   - `dvc repro`
   - `dvc push`
   - `dvc pull`

## Inputs and outputs

- Inputs: datasets, feature artifacts, model outputs, stage commands.
- Outputs: reproducible pipelines, versioned artifacts, and portable lineage metadata.
