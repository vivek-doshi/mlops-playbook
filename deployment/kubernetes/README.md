# Kubernetes Deployment

## Prerequisites
- kubectl configured against your cluster
- Image pushed to GHCR (handled by CI on main push)

## Deploy

```bash
# Update image tag in deployment.yaml to match your GHCR image
kubectl apply -f deployment/kubernetes/deployment.yaml

# Verify pods are running
kubectl get pods -l app=mlops-inference

# Check HPA status
kubectl get hpa mlops-inference-hpa

# Watch scaling in action
kubectl get hpa mlops-inference-hpa -w
```

## HPA Behaviour
- Scales between 1–6 replicas
- Scale-up triggers at 60% average CPU utilisation
- Scale-up adds max 2 pods per 60s (prevents thrashing)
- Scale-down waits 5 minutes before removing pods (prevents premature scale-down)
- readinessProbe on `/readiness` ensures no traffic is routed to pods with unloaded models
