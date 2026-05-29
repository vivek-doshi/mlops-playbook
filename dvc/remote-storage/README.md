# DVC Remote Storage Patterns

Store datasets and model artifacts outside Git and track pointers in the repository.

## Supported remote patterns

| Cloud | Sample file | Auth method |
|---|---|---|
| AWS S3 | `s3.remote.sample` | IAM role / access key |
| GCP Cloud Storage | `gcs.remote.sample` | Workload Identity / service account key |
| Azure Blob Storage (ADLS Gen2) | `azure.remote.sample` | Managed Identity (recommended) / SAS token / connection string |

## Setup pattern

1. Initialize DVC in repository root.
2. Pick a remote sample file and apply values.
3. Configure credentials through environment variables or workload identity.
4. Run `dvc push` and `dvc pull` in CI and local workflows.
