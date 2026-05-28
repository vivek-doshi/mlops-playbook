#!/usr/bin/env bash
set -euo pipefail

DVC_REMOTE="${1:-s3}"

echo "Bootstrapping MLOps playbook workspace"

if ! command -v dvc >/dev/null 2>&1; then
  echo "DVC not found on PATH"
fi

if ! command -v mlflow >/dev/null 2>&1; then
  echo "MLflow CLI not found on PATH"
fi

echo "Selected DVC remote: ${DVC_REMOTE}"
echo "Bootstrap complete"
