"""
Purpose:
    CLI model card generator.  Reads model metadata from MLflow, fairness
    policy from policy/fairness/, SLO config from monitoring/slos/, and
    approval status from policy/model-approval/approved-versions.yaml, then
    renders a Markdown model card via a Jinja2 template.

Usage:
    python scripts/generate_model_card.py \\
        --model-name    <name> \\
        --model-version <version> \\
        --output-dir    docs/model-cards/

    Optional overrides:
        --tracking-uri  <mlflow_tracking_uri>   (default: MLFLOW_TRACKING_URI env var)
        --template      <path/to/template.j2>   (default: scripts/model-card-template.md.j2)

Dependencies:
    mlflow>=2.11
    jinja2>=3.1
    pyyaml>=6.0

Exit codes:
    0  — model card written successfully
    1  — model or model version not found in MLflow registry
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install mlflow", file=sys.stderr)
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install jinja2", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict[str, Any] | None:
    """Return parsed YAML dict or None if file does not exist."""
    if not path.exists():
        return None
    with path.open() as fh:
        return yaml.safe_load(fh)


def _find_approval_entry(
    approved_versions_path: Path,
    model_name: str,
    model_version: str,
) -> dict[str, Any] | None:
    """Return the approval entry for model_name@model_version, or None."""
    data = _load_yaml(approved_versions_path)
    if not data:
        return None
    for entry in data.get("approved_versions", []):
        if (
            entry.get("model_name") == model_name
            and str(entry.get("version")) == str(model_version)
        ):
            return entry
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Core generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_model_card(
    model_name: str,
    model_version: str,
    output_dir: Path,
    tracking_uri: str | None,
    template_path: Path,
) -> int:
    """
    Fetch model metadata from MLflow and render a model card.

    Returns 0 on success, 1 on failure.
    """
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    client = MlflowClient()

    # ── 1. Resolve model version ──────────────────────────────────────────
    try:
        mv = client.get_model_version(model_name, model_version)
    except mlflow.exceptions.MlflowException as exc:
        print(
            f"ERROR: Model '{model_name}' version '{model_version}' not found "
            f"in MLflow registry.\n{exc}",
            file=sys.stderr,
        )
        return 1

    run_id: str = mv.run_id or ""

    # ── 2. Fetch run metrics and tags ─────────────────────────────────────
    metrics: dict[str, float] = {}
    model_tags: dict[str, str] = dict(mv.tags or {})

    if run_id:
        try:
            run = client.get_run(run_id)
            metrics = {k: v for k, v in (run.data.metrics or {}).items()}
            # Merge run tags; model version tags take precedence.
            run_tags = dict(run.data.tags or {})
            run_tags.update(model_tags)
            model_tags = run_tags
        except mlflow.exceptions.MlflowException:
            pass  # Run may have been garbage-collected; carry on.

    # ── 3. Load side-car YAML files ───────────────────────────────────────
    repo_root = Path(__file__).parent.parent

    fairness_config = _load_yaml(
        repo_root / "policy" / "fairness" / f"{model_name}-fairness.yaml"
    )
    slo_config = _load_yaml(
        repo_root / "monitoring" / "slos" / f"{model_name}-slo.yaml"
    )
    slo_defaults = _load_yaml(
        repo_root / "monitoring" / "slos" / "_defaults.yaml"
    ) or {}
    approval_entry = _find_approval_entry(
        repo_root / "policy" / "model-approval" / "approved-versions.yaml",
        model_name,
        model_version,
    )

    # ── 4. Render template ────────────────────────────────────────────────
    template_dir = template_path.parent
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_path.name)

    rendered = template.render(
        model_name=model_name,
        model_version=model_version,
        run_id=run_id,
        metrics=metrics,
        model_tags=model_tags,
        fairness_config=fairness_config,
        slo_config=slo_config,
        slo_defaults=slo_defaults.get("slo_defaults", {}),
        approval_entry=approval_entry,
        last_updated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )

    # ── 5. Write output ───────────────────────────────────────────────────
    out_path = output_dir / model_name / f"v{model_version}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")

    print(f"✓ Model card written to {out_path}")
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown model card from MLflow metadata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--model-name", required=True, help="MLflow registered model name.")
    parser.add_argument("--model-version", required=True, help="MLflow model version number.")
    parser.add_argument(
        "--output-dir",
        default="docs/model-cards/",
        help="Directory to write the model card into (default: docs/model-cards/).",
    )
    parser.add_argument(
        "--tracking-uri",
        default=None,
        help="MLflow tracking URI (overrides MLFLOW_TRACKING_URI env var).",
    )
    parser.add_argument(
        "--template",
        default=str(Path(__file__).parent / "model-card-template.md.j2"),
        help="Path to Jinja2 template file (default: scripts/model-card-template.md.j2).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return generate_model_card(
        model_name=args.model_name,
        model_version=args.model_version,
        output_dir=Path(args.output_dir),
        tracking_uri=args.tracking_uri,
        template_path=Path(args.template),
    )


if __name__ == "__main__":
    sys.exit(main())
