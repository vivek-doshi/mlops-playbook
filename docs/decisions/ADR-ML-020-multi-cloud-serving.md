# ADR-ML-020 — Multi-Cloud Model Serving Strategy

| Field       | Value                                                   |
|-------------|----------------------------------------------------------|
| ID          | ADR-ML-020                                               |
| Status      | Accepted                                                 |
| Date        | 2025-05-30                                               |
| Deciders    | Platform Engineering, ML Engineering, FinOps            |

---

## Context

The organisation serves ML models in production and has active workloads on all
three hyperscalers (AWS, GCP, Azure).  Current state:

- AWS SageMaker hosts the majority of online models.
- GCP Vertex AI is used by one product team.
- Azure ML was introduced via `terraform/azure-ml/` in Phase 2.

Single-cloud serving creates several risks:

1. **Availability**: a single cloud outage takes all inference offline.
2. **Vendor lock-in**: pricing leverage, egress costs, and API constraints grow over time.
3. **Latency**: users in different regions are served from a single geography.
4. **Cost optimisation**: spot pricing and committed-use discounts vary across clouds;
   dynamic traffic shifting can reduce cost by 20–40%.

---

## Decision

### Architecture: Weighted Traffic Routing with Automatic Failover

Implement a lightweight Python traffic router (`multi_cloud_serving/router.py`) that:

1. Reads per-model traffic weights from `routing-config/<model-name>.yaml`.
2. Routes requests using weighted random selection.
3. Tracks rolling 2-minute error rate per endpoint.
4. Triggers automatic failover when any endpoint's error rate exceeds **5%** for
   **2 consecutive minutes**, redistributing its traffic proportionally.

### Endpoint Registration

Endpoint URLs are read from Terraform output files — never hardcoded in Python
source or YAML configs.  The `EndpointRegistry` class reads:

- `terraform/aws-sagemaker/outputs.json` → SageMaker endpoint URLs
- `terraform/gcp-vertex-ai/outputs.json` → Vertex AI endpoint URLs
- `terraform/azure-ml/outputs.json` → Azure ML endpoint URLs

### Health Probing

Each cloud has a native health probe:

| Cloud | Probe method |
|---|---|
| AWS SageMaker | `GET /ping` → 200 |
| GCP Vertex AI | `GET /v1/endpoints/<id>` with GCP ADC token |
| Azure ML | `POST /score` with Azure DefaultCredential (200 or 400 = healthy) |

Health checks run every **30 seconds**.

### Cost Normalisation

All per-1000-prediction cost data is stored in `finops/data/instance-rates.yaml`
under keys `sagemaker_cost_per_1k`, `vertex_cost_per_1k`, `azure_cost_per_1k`.
The FinOps dashboard (Phase 2) aggregates these to show cross-cloud cost comparison.

---

## Alternatives Considered

### A: Global HTTP load balancer (Cloudflare / AWS Global Accelerator)

**Rejected**: adds infrastructure dependency not owned by ML Platform.  Routing
logic would live outside the ML codebase, making it hard to version alongside model
configs.  Added cost (~$0.005/10k requests) unwarranted at current scale.

### B: Istio service mesh for cross-cluster traffic

**Rejected**: requires multi-cluster Istio setup across three clouds — significant
operational overhead and not part of the existing Platform layer.

### C: MLflow-native multi-endpoint serving

**Rejected**: MLflow does not have native multi-cloud traffic routing; wrapping it
would require forking MLflow serving internals.

---

## Consequences

**Positive**:
- Automatic failover reduces MTTR for cloud-level incidents.
- Traffic weights are version-controlled YAML — easy to review, audit, and roll back.
- No new infrastructure is required; runs as a Python library called from existing
  serving code.
- Chaos test workflow (`failover-test.yml`) validates failover before each release.

**Negative / Risks**:
- Router is in-process with the calling service — not a dedicated sidecar.  A
  crash in the calling service takes the router down too.
- `EndpointRegistry` depends on Terraform outputs existing locally at deploy time.
  CI jobs must run `terraform output -json` before starting the router.
- Multi-cloud adds three times the monitoring surface area.

---

## Related Decisions

- [ADR-ML-003](ADR-ML-003-model-serving.md) — Three-Runtime Serving Strategy
- [ADR-ML-006](ADR-ML-006-infrastructure-terraform.md) — Terraform for Infrastructure
- [ADR-ML-017](ADR-ML-017-pipeline-orchestration.md) — Pipeline Orchestration
