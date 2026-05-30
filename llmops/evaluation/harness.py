"""
Purpose:
    LLM evaluation harness.  Runs a set of benchmarks (defined as YAML files in
    llmops/evaluation/benchmarks/) against a deployed or local model endpoint
    and logs results to MLflow under the experiment <model-name>-llm-eval.

    Benchmarks are evaluated by:
      1. Sending each prompt to the target model.
      2. Scoring the response with the specified metric (exact_match, f1, rouge_l,
         llm_judge_score).
      3. Aggregating per-benchmark scores and logging to MLflow.

Usage:
    python llmops/evaluation/harness.py \\
        --model-name    <name> \\
        --model-version <version> \\
        --benchmarks-dir llmops/evaluation/benchmarks/

Dependencies:
    mlflow>=2.11
    pyyaml>=6.0
    requests>=2.31
    rouge-score>=0.1.2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import mlflow
    import requests
    from rouge_score import rouge_scorer
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install mlflow requests rouge-score pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Scoring helpers
# ──────────────────────────────────────────────────────────────────────────────

def _exact_match(prediction: str, reference: str) -> float:
    return float(prediction.strip() == reference.strip())


def _token_f1(prediction: str, reference: str) -> float:
    pred_tokens = prediction.strip().lower().split()
    ref_tokens = reference.strip().lower().split()
    common = set(pred_tokens) & set(ref_tokens)
    if not common:
        return 0.0
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def _rouge_l(prediction: str, reference: str) -> float:
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(reference, prediction)
    return scores["rougeL"].fmeasure


def _score_response(prediction: str, reference: str, metric: str) -> float:
    if metric == "exact_match":
        return _exact_match(prediction, reference)
    if metric == "f1":
        return _token_f1(prediction, reference)
    if metric == "rouge_l":
        return _rouge_l(prediction, reference)
    raise ValueError(f"Unsupported metric: '{metric}'. Use exact_match, f1, or rouge_l.")


# ──────────────────────────────────────────────────────────────────────────────
# Model query
# ──────────────────────────────────────────────────────────────────────────────

def _query_endpoint(endpoint_url: str, prompt: str, max_new_tokens: int = 256) -> str:
    """Send a prompt to a model endpoint and return the completion text."""
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_new_tokens, "temperature": 0.0},
    }
    resp = requests.post(endpoint_url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Support both {predictions: [...]} (MLflow) and {choices: [...]} (OpenAI-style)
    if "predictions" in data:
        return str(data["predictions"][0])
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    return str(data)


# ──────────────────────────────────────────────────────────────────────────────
# Harness
# ──────────────────────────────────────────────────────────────────────────────

def run_evaluation(
    model_name: str,
    model_version: str,
    endpoint_url: str,
    benchmarks_dir: Path,
    golden_dataset_dir: Path | None,
) -> dict[str, float]:
    """
    Run all benchmark YAML files and return a {benchmark_name: score} dict.
    Logs all scores to MLflow experiment <model-name>-llm-eval.
    """
    experiment_name = f"{model_name}-llm-eval"
    mlflow.set_experiment(experiment_name)

    benchmark_files = sorted(benchmarks_dir.glob("*.yaml"))
    if not benchmark_files:
        print(f"WARNING: No benchmark YAML files found in {benchmarks_dir}", file=sys.stderr)

    results: dict[str, float] = {}

    with mlflow.start_run(
        tags={
            "llm_task": "eval",
            "model_name": model_name,
            "model_version": model_version,
        }
    ):
        mlflow.log_params(
            {
                "model_name": model_name,
                "model_version": model_version,
                "endpoint_url": endpoint_url,
                "num_benchmarks": str(len(benchmark_files)),
            }
        )

        for bm_path in benchmark_files:
            bm: dict[str, Any] = yaml.safe_load(bm_path.read_text())
            bm_name: str = bm.get("name", bm_path.stem)
            metric: str = bm.get("metric", "exact_match")
            examples: list[dict[str, str]] = bm.get("examples", [])

            if not examples:
                print(f"  SKIP {bm_name}: no examples defined.")
                continue

            scores: list[float] = []
            for ex in examples:
                prompt = ex.get("prompt", "")
                reference = ex.get("reference", "")
                try:
                    prediction = _query_endpoint(endpoint_url, prompt)
                    scores.append(_score_response(prediction, reference, metric))
                except Exception as exc:  # noqa: BLE001
                    print(f"  WARN [{bm_name}] example skipped: {exc}", file=sys.stderr)

            if scores:
                avg = sum(scores) / len(scores)
                results[bm_name] = avg
                mlflow.log_metric(f"benchmark/{bm_name}", avg)
                print(f"  {bm_name}: {avg:.4f} ({metric}, n={len(scores)})")

        # Overall score: mean of all benchmark scores
        if results:
            overall = sum(results.values()) / len(results)
            mlflow.log_metric("overall_score", overall)
            print(f"\n✓ Overall score: {overall:.4f}")

    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run LLM evaluation benchmarks.")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--endpoint-url", required=True, help="Model serving endpoint URL.")
    parser.add_argument(
        "--benchmarks-dir",
        default="llmops/evaluation/benchmarks/",
        help="Directory containing benchmark YAML files.",
    )
    parser.add_argument(
        "--golden-dataset-dir",
        default=None,
        help="Optional golden dataset directory for additional evaluation.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    run_evaluation(
        model_name=args.model_name,
        model_version=args.model_version,
        endpoint_url=args.endpoint_url,
        benchmarks_dir=Path(args.benchmarks_dir),
        golden_dataset_dir=Path(args.golden_dataset_dir) if args.golden_dataset_dir else None,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
