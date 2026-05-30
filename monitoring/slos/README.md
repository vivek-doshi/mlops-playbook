# SLO Authoring Guide

This directory contains PrometheusRule manifests that define Service Level
Objectives (SLOs) for deployed ML model endpoints.

## What is an SLO?

An SLO is a target reliability threshold for a service. For ML models,
the standard SLOs tracked here are:

| Metric | Default target | Window |
|---|---|---|
| Availability | ≥ 99.5% | 30 days |
| Latency P99 | ≤ 500 ms | 5 minutes |
| Latency P50 | ≤ 100 ms | 5 minutes |
| Error rate | ≤ 1% | 5 minutes |

Default values are defined in [`_defaults.yaml`](_defaults.yaml).

## Files in This Directory

| File | Purpose |
|---|---|
| `_defaults.yaml` | Default SLO threshold values; read by all per-model SLO files |
| `slo-template.yaml` | Copy-paste template for a new model endpoint SLO |
| `vllm-serving-slo.yaml` | Live SLO for the vLLM serving endpoint |
| `<model-name>-slo.yaml` | Per-model SLO file (create from template) |

## Creating a New Model SLO

1. Copy the template:

   ```bash
   cp monitoring/slos/slo-template.yaml monitoring/slos/<model-name>-slo.yaml
   ```

2. Replace every `<model-name>` placeholder with your model's name
   (e.g. `fraud-detection`):

   ```bash
   sed -i 's/<model-name>/fraud-detection/g' monitoring/slos/fraud-detection-slo.yaml
   ```

3. Review the thresholds. If your model has different latency or availability
   requirements, override the values directly in the file. Otherwise leave
   them matching `_defaults.yaml`.

4. Apply to the cluster:

   ```bash
   kubectl apply -f monitoring/slos/<model-name>-slo.yaml
   ```

5. Verify the rules loaded in Prometheus:

   ```
   Prometheus UI → Status → Rules → look for <model-name>-serving-slo-rules
   ```

## Per-Endpoint vs Per-Model

Each **deployed endpoint** (cloud or runtime) gets its own SLO file, not each
model version. When a model is multi-cloud, create one SLO file per cloud:

```
monitoring/slos/
  fraud-detection-aws-slo.yaml
  fraud-detection-gcp-slo.yaml
  fraud-detection-azure-slo.yaml
```

## Burn-Rate Alerting

The template includes two-tier burn-rate alerts:

- **Fast burn (critical)** — 14.4× budget consumption over 1 hour.
  If this fires, the 30-day error budget will be exhausted in approximately 2 hours.
  Page on-call immediately.

- **Slow burn (warning)** — 6× budget consumption over 6 hours.
  The 30-day error budget will be exhausted in approximately 5 days.
  Schedule remediation.

See [Google SRE Book Chapter 5](https://sre.google/workbook/alerting-on-slos/)
for the theory behind multi-window burn-rate alerting.
