Param(
    [string]$DvcRemote = "s3"
)

Write-Host "Bootstrapping MLOps playbook workspace"

if (-not (Get-Command dvc -ErrorAction SilentlyContinue)) {
    Write-Host "DVC not found on PATH"
}

if (-not (Get-Command mlflow -ErrorAction SilentlyContinue)) {
    Write-Host "MLflow CLI not found on PATH"
}

Write-Host "Selected DVC remote: $DvcRemote"
Write-Host "Bootstrap complete"
