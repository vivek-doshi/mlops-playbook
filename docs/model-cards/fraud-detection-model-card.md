# Model Card: fraud-detection

## 1) Model Details

- **Model name:** `fraud-detection`
- **Model type:** Binary classifier (fraud vs non-fraud)
- **Primary owner:** ML Platform Team
- **Serving runtime:** Triton (primary), shadow validation via Triton shadow deployment
- **Last updated:** 2026-05-29

## 2) Intended Use

- **Primary use case:** Real-time fraud screening for payment transactions.
- **Intended users:** Fraud risk platform services and fraud operations analysts.
- **Out-of-scope usage:** Credit decisioning, identity scoring, or any HR/legal decisions.

## 3) Training Data

- **Data source:** Versioned transaction features tracked through DVC + Feast feature definitions.
- **Entity granularity:** Customer and transaction level events.
- **Feature lineage contract:** Every training run stores feature snapshot hash and source dataset hash.
- **Sensitive data note:** No raw PAN data; tokenized or aggregated attributes only.

## 4) Evaluation

- **Primary metrics:** Precision, recall, PR-AUC, false-positive rate.
- **Promotion gates:** Accuracy threshold + drift threshold + lineage verification.
- **Stress scenarios evaluated:** High-volume bursts, high-risk geographies, chargeback lag windows.

## 5) Fairness and Risk Notes

- Monitor false-positive rate by region, payment channel, and customer tenure bucket.
- Escalate for review if any monitored segment exceeds baseline false-positive rate by >20%.
- Human review remains required for high-risk flagged transactions above policy threshold.

## 6) Monitoring and SLO Alignment

- Drift checks run on a schedule through `ci/github-actions/model-monitoring/drift-check.yml`.
- Shadow deployment compares primary vs shadow score distribution before production promotion.
- Serving reliability objectives are tracked via vLLM/Triton SLO definitions in `monitoring/slos/`.

## 7) Ethical and Operational Limitations

- The model can underperform during abrupt fraud pattern shifts (seasonality, new attack vectors).
- False negatives can occur for previously unseen fraud signatures.
- Regular retraining and analyst feedback loops are required to maintain effectiveness.

## 8) Approval and Governance

- Production promotion requires policy compliance with `policy/model-approval/README.md`.
- PII and governance checklist must pass when sensitive features are introduced.
- Incident response follows monitoring and model rollback runbooks in golden paths.
