# MLOps Maturity Roadmap

The repository is a reference implementation with a staged path to production
operability.

## P0: release safety

- Fail-closed promotion and exact lineage validation.
- Enterprise authentication, authorization, explicit CORS, and portal audit logs.
- Pull-request tests for Python behavior, policies, and manifests.

## P1: enterprise hardening

- Immutable image digests, dependency locks, SBOMs, signing, and build provenance.
- OpenLineage events and OpenTelemetry telemetry.
- Data quality, schema, feature freshness, and label-delay gates.
- AI risk classification, model inventory, and recovery evidence.

## P2: scale and optimization

- Canary or blue/green delivery with automated rollback.
- Champion/challenger and shadow evaluation.
- Tenant isolation, quota enforcement, and cost attribution.
- Model and artifact expiry policies with evidence retention.
- Production validation for each advanced domain.

The repository now contains the contracts and starter controls for these phases;
staging execution and signed operational evidence remain deployment responsibilities.

Use [production-readiness.md](production-readiness.md) as the acceptance checklist.
