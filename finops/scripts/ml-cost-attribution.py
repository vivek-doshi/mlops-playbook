"""
Purpose:
    ML cost attribution script.  Reads Kubernetes pod metrics from the
    cluster, joins them to the pod's required cost labels (cost-center,
    team, model-name, environment), and writes per-model GPU/CPU/memory
    spend estimates to a structured JSON output.

    Cost is estimated using the instance rates defined in
    finops/data/instance-rates.yaml.  This script does NOT call a cloud
    billing API — it is purely a usage-based estimate.

Usage:
    python finops/scripts/ml-cost-attribution.py \\
        --rates-file  finops/data/instance-rates.yaml \\
        --output-path finops/reports/cost-attribution.json \\
        --lookback-hours 24

Dependencies:
    kubernetes>=29.0
    pyyaml>=6.0
    pandas>=2.0
    prometheus-api-client>=0.5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

# Kubernetes client is optional — falls back to in-cluster config.
try:
    from kubernetes import client as k8s_client, config as k8s_config
    HAS_K8S = True
except ImportError:
    HAS_K8S = False

# Prometheus API client is optional — used for actual resource usage.
try:
    from prometheus_api_client import PrometheusConnect
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


# --------------------------------------------------------------------------- #
# Required cost labels — pods missing these are flagged but not skipped.
# --------------------------------------------------------------------------- #
REQUIRED_LABELS = ["cost-center", "team", "model-name", "environment"]


# --------------------------------------------------------------------------- #
# Rate loading
# --------------------------------------------------------------------------- #


def _load_rates(rates_path: str) -> dict[str, float]:
    """
    Load instance rates from YAML.
    Expected structure:
        cpu_per_core_per_hour: 0.048
        memory_per_gib_per_hour: 0.006
        gpu_per_unit_per_hour: 2.10
    """
    with open(rates_path) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Kubernetes pod discovery
# --------------------------------------------------------------------------- #


def _list_ml_pods(
    namespace_pattern: str = "",
) -> list[dict[str, Any]]:
    """
    List pods from all namespaces whose name matches the pattern
    (e.g. '*-dev', '*-staging', '*-prod').
    Returns a list of pod metadata dicts.
    """
    if not HAS_K8S:
        print("WARNING: kubernetes package not installed — using mock pod data.", file=sys.stderr)
        return []

    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        k8s_config.load_kube_config()

    v1 = k8s_client.CoreV1Api()
    pods_response = v1.list_pod_for_all_namespaces(watch=False)

    records: list[dict[str, Any]] = []
    for pod in pods_response.items:
        ns = pod.metadata.namespace
        if namespace_pattern and namespace_pattern not in ns:
            continue
        labels = pod.metadata.labels or {}
        resources = {}
        if pod.spec.containers:
            for container in pod.spec.containers:
                req = container.resources.requests or {}
                resources["cpu_request"] = req.get("cpu", "0")
                resources["memory_request"] = req.get("memory", "0")
                resources["gpu_request"] = req.get("nvidia.com/gpu", "0")

        records.append(
            {
                "name": pod.metadata.name,
                "namespace": ns,
                "phase": pod.status.phase,
                "labels": labels,
                "resources": resources,
                "missing_labels": [l for l in REQUIRED_LABELS if l not in labels],
            }
        )
    return records


# --------------------------------------------------------------------------- #
# Resource parsing helpers
# --------------------------------------------------------------------------- #


def _parse_cpu(cpu_str: str) -> float:
    """Convert Kubernetes CPU string to cores (float)."""
    if not cpu_str or cpu_str == "0":
        return 0.0
    if cpu_str.endswith("m"):
        return float(cpu_str[:-1]) / 1000.0
    return float(cpu_str)


def _parse_memory_gib(mem_str: str) -> float:
    """Convert Kubernetes memory string to GiB (float)."""
    if not mem_str or mem_str == "0":
        return 0.0
    units = {"Ki": 1 / 1024**2, "Mi": 1 / 1024, "Gi": 1.0, "Ti": 1024.0}
    for suffix, factor in units.items():
        if mem_str.endswith(suffix):
            return float(mem_str[: -len(suffix)]) * factor
    return float(mem_str) / (1024**3)


# --------------------------------------------------------------------------- #
# Cost computation
# --------------------------------------------------------------------------- #


def _compute_cost(
    pods: list[dict[str, Any]],
    rates: dict[str, float],
    lookback_hours: float,
) -> dict[str, Any]:
    """
    Aggregate estimated cost per (cost-center, team, model-name, environment).
    """
    cpu_rate = rates.get("cpu_per_core_per_hour", 0.048)
    mem_rate = rates.get("memory_per_gib_per_hour", 0.006)
    gpu_rate = rates.get("gpu_per_unit_per_hour", 2.10)

    rows: list[dict[str, Any]] = []
    untagged_pods: list[str] = []

    for pod in pods:
        if pod.get("phase") not in ("Running", "Pending"):
            continue
        labels = pod.get("labels", {})
        missing = pod.get("missing_labels", [])
        if missing:
            untagged_pods.append(f"{pod['namespace']}/{pod['name']} missing: {missing}")

        res = pod.get("resources", {})
        cpu_cores = _parse_cpu(res.get("cpu_request", "0"))
        mem_gib = _parse_memory_gib(res.get("memory_request", "0"))
        gpu_units = float(res.get("gpu_request", "0"))

        cost_usd = (
            cpu_cores * cpu_rate * lookback_hours
            + mem_gib * mem_rate * lookback_hours
            + gpu_units * gpu_rate * lookback_hours
        )

        rows.append(
            {
                "cost_center": labels.get("cost-center", "unknown"),
                "team": labels.get("team", "unknown"),
                "model_name": labels.get("model-name", "unknown"),
                "environment": labels.get("environment", "unknown"),
                "namespace": pod["namespace"],
                "pod_name": pod["name"],
                "cpu_cores": round(cpu_cores, 4),
                "memory_gib": round(mem_gib, 4),
                "gpu_units": gpu_units,
                "cost_usd": round(cost_usd, 4),
                "lookback_hours": lookback_hours,
            }
        )

    if not rows:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "lookback_hours": lookback_hours,
            "summary": [],
            "untagged_pods": untagged_pods,
            "total_cost_usd": 0.0,
        }

    df = pd.DataFrame(rows)
    summary = (
        df.groupby(["cost_center", "team", "model_name", "environment"])
        .agg(
            total_cost_usd=("cost_usd", "sum"),
            total_cpu_cores=("cpu_cores", "sum"),
            total_memory_gib=("memory_gib", "sum"),
            total_gpu_units=("gpu_units", "sum"),
            pod_count=("pod_name", "count"),
        )
        .reset_index()
        .round(4)
        .to_dict(orient="records")
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookback_hours": lookback_hours,
        "summary": summary,
        "untagged_pods": untagged_pods,
        "total_cost_usd": round(df["cost_usd"].sum(), 4),
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def attribute_costs(
    rates_file: str,
    output_path: str,
    lookback_hours: float = 24.0,
    namespace_pattern: str = "",
) -> dict[str, Any]:
    rates = _load_rates(rates_file)
    pods = _list_ml_pods(namespace_pattern)
    report = _compute_cost(pods, rates, lookback_hours)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"Cost attribution report written to: {output_path}")
    print(f"Total estimated cost (USD): {report['total_cost_usd']}")
    if report["untagged_pods"]:
        print(f"WARNING: {len(report['untagged_pods'])} pods missing required cost labels:")
        for p in report["untagged_pods"]:
            print(f"  {p}")
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate ML workload cost by Kubernetes pod label attribution."
    )
    parser.add_argument(
        "--rates-file", default="finops/data/instance-rates.yaml"
    )
    parser.add_argument(
        "--output-path", default="finops/reports/cost-attribution.json"
    )
    parser.add_argument("--lookback-hours", type=float, default=24.0)
    parser.add_argument(
        "--namespace-pattern",
        default="",
        help="Filter namespaces by substring (e.g. '-prod')",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    attribute_costs(
        rates_file=args.rates_file,
        output_path=args.output_path,
        lookback_hours=args.lookback_hours,
        namespace_pattern=args.namespace_pattern,
    )
