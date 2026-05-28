# MLflow Tracking Server

This deployment runs a local, production-like MLflow stack using:

- PostgreSQL as backend store
- MinIO as artifact store
- MLflow server with artifact serving enabled

## Quick Start

1. Copy `.env.example` to `.env` and update secrets.
2. Start the stack:

   docker compose up -d

3. Open MLflow UI at http://localhost:5000

## Notes

- For cloud deployments, replace MinIO with managed object storage (S3/GCS/Azure Blob).
- Keep this stack behind identity-aware ingress in shared environments.
