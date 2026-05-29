# ML Cost Attribution & FinOps

This directory contains cost attribution scripts, per-model budget configs,
dashboards, and alert rules for ML workload cost governance.

## Directory Layout

```
finops/
├── budgets/
│   ├── _budget-schema.yaml     # Schema reference
│   └── <model-name>.yaml       # One budget file per model
├── data/
│   └── instance-rates.yaml     # Compute cost rates ($/core/hr, $/GiB/hr, $/GPU/hr)
├── dashboards/
│   └── ml-cost-attribution.json  # Grafana dashboard JSON
├── alerts/
│   └── ml-cost-alerts.yaml     # Prometheus cost alerts
├── reports/
│   ├── daily/                  # Auto-generated daily JSON files
│   ├── weekly/                 # Auto-generated weekly reports
│   └── monthly/                # Auto-generated monthly reports
└── scripts/
    ├── ml-cost-attribution.py  # Daily cost attribution runner
    ├── weekly-cost-report.py   # Weekly aggregation and budget check
    └── monthly-cost-report.py  # Monthly chargeback report
```

## Quick Start

### 1. Create a budget file for your model

```bash
cp finops/budgets/_budget-schema.yaml finops/budgets/<model-name>.yaml
# Edit model_name, team, cost_center, weekly_limit_usd, monthly_limit_usd
```

### 2. Run daily cost attribution

```bash
python finops/scripts/ml-cost-attribution.py \
    --rates-file  finops/data/instance-rates.yaml \
    --output-path finops/reports/daily/$(date +%Y-%m-%d).json
```

### 3. Generate weekly report

```bash
python finops/scripts/weekly-cost-report.py
```

### 4. Generate monthly report

```bash
python finops/scripts/monthly-cost-report.py --month 2026-05
```

## CI Automation

| Workflow | Schedule | File |
|---|---|---|
| Daily cost attribution | Cron: 01:00 UTC daily | `ci/github-actions/finops/weekly-cost-report.yml` |
| Weekly report | Cron: Monday 06:00 UTC | `ci/github-actions/finops/weekly-cost-report.yml` |
| Monthly report | Cron: 1st of month 07:00 UTC | `ci/github-actions/finops/monthly-cost-report.yml` |
| Budget check in promotion | Called from promotion-gates.yml | `ci/github-actions/finops/cost-budget-check.yml` |

## Required Pod Labels

Every pod deployed by this playbook must carry these labels or cost attribution
cannot be assigned:

```yaml
labels:
  cost-center: "<value>"
  team:        "<value>"
  model-name:  "<value>"
  environment: "<value>"
```

Missing labels are reported in `untagged_pods` in the daily report.

## Further Reading

- `docs/golden-paths/ml-cost-attribution.md` — step-by-step guide
- `docs/guides/gpu-cost-governance.md` — GPU-specific cost guidance
