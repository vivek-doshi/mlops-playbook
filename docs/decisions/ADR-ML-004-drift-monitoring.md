# ADR-ML-004: Evidently AI for Drift and Data Quality Monitoring

**Status:** Accepted
**Date:** 2024-09-01
**Authors:** ML Platform Team
**Reviewers:** @ml-approvers

---

## Context

Deployed ML models degrade silently. Two root causes account for most production failures:

1. **Data drift** — the statistical distribution of input features shifts away from the training distribution. The model was never trained on inputs that look like this.
2. **Target drift** — the distribution of model predictions (or ground-truth labels, when available) changes over time.

Without an automated monitoring layer, teams discover degradation only after a business metric (fraud rate, click-through rate, revenue) moves visibly — often days or weeks after the model started failing.

Requirements identified:

- Detect distributional shift on tabular feature inputs.
- Produce human-readable HTML reports for model review sessions.
- Export numeric drift scores that Prometheus can scrape and alert on.
- Work without a paid SaaS contract (data residency requirement).
- Integrate with the existing MLflow + DVC lineage chain.

---

## Decision

We will use **Evidently AI** (open-source, Apache-2.0) for drift and data quality monitoring.

Key implementation choices:

| Concern | Approach |
|---------|---------|
| Scheduled monitoring | GitHub Actions cron job (`ci/github-actions/model-monitoring/drift-check.yml`) |
| On-demand script | `monitoring/evidently/drift_report.py` — CLI with `--reference`, `--current`, `--threshold` |
| Report format | HTML (human review) + JSON (machine-readable Prometheus push) |
| Drift threshold | Warning at 0.3, critical at 0.6 (dataset-share-of-drifted-features) |
| Alert routing | Prometheus `AlertManager` → Slack (warning), PagerDuty (critical) |
| Retraining trigger | Critical drift dispatches `train.yml` via GitHub Actions API |
| MLflow logging | Drift score logged as a metric on a dedicated `drift-monitoring` run |

Prometheus alert rules: `monitoring/alerts/drift-alerts.yaml`
Grafana dashboard: `monitoring/dashboards/model-health.json`

---

## Alternatives Considered

### Alibi Detect (SeldonIO)
- **Pros:** Statistical rigour (MMD, LSDD, online detectors). Excellent for image/NLP data.
- **Cons:** Requires Python runtime with heavy TensorFlow/PyTorch dependencies even for tabular data. No built-in HTML reporting. Harder for data scientists unfamiliar with hypothesis testing to interpret.

### WhyLogs / WhyLabs
- **Pros:** Lightweight profiling library. Cloud dashboard is polished.
- **Cons:** Best value comes from the WhyLabs SaaS — violates our data residency requirement. Self-hosted option is significantly less capable.

### Grafana + custom Prometheus metrics (no Evidently)
- **Pros:** Already in the observability stack.
- **Cons:** Requires writing custom feature distribution exporters for every model. No standardised drift statistical test. Does not produce the model-card-style HTML reports that stakeholders expect.

### nannyML
- **Pros:** Strong CBPE-based performance estimation without ground-truth labels.
- **Cons:** Narrower scope (performance estimation only). Complementary to drift detection rather than a replacement. May be added as a future integration.

---

## Consequences

**Positive:**
- Engineers write one standard drift report script per model; the CI job handles scheduling.
- Drift scores are Prometheus-native — no extra instrumentation.
- HTML reports can be committed as CI artifacts or linked in incident GitHub Issues.

**Negative:**
- Evidently is Python-only. Non-Python model owners must wrap the monitoring call.
- Statistical tests (KS, PSI, Wasserstein) may produce false positives during seasonal data shifts — thresholds will need tuning per model after production observation.

**Neutral:**
- Evidently v0.4+ has breaking API changes from v0.3. Pin the version in `requirements.txt` and Dependabot will manage upgrades.

---

## Review Triggers

Re-evaluate this decision if:
- The team adopts real-time feature stores (Feast, Tecton) — streaming drift detection may be preferred over batch.
- Model count exceeds 20 — a centralised monitoring platform (Arize, Fiddler) may offer better multi-model UX at that scale.
