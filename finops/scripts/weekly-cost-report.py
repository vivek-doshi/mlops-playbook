"""
Purpose:
    Weekly ML cost report generator.  Reads the daily cost-attribution JSON
    files produced by ml-cost-attribution.py (one file per day, stored in
    finops/reports/daily/), aggregates them into a 7-day summary, and writes
    a weekly report plus a Markdown summary suitable for Slack / PR comment.

Usage:
    python finops/scripts/weekly-cost-report.py \\
        --reports-dir  finops/reports/daily/ \\
        --output-dir   finops/reports/weekly/ \\
        --budget-dir   finops/budgets/

Dependencies:
    pandas>=2.0
    pyyaml>=6.0
    jinja2>=3.1
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yaml


# --------------------------------------------------------------------------- #
# Budget loading
# --------------------------------------------------------------------------- #


def _load_budgets(budget_dir: str) -> dict[str, dict]:
    """
    Load all budget YAML files from budget_dir.
    Returns a dict keyed by model_name.
    """
    budgets: dict[str, dict] = {}
    for path in Path(budget_dir).glob("*.yaml"):
        if path.name.startswith("_"):
            continue
        with open(path) as fh:
            cfg = yaml.safe_load(fh)
        if cfg and "model_name" in cfg:
            budgets[cfg["model_name"]] = cfg
    return budgets


# --------------------------------------------------------------------------- #
# Report aggregation
# --------------------------------------------------------------------------- #


def _load_daily_reports(reports_dir: str, days: int = 7) -> pd.DataFrame:
    """
    Load daily cost-attribution JSON files for the last `days` days.
    Files are expected to be named YYYY-MM-DD.json.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows: list[dict] = []
    for path in sorted(Path(reports_dir).glob("*.json")):
        try:
            date = datetime.strptime(path.stem, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if date < cutoff:
            continue
        with open(path) as fh:
            report = json.load(fh)
        for entry in report.get("summary", []):
            entry["report_date"] = path.stem
            rows.append(entry)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _generate_weekly_summary(
    df: pd.DataFrame,
    budgets: dict[str, dict],
) -> dict:
    if df.empty:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days": 7,
            "total_cost_usd": 0.0,
            "by_model": [],
            "budget_alerts": [],
        }

    # Aggregate by model
    by_model = (
        df.groupby(["model_name", "environment", "cost_center", "team"])
        .agg(
            total_cost_usd=("total_cost_usd", "sum"),
            avg_daily_cost_usd=("total_cost_usd", "mean"),
            total_gpu_units=("total_gpu_units", "sum"),
        )
        .reset_index()
        .round(4)
        .to_dict(orient="records")
    )

    # Budget breach detection
    budget_alerts: list[dict] = []
    weekly_by_model = df.groupby("model_name")["total_cost_usd"].sum()
    for model, weekly_cost in weekly_by_model.items():
        if model in budgets:
            budget = budgets[model]
            weekly_limit = budget.get("weekly_limit_usd")
            if weekly_limit and weekly_cost > weekly_limit:
                budget_alerts.append(
                    {
                        "model_name": model,
                        "weekly_cost_usd": round(float(weekly_cost), 2),
                        "weekly_limit_usd": weekly_limit,
                        "overage_pct": round(
                            (float(weekly_cost) - weekly_limit) / weekly_limit * 100, 1
                        ),
                    }
                )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_days": 7,
        "total_cost_usd": round(float(df["total_cost_usd"].sum()), 4),
        "by_model": by_model,
        "budget_alerts": budget_alerts,
    }


def _render_markdown(summary: dict) -> str:
    """Render a Markdown summary of the weekly report."""
    lines = [
        "## Weekly ML Cost Report",
        f"**Period:** last 7 days  ",
        f"**Total:** ${summary['total_cost_usd']:,.2f}  ",
        f"**Generated:** {summary['generated_at']}",
        "",
    ]

    if summary["budget_alerts"]:
        lines.append("### ⚠️ Budget Alerts")
        for alert in summary["budget_alerts"]:
            lines.append(
                f"- **{alert['model_name']}**: ${alert['weekly_cost_usd']:,.2f} "
                f"vs limit ${alert['weekly_limit_usd']:,.2f} "
                f"(+{alert['overage_pct']}%)"
            )
        lines.append("")

    lines.append("### Cost by Model")
    lines.append("| Model | Environment | Cost (USD) | Avg Daily | GPU units |")
    lines.append("|---|---|---|---|---|")
    for row in sorted(
        summary["by_model"], key=lambda r: r["total_cost_usd"], reverse=True
    ):
        lines.append(
            f"| {row['model_name']} | {row['environment']} "
            f"| ${row['total_cost_usd']:,.2f} "
            f"| ${row['avg_daily_cost_usd']:,.2f} "
            f"| {row['total_gpu_units']} |"
        )

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def generate_weekly_report(
    reports_dir: str,
    output_dir: str,
    budget_dir: str,
) -> dict:
    df = _load_daily_reports(reports_dir, days=7)
    budgets = _load_budgets(budget_dir)
    summary = _generate_weekly_summary(df, budgets)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = out / f"{today}-weekly-report.json"
    with open(json_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"Weekly report: {json_path}")

    md_path = out / f"{today}-weekly-report.md"
    with open(md_path, "w") as fh:
        fh.write(_render_markdown(summary))
    print(f"Markdown summary: {md_path}")

    if summary["budget_alerts"]:
        print(f"ALERT: {len(summary['budget_alerts'])} models exceeded weekly budget.")
        sys.exit(1)

    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly ML cost report.")
    parser.add_argument("--reports-dir", default="finops/reports/daily/")
    parser.add_argument("--output-dir", default="finops/reports/weekly/")
    parser.add_argument("--budget-dir", default="finops/budgets/")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    generate_weekly_report(
        reports_dir=args.reports_dir,
        output_dir=args.output_dir,
        budget_dir=args.budget_dir,
    )
