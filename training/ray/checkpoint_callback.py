"""
Purpose:
    Ray Train checkpoint save/restore callback for distributed training.
    Wraps the Ray Train checkpoint API into a Keras/PyTorch-Trainer-style
    callback so that training scripts can checkpoint without boilerplate.

Usage:
    from training.ray.checkpoint_callback import CheckpointCallback

    callback = CheckpointCallback(
        checkpoint_dir="/checkpoints",
        keep_last_n=3,
    )
    # Call inside the training loop:
    callback.on_epoch_end(epoch=5, metrics={"val_loss": 0.23}, model=model)

Dependencies:
    ray[train]>=2.9
    torch>=2.2
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

try:
    from ray.train import Checkpoint, get_context
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

logger = logging.getLogger(__name__)


class CheckpointCallback:
    """
    Checkpoint callback for Ray Train distributed training loops.

    Saves model state, optimiser state, epoch number, and custom metrics.
    Keeps only the last ``keep_last_n`` checkpoints on local disk; older
    ones are deleted automatically.

    Parameters
    ----------
    checkpoint_dir:
        Base directory for checkpoint storage.  Each epoch creates a
        sub-directory named ``epoch-<N>``.
    keep_last_n:
        Number of most recent checkpoints to retain locally (default 3).
    metric_key:
        Metric used to determine the "best" checkpoint.
    mode:
        ``"min"`` or ``"max"`` for ``metric_key`` (default ``"min"``).
    """

    def __init__(
        self,
        checkpoint_dir: str = "/checkpoints",
        keep_last_n: int = 3,
        metric_key: str = "val_loss",
        mode: str = "min",
    ) -> None:
        self.checkpoint_dir  = Path(checkpoint_dir)
        self.keep_last_n     = keep_last_n
        self.metric_key      = metric_key
        self.mode            = mode
        self._checkpoints: list[Path] = []
        self._best_metric: float | None = None
        self._best_checkpoint: Path | None = None

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def on_epoch_end(
        self,
        epoch: int,
        metrics: dict[str, float],
        model: nn.Module,
        optimiser: torch.optim.Optimizer | None = None,
    ) -> None:
        """
        Save checkpoint at the end of an epoch and report to Ray Train.

        Parameters
        ----------
        epoch:
            Current epoch number (0-based).
        metrics:
            Dictionary of metric name → value.
        model:
            PyTorch model to checkpoint.
        optimiser:
            Optional optimiser whose state should be included.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path  = Path(tmpdir) / "checkpoint.pt"
            meta_path  = Path(tmpdir) / "meta.json"

            state: dict[str, Any] = {
                "epoch":       epoch,
                "model_state": model.module.state_dict()
                if hasattr(model, "module")
                else model.state_dict(),
            }
            if optimiser is not None:
                state["optim_state"] = optimiser.state_dict()

            torch.save(state, ckpt_path)

            with open(meta_path, "w") as fh:
                json.dump({"epoch": epoch, "metrics": metrics}, fh, indent=2)

            # Copy to persistent storage.
            epoch_dir = self.checkpoint_dir / f"epoch-{epoch:05d}"
            if epoch_dir.exists():
                shutil.rmtree(epoch_dir)
            shutil.copytree(tmpdir, epoch_dir)
            self._checkpoints.append(epoch_dir)
            logger.info("Checkpoint saved: %s", epoch_dir)

            # Track best checkpoint.
            self._update_best(epoch_dir, metrics)

            # Report to Ray Train if running inside a worker.
            if HAS_RAY:
                try:
                    checkpoint = Checkpoint.from_directory(tmpdir)
                    from ray import train as ray_train  # noqa: PLC0415
                    ray_train.report(metrics=metrics, checkpoint=checkpoint)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.debug("Ray Train report skipped (%s)", exc)

        # Prune old checkpoints.
        self._prune()

    def restore(
        self,
        model: nn.Module,
        optimiser: torch.optim.Optimizer | None = None,
        checkpoint_dir: str | None = None,
    ) -> int:
        """
        Restore model (and optionally optimiser) from the most recent checkpoint.

        Returns the epoch number of the restored checkpoint, or -1 if none found.
        """
        search_dir = Path(checkpoint_dir) if checkpoint_dir else self.checkpoint_dir
        candidates = sorted(search_dir.glob("epoch-*"), reverse=True)

        if not candidates:
            logger.info("No checkpoints found in %s — starting fresh.", search_dir)
            return -1

        latest = candidates[0]
        ckpt_path = latest / "checkpoint.pt"

        state = torch.load(ckpt_path, map_location="cpu")
        model.load_state_dict(state["model_state"])

        if optimiser is not None and "optim_state" in state:
            optimiser.load_state_dict(state["optim_state"])

        epoch = state.get("epoch", -1)
        logger.info("Restored checkpoint from %s (epoch %d)", latest, epoch)
        return epoch

    # ---------------------------------------------------------------------- #
    # Private helpers
    # ---------------------------------------------------------------------- #

    def _update_best(self, epoch_dir: Path, metrics: dict[str, float]) -> None:
        value = metrics.get(self.metric_key)
        if value is None:
            return

        is_better = (
            self._best_metric is None
            or (self.mode == "min" and value < self._best_metric)
            or (self.mode == "max" and value > self._best_metric)
        )

        if is_better:
            self._best_metric = value
            self._best_checkpoint = epoch_dir
            best_link = self.checkpoint_dir / "best"
            if best_link.exists() or best_link.is_symlink():
                best_link.unlink()
            best_link.symlink_to(epoch_dir.name)
            logger.info(
                "New best checkpoint: %s=%.4f at %s",
                self.metric_key,
                value,
                epoch_dir,
            )

    def _prune(self) -> None:
        while len(self._checkpoints) > self.keep_last_n:
            old = self._checkpoints.pop(0)
            if old != self._best_checkpoint and old.exists():
                shutil.rmtree(old)
                logger.debug("Pruned old checkpoint: %s", old)
