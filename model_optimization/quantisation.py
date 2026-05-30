"""
Purpose:
    Model quantisation via ONNX Runtime (INT8, FP16) and TensorRT (INT8, FP16).
    Converts an MLflow-registered model to an optimised ONNX or TensorRT engine
    suitable for CPU or NVIDIA GPU serving.

Usage:
    from model_optimization.quantisation import run_quantisation
    run_quantisation(model_uri="models:/my-model/3", output_dir=Path("out/"), target="cpu")

    # or CLI:
    python model_optimization/quantisation.py \\
        --model-uri   models:/my-model/3 \\
        --output-dir  outputs/quantised/ \\
        --target      cpu \\
        --precision   int8

Dependencies:
    mlflow>=2.14
    onnx>=1.16
    onnxruntime>=1.18
    optimum>=1.20   (for HuggingFace model export)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import mlflow
    import onnx
    import onnxruntime as ort
    from onnxruntime.quantization import (
        QuantType,
        quantize_dynamic,
        quantize_static,
    )
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install mlflow onnx onnxruntime optimum",
        file=sys.stderr,
    )
    sys.exit(1)


def _download_model(model_uri: str, local_dir: Path) -> Path:
    """Download an MLflow model artifact to a local directory and return its path."""
    local_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = mlflow.artifacts.download_artifacts(model_uri, dst_path=str(local_dir))
    return Path(artifact_path)


def _find_onnx_path(model_dir: Path) -> Path | None:
    """Locate an existing .onnx file in the model directory."""
    for f in model_dir.rglob("*.onnx"):
        return f
    return None


def quantise_dynamic(onnx_path: Path, output_path: Path, weight_type: QuantType) -> Path:
    """Apply dynamic quantisation (INT8 weights, float32 activations)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    quantize_dynamic(str(onnx_path), str(output_path), weight_type=weight_type)
    print(f"  ✓ Dynamic quantisation → {output_path}")
    return output_path


def export_to_onnx(model_dir: Path, output_path: Path) -> Path:
    """
    Export a PyTorch / HuggingFace model to ONNX using Optimum.
    Returns the path to the exported .onnx file.
    """
    try:
        from optimum.exporters.onnx import main_export
    except ImportError as exc:
        print(f"ERROR: {exc}\nInstall: pip install optimum[onnxruntime]", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)
    main_export(
        model_name_or_path=str(model_dir),
        output=str(output_path),
        task="text-classification",  # override at call site if needed
    )
    onnx_file = next(output_path.glob("*.onnx"), None)
    if onnx_file is None:
        print("ERROR: Optimum export did not produce an ONNX file.", file=sys.stderr)
        sys.exit(1)
    return onnx_file


def run_quantisation(
    model_uri: str,
    output_dir: Path,
    target: str = "cpu",
    precision: str = "int8",
) -> Path:
    """
    Run end-to-end quantisation for the given model URI.

    Parameters
    ----------
    model_uri : str
        MLflow model URI (e.g. ``models:/my-model/3``).
    output_dir : Path
        Directory to write quantised model artefacts.
    target : str
        Hardware target: cpu | cuda-a100 | cuda-h100 | triton-onnx | triton-trt.
    precision : str
        Quantisation precision: int8 | fp16.

    Returns
    -------
    Path
        Path to the quantised ONNX model file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = output_dir / "staging"

    print(f"Downloading model: {model_uri}")
    model_dir = _download_model(model_uri, staging_dir)

    onnx_path = _find_onnx_path(model_dir)
    if onnx_path is None:
        print("No ONNX file found — exporting from PyTorch/HuggingFace...")
        onnx_dir = output_dir / "onnx_export"
        onnx_path = export_to_onnx(model_dir, onnx_dir)

    if target in ("triton-trt", "cuda-a100", "cuda-h100"):
        # TensorRT path — defer to trtexec or tensorrt Python API
        return _quantise_tensorrt(onnx_path, output_dir, precision)

    # ONNX Runtime path
    quant_output = output_dir / f"model_{precision}.onnx"
    weight_type = QuantType.QUInt8 if precision == "int8" else QuantType.QInt8
    return quantise_dynamic(onnx_path, quant_output, weight_type)


def _quantise_tensorrt(onnx_path: Path, output_dir: Path, precision: str) -> Path:
    """Invoke trtexec to build a TensorRT engine from ONNX."""
    import subprocess  # noqa: PLC0415

    engine_path = output_dir / f"model_{precision}.trt"
    precision_flag = "--int8" if precision == "int8" else "--fp16"

    cmd = [
        "trtexec",
        f"--onnx={onnx_path}",
        f"--saveEngine={engine_path}",
        precision_flag,
        "--explicitBatch",
    ]
    print(f"  Running trtexec: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        print(f"  trtexec stderr: {result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"  ✓ TensorRT engine → {engine_path}")
    return engine_path


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Quantise a model to ONNX or TensorRT.")
    parser.add_argument("--model-uri", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--target",
        choices=["cpu", "cuda-a100", "cuda-h100", "triton-onnx", "triton-trt"],
        default="cpu",
    )
    parser.add_argument("--precision", choices=["int8", "fp16"], default="int8")
    parser.add_argument("--tracking-uri", default="http://localhost:5000")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    mlflow.set_tracking_uri(args.tracking_uri)
    run_quantisation(
        model_uri=args.model_uri,
        output_dir=Path(args.output_dir),
        target=args.target,
        precision=args.precision,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
