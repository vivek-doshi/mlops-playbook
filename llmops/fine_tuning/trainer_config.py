"""
Purpose:
    Shared configuration dataclass for all LLMOps fine-tuning trainers
    (LoRA, QLoRA, and full fine-tune).  Load from YAML with:

        config = LLMTrainerConfig(**yaml.safe_load(open("config.yaml")))

Usage:
    from llmops.fine_tuning.trainer_config import LLMTrainerConfig

Dependencies:
    dataclasses (stdlib)
    typing (stdlib)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LLMTrainerConfig:
    """Validated configuration object for LLM fine-tuning runs."""

    # ── Model identification ──────────────────────────────────────────────
    model_name: str
    """MLflow registered model name (used as experiment prefix)."""

    base_model: str
    """HuggingFace model ID or local path to the pre-trained base model."""

    # ── Dataset ───────────────────────────────────────────────────────────
    dataset_path: str
    """HuggingFace dataset ID or local path to the training data."""

    text_column: str = "text"
    """Column name containing the input text within the dataset."""

    eval_dataset_path: Optional[str] = None
    """Optional separate evaluation dataset.  If None, 5% of training set is used."""

    # ── Training hyperparameters ──────────────────────────────────────────
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    max_seq_length: int = 2048

    # ── LoRA / QLoRA specific ─────────────────────────────────────────────
    lora_r: int = 16
    """LoRA attention dimension (rank)."""

    lora_alpha: int = 32
    """LoRA scaling factor."""

    lora_dropout: float = 0.05
    """LoRA dropout probability."""

    lora_target_modules: Optional[List[str]] = None
    """List of modules to apply LoRA adapters to.  Defaults to ['q_proj', 'v_proj']."""

    # ── Output ────────────────────────────────────────────────────────────
    output_dir: str = "outputs"
    """Directory to write checkpoints and adapter artifacts."""
