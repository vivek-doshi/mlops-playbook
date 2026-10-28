# Repository Scripts

## What this folder does

This folder contains utility scripts for local bootstrap, documentation generation, and model-card automation.
These scripts are designed to be used independently from pipelines when teams need quick operational tasks.

## Folder description and details

- `bootstrap.ps1` / `bootstrap.sh`: local environment bootstrap for Windows/Linux.
- `generate_model_card.py`: model card generation helper.
- `model-card-template.md.j2`: Jinja template used by model card generation.
- `generate-repo-map.ps1`: regenerates repository map documentation under `.ai/context/`.

## How to use this as an individual component

1. Run bootstrap:
   - Windows: `./scripts/bootstrap.ps1`
   - Linux/macOS: `./scripts/bootstrap.sh`
2. Generate a model card using the template and structured metadata input.
3. Regenerate repository map after adding new repository files:
   - `./scripts/generate-repo-map.ps1`

## Inputs and outputs

- Inputs: local environment, model metadata, repository file structure.
- Outputs: initialized developer setup, generated model cards, updated repository map docs.
