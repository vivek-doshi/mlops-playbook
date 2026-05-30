"""
Purpose:
    Structured and unstructured pruning for PyTorch models.  Loads a model from
    the MLflow Model Registry, applies magnitude-based or structured pruning, and
    saves the sparse model to a local output directory for subsequent benchmarking.

Usage:
    python model_optimization/pruning.py \\
        --model-uri   models:/my-model/3 \\
        --output-dir  outputs/pruned/ \\
        --sparsity    0.3 \\
        --method      magnitude

Dependencies:
    mlflow>=2.14
    torch>=2.2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import mlflow
    import torch
    import torch.nn.utils.prune as torch_prune
except ImportError as exc:
    print(
        f"ERROR: {exc}\nInstall with: pip install mlflow torch",
        file=sys.stderr,
    )
    sys.exit(1)


def _load_pytorch_model(model_uri: str, staging_dir: Path) -> torch.nn.Module:
    """Download and load a PyTorch model from MLflow."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    local_path = mlflow.artifacts.download_artifacts(model_uri, dst_path=str(staging_dir))
    model = mlflow.pytorch.load_model(local_path)
    model.eval()
    return model


def apply_magnitude_pruning(
    model: torch.nn.Module,
    sparsity: float,
) -> torch.nn.Module:
    """
    Apply global unstructured magnitude-based pruning.

    Parameters
    ----------
    model : torch.nn.Module
        PyTorch model to prune.
    sparsity : float
        Target fraction of parameters to zero out (0.0–1.0).

    Returns
    -------
    torch.nn.Module
        Pruned model (weights zeroed, masks applied).
    """
    parameters_to_prune = [
        (module, "weight")
        for module in model.modules()
        if isinstance(module, (torch.nn.Linear, torch.nn.Conv2d))
    ]

    if not parameters_to_prune:
        print("  WARN: No Linear or Conv2d layers found for pruning.", file=sys.stderr)
        return model

    torch_prune.global_unstructured(
        parameters_to_prune,
        pruning_method=torch_prune.L1Unstructured,
        amount=sparsity,
    )

    # Remove pruning reparametrisation and make masks permanent
    for module, param_name in parameters_to_prune:
        torch_prune.remove(module, param_name)

    total = sum(p.numel() for p in model.parameters())
    zero = sum((p == 0).sum().item() for p in model.parameters())
    actual_sparsity = zero / total if total > 0 else 0.0
    print(f"  ✓ Magnitude pruning: actual sparsity = {actual_sparsity:.2%}")
    return model


def apply_structured_pruning(
    model: torch.nn.Module,
    sparsity: float,
) -> torch.nn.Module:
    """
    Apply structured (channel-level) L2-norm pruning on Conv2d and Linear layers.

    Parameters
    ----------
    model : torch.nn.Module
        PyTorch model to prune.
    sparsity : float
        Fraction of output channels/neurons to prune per layer.

    Returns
    -------
    torch.nn.Module
        Pruned model.
    """
    for module in model.modules():
        if isinstance(module, torch.nn.Conv2d):
            n_filters = max(1, int(module.out_channels * (1.0 - sparsity)))
            torch_prune.ln_structured(
                module, name="weight", amount=sparsity, n=2, dim=0
            )
            torch_prune.remove(module, "weight")
        elif isinstance(module, torch.nn.Linear):
            torch_prune.ln_structured(
                module, name="weight", amount=sparsity, n=2, dim=0
            )
            torch_prune.remove(module, "weight")
    print(f"  ✓ Structured pruning: sparsity per layer = {sparsity:.0%}")
    return model


def run_pruning(
    model_uri: str,
    output_dir: Path,
    sparsity: float = 0.3,
    method: str = "magnitude",
) -> Path:
    """
    Download, prune, and save a model.

    Parameters
    ----------
    model_uri : str
        MLflow model URI.
    output_dir : Path
        Directory to write the pruned model.
    sparsity : float
        Target sparsity level (default 0.30).
    method : str
        Pruning strategy: magnitude | structured.

    Returns
    -------
    Path
        Path where the pruned model was saved.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    staging = output_dir / "staging"

    print(f"Loading model: {model_uri}")
    model = _load_pytorch_model(model_uri, staging)

    if method == "magnitude":
        model = apply_magnitude_pruning(model, sparsity)
    elif method == "structured":
        model = apply_structured_pruning(model, sparsity)
    else:
        print(f"ERROR: Unknown pruning method '{method}'.", file=sys.stderr)
        sys.exit(1)

    save_path = output_dir / "pruned_model.pt"
    torch.save(model.state_dict(), save_path)
    print(f"  ✓ Pruned model saved to {save_path}")
    return save_path


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Prune a PyTorch model.")
    parser.add_argument("--model-uri", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sparsity", type=float, default=0.3)
    parser.add_argument("--method", choices=["magnitude", "structured"], default="magnitude")
    parser.add_argument("--tracking-uri", default="http://localhost:5000")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    mlflow.set_tracking_uri(args.tracking_uri)
    run_pruning(
        model_uri=args.model_uri,
        output_dir=Path(args.output_dir),
        sparsity=args.sparsity,
        method=args.method,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
