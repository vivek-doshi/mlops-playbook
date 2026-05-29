"""
Purpose:
    Monthly ML cost report generator.  Aggregates all daily cost-attribution
    JSON files for the previous calendar month, produces a per-model/per-team
    cost breakdown, checks against monthly budget limits, and writes a JSON
    report and Markdown summary.

    The monthly report is the primary input for chargeback to engineering teams.

Usage:
    python finops/scripts/monthly-cost-report.py \\
        --reports-dir  finops/reports/daily/ \\
        --output-dir   finops/reports/monthly/ \\
        --budget-dir   finops/budgets/ \\
        --month        2026-05   # defaults to previous calendar month

Dependencies:
    pandas>=2.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import json
import sys
from calendar import monthrange
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


# --------------------------------------------------------------------------- #
# Helpers (shared with weekly report)
# --------------------------------------------------------------------------- #


def _load_budgets(budget_dir: str) -> dict[str, dict]:
    budgets: dict[str, dict] = {}
    for path in Path(budget_dir).glob("*.yaml"):
        if path.name.startswith("_"):
            continue
        with open(path) as fh:
            cfg = yaml.safe_load(fh)
        if cfg and "model_name" in cfg:
            budgets[cfg["model_name"]] = cfg
    return budgets


def _load_daily_reports_for_month(
    reports_dir: str, year: int, month: int
) -> pd.DataFrame:
    """Load all daily JSON reports for the given year-month."""
    prefix = f"{year:04d}-{month:02d}-"
    rows: list[dict] = []
    for path in sorted(Path(reports_dir).glob(f"{prefix}*.json")):
        with open(path) as fh:
            report = json.load(fh)
        for entry in report.get("summary", []):
            entry["report_date"] = path.stem
            rows.append(entry)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# --------------------------------------------------------------------------- #
# Monthly summary
# --------------------------------------------------------------------------- #


def _generate_monthly_summary(
    df: pd.DataFrame,
    budgets: dict[str, dict],
    year: int,
    month: int,
) -> dict:
    month_str = f"{year:04d}-{month:02d}"
    _, days_in_month = monthrange(year, month)

    if df.empty:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": month_str,
            "days_in_period": days_in_month,
            "total_cost_usd": 0.0,
            "by_model": [],
            "by_team": [],
            "by_cost_center": [],
            "budget_alerts": [],
        }

    by_model = (
        df.groupby(["model_name", "environment", "cost_center", "team"])
        .agg(
            total_cost_usd=("total_cost_usd", "sum"),
            avg_daily_cost_usd=("total_cost_usd", "mean"),
            total_gpu_units=("total_gpu_units", "sum"),
            total_cpu_cores=("total_cpu_cores", "sum"),
            total_memory_gib=("total_memory_gib", "sum"),
        )
        .reset_index()
        .round(4)
        .to_dict(orient="records")
    )

    by_team = (
        df.groupby("team")["total_cost_usd"]
        .sum()
        .reset_index()
        .rename(columns={"total_cost_usd": "monthly_cost_usd"})
        .round(4)
        .sort_values("monthly_cost_usd", ascending=False)
        .to_dict(orient="records")
    )

    by_cost_center = (
        df.groupby("cost_center")["total_cost_usd"]
        .sum()
        .reset_index()
        .rename(columns={"total_cost_usd": "monthly_cost_usd"})
        .round(4)
        .sort_values("monthly_cost_usd", ascending=False)
        .to_dict(orient="records")
    )

    # Budget breach detection (monthly)
    budget_alerts: list[dict] = []
    monthly_by_model = df.groupby("model_name")["total_cost_usd"].sum()
    for model, monthly_cost in monthly_by_model.items():
        if model in budgets:
            budget = budgets[model]
            monthly_limit = budget.get("monthly_limit_usd")
            if monthly_limit and monthly_cost > monthly_limit:
                budget_alerts.append(
                    {
                        "model_name": model,
                        "monthly_cost_usd": round(float(monthly_cost), 2),
                        "monthly_limit_usd": monthly_limit,
                        "overage_pct": round(
                            (float(monthly_cost) - monthly_limit)
                            / monthly_limit
                            * 100,
                            1,
                        ),
                    }
                )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": month_str,
        "days_in_period": days_in_month,
        "total_cost_usd": round(float(df["total_cost_usd"].sum()), 4),
        "by_model": by_model,
        "by_team": by_team,
        "by_cost_center": by_cost_center,
        "budget_alerts": budget_alerts,
    }


def _render_markdown(summary: dict) -> str:
    lines = [
        f"## Monthly ML Cost Report — {summary['period']}",
        f"**Total:** ${summary['total_cost_usd']:,.2f}  ",
        f"**Generated:** {summary['generated_at']}",
        "",
    ]

    if summary["budget_alerts"]:
        lines.append("### ⚠️ Budget Alerts")
        for alert in summary["budget_alerts"]:
            lines.append(
                f"- **{alert['model_name']}**: ${alert['monthly_cost_usd']:,.2f} "
                f"vs limit ${alert['monthly_limit_usd']:,.2f} "
                f"(+{alert['overage_pct']}%)"
            )
        lines.append("")

    lines.append("### Cost by Team")
    lines.append("| Team | Monthly Cost (USD) |")
    lines.append("|---|---|")
    for row in summary["by_team"]:
        lines.append(f"| {row['team']} | ${row['monthly_cost_usd']:,.2f} |")

    lines.append("")
    lines.append("### Cost by Cost Centre")
    lines.append("| Cost Centre | Monthly Cost (USD) |")
    lines.append("|---|---|")
    for row in summary["by_cost_center"]:
        lines.append(
            f"| {row['cost_center']} | ${row['monthly_cost_usd']:,.2f} |"
        )

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def generate_monthly_report(
    reports_dir: str,
    output_dir: str,
    budget_dir: str,
    year: int,
    month: int,
) -> dict:
    df = _load_daily_reports_for_month(reports_dir, year, month)
    budgets = _load_budgets(budget_dir)
    summary = _generate_monthly_summary(df, budgets, year, month)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    month_str = f"{year:04d}-{month:02d}"

    json_path = out / f"{month_str}-monthly-report.json"
    with open(json_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"Monthly report: {json_path}")

    md_path = out / f"{month_str}-monthly-report.md"
    with open(md_path, "w") as fh:
        fh.write(_render_markdown(summary))
    print(f"Markdown summary: {md_path}")

    if summary["budget_alerts"]:
        print(f"ALERT: {len(summary['budget_alerts'])} models exceeded monthly budget.")
        sys.exit(1)

    return summary


def _parse_args() -> argparse.Namespace:
    now = datetime.now(timezone.utc)
    prev_month = now.month - 1 or 12
    prev_year = now.year if now.month > 1 else now.year - 1
    default_month = f"{prev_year:04d}-{prev_month:02d}"

    parser = argparse.ArgumentParser(description="Generate monthly ML cost report.")
    parser.add_argument("--reports-dir", default="finops/reports/daily/")
    parser.add_argument("--output-dir", default="finops/reports/monthly/")
    parser.add_argument("--budget-dir", default="finops/budgets/")
    parser.add_argument(
        "--month",
        default=default_month,
        help="Month to report (YYYY-MM). Defaults to previous calendar month.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    year, month = [int(p) for p in args.month.split("-")]
    generate_monthly_report(
        reports_dir=args.reports_dir,
        output_dir=args.output_dir,
        budget_dir=args.budget_dir,
        year=year,
        month=month,
    )
