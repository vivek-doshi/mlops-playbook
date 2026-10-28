# MLOps Disaster Recovery Standard

## Recovery objectives

Each production service must document an RTO and RPO before release.

| Component | Example RTO | Example RPO | Recovery evidence |
|---|---:|---:|---|
| MLflow metadata and registry | 4 hours | 1 hour | restore test and registry integrity check |
| DVC/object storage | 4 hours | 1 hour | object restore and hash verification |
| Feature store | 2 hours | 15 minutes | point-in-time or snapshot restore |
| Serving runtime | 30 minutes | 0-15 minutes | redeploy from signed image and model digest |
| Monitoring and alerts | 4 hours | 1 hour | dashboard and alert restore |
| Portal | 1 hour | 15 minutes | authenticated health and workflow-dispatch test |

Values must be replaced with business-approved targets for each workload.

## Required exercises

1. Restore MLflow metadata and verify registered model versions.
2. Restore the DVC/object-storage reference dataset and verify hashes.
3. Redeploy a signed serving image and immutable model artifact.
4. Verify SLO dashboards, alerts, and notification routes.
5. Execute rollback and confirm the previous model serves traffic.
6. Record duration, gaps, owners, and remediation dates.

The weekly multi-cloud failover workflow is a test trigger, not proof of recovery.
Recovery evidence must be retained as a CI artifact or incident record.
