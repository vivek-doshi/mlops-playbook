# Self-Service Portal

The MLOps Self-Service Portal is a **read-and-trigger** web application that gives
ML engineers and data scientists a unified UI over MLflow, Kubernetes, and GitHub
Actions.  **The portal never mutates state directly** — all changes are dispatched
as GitHub Actions workflow_dispatch events.

## Architecture

```
Browser (React SPA)
    │  /mlops-portal/*
    ▼
Nginx Ingress
    │
    ▼
FastAPI backend (portal/backend/main.py)
    ├── GET  /api/models/**      → MLflow registry (read-only)
    ├── GET  /api/deployments/** → Kubernetes API (read-only)
    ├── *    /api/budgets/**     → finops/budgets/ YAML files
    ├── *    /api/notifications/** → monitoring/alerts/ YAML files
    └── POST /api/*/promote      → GitHub Actions workflow_dispatch
                                      (GitHub App token, NOT PAT)
```

## Kubernetes deployment

The portal runs as a `Deployment` in the `mlops-portal` namespace with 2 replicas.

All pod specs carry the four required cost labels:
- `cost-center: platform-engineering`
- `team: mlops`
- `model-name: portal`
- `environment: production`

Liveness and readiness probes target `GET /health`.

## Authentication

The portal requires an enterprise OIDC bearer token for every `/api/*` route.
The backend validates the JWT signature and claims using the configured issuer,
audience, and JWKS endpoint. Human authorization is group-based:

- `PORTAL_OPERATOR_GROUP` may trigger promotion and rollback workflows.
- `PORTAL_ADMIN_GROUP` may update budgets and notification configuration.

The backend uses a **GitHub App installation token** to trigger workflows after
the authenticated user is authorized. Never use a PAT. Required secrets:

| Secret | Description |
|---|---|
| `GITHUB_APP_ID` | GitHub App numeric ID |
| `GITHUB_APP_PRIVATE_KEY` | PEM private key for JWT signing |
| `GITHUB_INSTALLATION_ID` | Installation ID for the target org/repo |

Required OIDC configuration:

| Variable | Description |
|---|---|
| `OIDC_ISSUER` | Trusted token issuer URL |
| `OIDC_AUDIENCE` | API audience / client ID |
| `OIDC_JWKS_URL` | Issuer signing-key endpoint |
| `PORTAL_OPERATOR_GROUP` | Group allowed to promote or roll back |
| `PORTAL_ADMIN_GROUP` | Group allowed to change budgets and notifications |
| `ALLOWED_ORIGINS` | Comma-separated browser origins; wildcard is prohibited |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000` | MLflow server |
| `GITHUB_REPOSITORY` | — | `org/repo` for workflow dispatch |
| `GITHUB_APP_ID` | — | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY` | — | PEM key (newline-escaped) |
| `GITHUB_INSTALLATION_ID` | — | Installation ID |
| `BUDGETS_DIR` | `finops/budgets` | Budget YAML directory |
| `NOTIFICATIONS_DIR` | `monitoring/alerts` | Notification config directory |

## Local development

```bash
cd portal/backend
pip install -r requirements.txt
uvicorn portal.backend.main:app --reload --port 8080
```

Frontend:

```bash
cd portal/frontend
npm install
npm run dev
```

## Building the container

```bash
docker build -t mlops-portal:local -f portal/Dockerfile portal/
```

## Deploying to Kubernetes

```bash
kubectl apply -f cd/kubernetes/portal/
```
