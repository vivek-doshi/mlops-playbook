# finops/reports/README.md
#
# This directory is auto-generated. Do not commit hand-edited files here.
# Reports are created by the finops CI workflows.

# ML Cost Reports

Auto-generated cost reports are stored here.

| Subdirectory | Contents | Created by |
|---|---|---|
| `daily/` | Daily cost-attribution JSON (`YYYY-MM-DD.json`) | `ci/github-actions/finops/weekly-cost-report.yml` (daily step) |
| `weekly/` | Weekly JSON + Markdown reports | `ci/github-actions/finops/weekly-cost-report.yml` |
| `monthly/` | Monthly chargeback JSON + Markdown | `ci/github-actions/finops/monthly-cost-report.yml` |

All files in these subdirectories are gitignored (add `finops/reports/` to
`.gitignore`) and are uploaded as GitHub Actions artifacts for 90 days.
