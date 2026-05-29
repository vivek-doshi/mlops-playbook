# ML Cost Attribution Golden Path

## Purpose and Scope

This golden path describes how to track, report, and govern the cost of ML
workloads using label-based attribution, per-model budgets, and automated CI gates.

> **Beginner tip**: Cloud ML costs can spiral without visibility. This system
> works by reading Kubernetes pod labels (`cost-center`, `team`, `model-name`,
> `environment`) and multiplying resource requests by per-hour rates. It's
> an *estimate* — not your cloud bill — but it's fast enough to run daily and
> attributable enough to charge back to teams.

---

## Prerequisites

| Requirement | Where to configure |
|---|---|
| All pods carry required cost labels | `cd/kubernetes/_base/deployment.yaml` |
| Instance rates file up to date | `finops/data/instance-rates.yaml` |
| Kubeconfig secret in GitHub Actions | `KUBECONFIG_B64` secret |

---

## Required Pod Labels

Every Kubernetes workload in this playbook must include:

```yaml
labels:
  cost-center: "ml-platform"   # billing cost centre
  team:        "fraud-ml"      # owning team
  model-name:  "fraud-detection"
  environment: "production"    # dev | staging | production
```

Pods missing any of these labels appear in `untagged_pods` in every cost report.

---

## Step 1: Create a Budget File

```bash
cp finops/budgets/_budget-schema.yaml finops/budgets/<model-name>.yaml
```

Edit the file:

```yaml
model_name:       fraud-detection
team:             fraud-ml
cost_center:      ml-platform
weekly_limit_usd: 500.00
monthly_limit_usd: 2000.00
```

Open a PR — the budget file is reviewed alongside the model PR.

---

## Step 2: Update Instance Rates (Platform Team)

If your cloud provider rates have changed, update `finops/data/instance-rates.yaml`:

```yaml
cpu_per_core_per_hour:    0.048
memory_per_gib_per_hour:  0.006
gpu_per_unit_per_hour:    2.10
spot_discount_factor:     0.70
```

---

## Step 3: Run Daily Cost Attribution

The CI workflow runs this automatically, but you can run it locally:

```bash
python finops/scripts/ml-cost-attribution.py \
    --rates-file  finops/data/instance-rates.yaml \
    --output-path finops/reports/daily/$(date +%Y-%m-%d).json
```

The output is a JSON file with:
- `summary`: cost per (cost-center, team, model-name, environment)
- `untagged_pods`: pods missing required labels
- `total_cost_usd`: total estimated spend for the lookback window

---

## Step 4: Weekly and Monthly Reports

**Weekly report** (auto-generated every Monday):

```bash
python finops/scripts/weekly-cost-report.py
```

**Monthly report** (auto-generated on the 1st of each month):

```bash
python finops/scripts/monthly-cost-report.py --month 2026-05
```

Both reports exit 1 if any model exceeds its budget limit, making the CI
workflow visibly fail.

---

## Step 5: Budget Gate in Promotions

The `cost-budget-check.yml` workflow is called by `promotion-gates.yml` for
staging and production promotions. If a model's current weekly spend exceeds
its budget limit, the promotion is blocked.

To override a budget block:

1. Investigate and justify the cost overrun in a PR comment.
2. Either update `weekly_limit_usd` in the budget file, or
3. Have a `@platform-infra-team` member manually approve the promotion with
   a GitHub environment override.

---

## Interpreting Reports

### `total_cost_usd`

Estimated spend based on pod resource *requests* × per-hour rates × lookback window.
This is always an over-estimate because pods may not use all their requested resources.
Use this as an upper bound.

### GPU cost

GPU is typically the dominant cost driver. A model running 1 × A10G for 24 hours
costs approximately:

$$1 \times \$2.10/\text{hr} \times 24 = \$50.40/\text{day}$$

Enable spot instances (dev and staging by default) to save ~70%.

### Untagged pods

Untagged pods are a governance gap — their cost cannot be attributed. Fix by
ensuring all pod specs carry the required labels (set in the Kustomize base).

---

## Cost Governance Rules

| Rule | Enforcement |
|---|---|
| All pods must have 4 required labels | Kyverno policy (platform repo) |
| Budget file required before prod promotion | `cost-budget-check.yml` gate |
| Spot instances required in dev + staging | `dev-policy.yaml`, `staging-policy.yaml` |
| On-demand in production by default | `production-policy.yaml` |
| Spot override in staging requires @platform-infra-team | `staging-policy.yaml` |

---

## Further Reading

- `finops/` — scripts, budgets, data, alerts
- `docs/guides/gpu-cost-governance.md` — GPU-specific cost controls
- `monitoring/alerts/drift-alerts.yaml` — cost alert reference
