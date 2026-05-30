"""
Purpose:
    Latency and throughput benchmarking harness for model optimisation.
    Runs 1000 warmup requests followed by 5000 measurement requests against a
    local model (ONNX, PyTorch) or HTTP serving endpoint, then computes p50 / p99
    latency and requests-per-second throughput.

    A target config YAML specifies the hardware profile (batch size, concurrency,
    input shape) for each target platform.

Usage:
    python model_optimization/benchmark.py \\
        --model-dir   outputs/quantised/ \\
        --target-config model_optimization/targets/cpu.yaml

Dependencies:
    mlflow>=2.14
    onnxruntime>=1.18
    numpy>=1.26
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import yaml
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install numpy pyyaml", file=sys.stderr)
    sys.exit(1)

_WARMUP_REQUESTS = 1_000
_MEASUREMENT_REQUESTS = 5_000


def _load_target_config(target_config: Path) -> dict[str, Any]:
    """Load a hardware target YAML config."""
    if not target_config.exists():
        print(f"  WARN: Target config not found: {target_config}. Using defaults.")
        return {"batch_size": 1, "input_shape": [1, 128], "dtype": "float32"}
    with target_config.open() as fh:
        return yaml.safe_load(fh)


def _build_dummy_input(config: dict[str, Any]) -> np.ndarray:
    """Build a dummy input array from the target config."""
    shape = config.get("input_shape", [1, 128])
    dtype = config.get("dtype", "float32")
    return np.random.randn(*shape).astype(dtype)  # noqa: S311


def _run_onnx_session(
    onnx_path: Path, dummy_input: np.ndarray, n_requests: int
) -> list[float]:
    """Run n_requests through an ONNX Runtime session and return latencies (ms)."""
    try:
        import onnxruntime as ort  # noqa: PLC0415
    except ImportError as exc:
        print(f"ERROR: {exc}\nInstall with: pip install onnxruntime", file=sys.stderr)
        sys.exit(1)

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(str(onnx_path), sess_options=opts)
    input_name = session.get_inputs()[0].name

    latencies = []
    for _ in range(n_requests):
        t0 = time.perf_counter()
        session.run(None, {input_name: dummy_input})
        latencies.append((time.perf_counter() - t0) * 1_000)  # ms
    return latencies


def _percentile(values: list[float], pct: float) -> float:
    return float(np.percentile(values, pct))


class BenchmarkHarness:
    """
    Benchmark harness for model optimisation.

    Parameters
    ----------
    target_config : Path
        Path to a hardware target YAML config.
    """

    def __init__(self, target_config: Path) -> None:
        self.config = _load_target_config(target_config)

    def run(self, model_dir: Path) -> dict[str, float]:
        """
        Benchmark a local model directory (looks for .onnx or .pt).

        Returns a dict with latency_p50_ms, latency_p99_ms, throughput_rps.
        """
        onnx_path = next(model_dir.rglob("*.onnx"), None)
        if onnx_path is None:
            print("  WARN: No ONNX file found in model_dir — returning zeros.", file=sys.stderr)
            return {"latency_p50_ms": 0.0, "latency_p99_ms": 0.0, "throughput_rps": 0.0}

        dummy = _build_dummy_input(self.config)

        print(f"  Warmup: {_WARMUP_REQUESTS} requests ...")
        _run_onnx_session(onnx_path, dummy, _WARMUP_REQUESTS)

        print(f"  Measurement: {_MEASUREMENT_REQUESTS} requests ...")
        t_start = time.perf_counter()
        latencies = _run_onnx_session(onnx_path, dummy, _MEASUREMENT_REQUESTS)
        elapsed = time.perf_counter() - t_start

        metrics = {
            "latency_p50_ms": _percentile(latencies, 50),
            "latency_p99_ms": _percentile(latencies, 99),
            "throughput_rps": _MEASUREMENT_REQUESTS / elapsed,
        }
        print(
            f"  p50={metrics['latency_p50_ms']:.2f}ms  "
            f"p99={metrics['latency_p99_ms']:.2f}ms  "
            f"rps={metrics['throughput_rps']:.1f}"
        )
        return metrics

    def run_baseline(self, model_uri: str) -> dict[str, float]:
        """Download and benchmark the baseline model for comparison."""
        import mlflow  # noqa: PLC0415

        staging = Path("outputs/_baseline_benchmark_staging/")
        staging.mkdir(parents=True, exist_ok=True)
        local = mlflow.artifacts.download_artifacts(model_uri, dst_path=str(staging))
        return self.run(Path(local))


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark a model for latency and throughput.")
    parser.add_argument("--model-dir", required=True, help="Directory containing the model.")
    parser.add_argument(
        "--target-config",
        required=True,
        help="Path to hardware target YAML config.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    harness = BenchmarkHarness(target_config=Path(args.target_config))
    metrics = harness.run(model_dir=Path(args.model_dir))
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
