"""
Purpose:
    End-to-end model optimisation pipeline.  Accepts a Production-stage MLflow
    model, applies quantisation, pruning, or distillation, benchmarks the result
    against the baseline, validates accuracy and latency gates, and registers the
    optimised model in the MLflow Model Registry.

Usage:
    python model_optimization/pipeline.py \\
        --model-name     my-model \\
        --model-version  3 \\
        --method         quantisation \\
        --target         cpu

Dependencies:
    mlflow>=2.14
    onnxruntime>=1.18
    optimum>=1.20
    numpy>=1.26
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install mlflow", file=sys.stderr)
    sys.exit(1)

from model_optimization.quantisation import run_quantisation
from model_optimization.pruning import run_pruning
from model_optimization.benchmark import BenchmarkHarness

# Accuracy and latency gate thresholds
_MAX_ACCURACY_DELTA_PCT = 0.5     # reject if accuracy drops more than 0.5 %
_MAX_LATENCY_REGRESSION_PCT = 0.0  # reject if p99 latency increases at all


def _load_baseline_metrics(
    client: MlflowClient, run_id: str
) -> dict[str, float]:
    """Return a flat metric dict from the baseline MLflow run."""
    run = client.get_run(run_id)
    return {k: v for k, v in run.data.metrics.items()}


def _accuracy_delta_pct(
    baseline_metrics: dict[str, float], optimised_metrics: dict[str, float]
) -> float:
    """Return percentage accuracy drop (positive = degraded)."""
    key = next(
        (k for k in ("accuracy", "f1", "roc_auc", "eval_loss") if k in baseline_metrics),
        None,
    )
    if key is None:
        print("  WARN: No accuracy metric found; skipping accuracy gate.", file=sys.stderr)
        return 0.0
    baseline = baseline_metrics[key]
    optimised = optimised_metrics.get(key, baseline)
    if baseline == 0:
        return 0.0
    return ((baseline - optimised) / abs(baseline)) * 100.0


def run_pipeline(
    model_name: str,
    model_version: int,
    method: str,
    target: str,
    tracking_uri: str = "http://localhost:5000",
    dry_run: bool = False,
) -> str | None:
    """
    Execute the optimisation pipeline.

    Parameters
    ----------
    model_name : str
        Name of the Production-stage model in MLflow Registry.
    model_version : int
        Model version to optimise.
    method : str
        Optimisation method: quantisation | pruning | distillation.
    target : str
        Hardware target: cpu | cuda-a100 | cuda-h100 | triton-onnx | triton-trt.
    tracking_uri : str
        MLflow tracking server URI.
    dry_run : bool
        If True, skip registration after benchmarking.

    Returns
    -------
    str | None
        MLflow run ID of the optimised model run, or None on rejection.
    """
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    # ── 0. Verify model is in Production stage ────────────────────────────────
    mv = client.get_model_version(model_name, str(model_version))
    if mv.current_stage not in ("Production", "Staging"):
        print(
            f"ERROR: Model {model_name} v{model_version} is in stage "
            f"'{mv.current_stage}' — only Production/Staging models may be optimised.",
            file=sys.stderr,
        )
        sys.exit(1)

    baseline_run_id = mv.run_id
    baseline_metrics = _load_baseline_metrics(client, baseline_run_id)
    print(f"Baseline run: {baseline_run_id}")
    print(f"Baseline metrics: {baseline_metrics}")

    # ── 1. Apply optimisation ─────────────────────────────────────────────────
    model_uri = f"models:/{model_name}/{model_version}"
    optimised_dir = Path(f"outputs/optimised/{model_name}-v{model_version}-{method}/")

    if method == "quantisation":
        run_quantisation(
            model_uri=model_uri,
            output_dir=optimised_dir,
            target=target,
        )
    elif method == "pruning":
        run_pruning(
            model_uri=model_uri,
            output_dir=optimised_dir,
        )
    elif method == "distillation":
        print(
            "Distillation requires separate teacher/student training — "
            "use model_optimization/distillation/trainer.py directly.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(f"ERROR: Unknown method '{method}'.", file=sys.stderr)
        sys.exit(1)

    # ── 2. Benchmark ──────────────────────────────────────────────────────────
    target_config = Path(f"model_optimization/targets/{target}.yaml")
    harness = BenchmarkHarness(target_config=target_config)
    optimised_metrics = harness.run(model_dir=optimised_dir)
    baseline_benchmark = harness.run_baseline(model_uri=model_uri)

    print(f"Optimised metrics: {optimised_metrics}")
    print(f"Baseline benchmark: {baseline_benchmark}")

    # ── 3. Gate: accuracy ─────────────────────────────────────────────────────
    delta = _accuracy_delta_pct(baseline_metrics, optimised_metrics)
    if delta > _MAX_ACCURACY_DELTA_PCT:
        print(
            f"REJECT: accuracy delta {delta:.2f}% > threshold {_MAX_ACCURACY_DELTA_PCT}%. "
            "Keeping baseline.",
            file=sys.stderr,
        )
        return None

    # ── 4. Gate: latency ──────────────────────────────────────────────────────
    baseline_p99 = baseline_benchmark.get("latency_p99_ms", 0.0)
    opt_p99 = optimised_metrics.get("latency_p99_ms", 0.0)
    if baseline_p99 > 0 and opt_p99 > baseline_p99:
        print(
            f"REJECT: p99 latency {opt_p99:.1f}ms > baseline {baseline_p99:.1f}ms. "
            "Optimisation made inference slower.",
            file=sys.stderr,
        )
        return None

    # ── 5. Register ───────────────────────────────────────────────────────────
    if dry_run:
        print("DRY RUN: skipping registration.")
        return None

    latency_reduction = (
        ((baseline_p99 - opt_p99) / baseline_p99 * 100.0) if baseline_p99 > 0 else 0.0
    )

    exp_name = f"{model_name}-optimisation"
    mlflow.set_experiment(exp_name)

    with mlflow.start_run(run_name=f"{model_name}-{method}-{target}") as run:
        mlflow.log_metrics(optimised_metrics)
        mlflow.log_param("method", method)
        mlflow.log_param("target", target)
        mlflow.log_param("baseline_version", str(model_version))
        mlflow.log_param("accuracy_delta_pct", f"{delta:.4f}")
        mlflow.log_param("latency_p99_reduction_pct", f"{latency_reduction:.2f}")
        mlflow.log_artifacts(str(optimised_dir), artifact_path="optimised_model")

        opt_model_name = f"{model_name}-opt"
        mlflow.register_model(
            model_uri=f"runs:/{run.info.run_id}/optimised_model",
            name=opt_model_name,
        )
        client.set_registered_model_tag(
            opt_model_name,
            key="optimization_method",
            value=method,
        )
        client.set_registered_model_tag(
            opt_model_name,
            key="baseline_version",
            value=str(model_version),
        )
        print(f"✓ Registered optimised model: {opt_model_name}  run_id={run.info.run_id}")
        return run.info.run_id


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Model optimisation pipeline.")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-version", required=True, type=int)
    parser.add_argument(
        "--method",
        required=True,
        choices=["quantisation", "pruning", "distillation"],
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["cpu", "cuda-a100", "cuda-h100", "triton-onnx", "triton-trt"],
    )
    parser.add_argument(
        "--tracking-uri",
        default="http://localhost:5000",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    result = run_pipeline(
        model_name=args.model_name,
        model_version=args.model_version,
        method=args.method,
        target=args.target,
        tracking_uri=args.tracking_uri,
        dry_run=args.dry_run,
    )
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
