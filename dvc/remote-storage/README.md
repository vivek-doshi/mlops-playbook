# DVC Remote Storage Patterns

Store datasets and model artifacts outside Git and track pointers in the repository.

## Supported remote patterns

- S3-compatible remote: `s3.remote.sample`
- GCS remote: `gcs.remote.sample`
- Azure Blob remote: `azure.remote.sample`

## Setup pattern

1. Initialize DVC in repository root.
2. Pick a remote sample file and apply values.
3. Configure credentials through environment variables or workload identity.
4. Run `dvc push` and `dvc pull` in CI and local workflows.
