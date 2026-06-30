# Feature Store

## What this folder does

This folder contains feature store assets used to define, register, and serve ML features.
It currently focuses on Feast-based configuration and repository structure.

## Folder description and details

- `feast/feature_store.yaml`: core Feast project configuration.
- `feast/repo.py`: feature view and entity definitions.
- `feast/README.md`: Feast-specific setup and usage details.

## How to use this as an individual component

1. Install Feast in your environment.
2. Move to `feature-store/feast/`.
3. Register/apply feature definitions: `feast apply`.
4. Materialize features for serving windows as needed: `feast materialize <start> <end>`.
5. Query features from training/inference services via Feast SDK.

## Inputs and outputs

- Inputs: feature definitions, source mappings, materialization windows.
- Outputs: registered feature views and online/offline feature availability for consumers.
