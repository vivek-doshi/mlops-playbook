"""
Purpose:
    Holdout-accuracy gate for online-learned model versions.
    Evaluates the updated model on a fixed holdout split and returns whether
    the model meets the accuracy threshold.  Accuracy drop > 2% triggers rollback.

Usage:
    validator = OnlineValidator(holdout_path="data/holdout.parquet")
    passed, metrics = validator.evaluate(model, baseline_accuracy=0.92)
    if not passed:
        rollback.execute(...)

Dependencies:
    scikit-learn>=1.4, pandas>=2.2
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_MAX_ACCURACY_DROP = 0.02  # 2%


class OnlineValidator:
    """
    Validates an online-updated model against a fixed holdout dataset.

    Parameters
    ----------
    holdout_path : str
        Path to parquet or CSV file with features and labels.
    label_col : str
        Column name for the target label.  Default "label".
    max_accuracy_drop : float
        Maximum allowed accuracy drop before recommending rollback.  Default 0.02.
    """

    def __init__(
        self,
        holdout_path: str,
        label_col: str = "label",
        max_accuracy_drop: float = _MAX_ACCURACY_DROP,
    ) -> None:
        self._holdout_path = holdout_path
        self._label_col = label_col
        self._max_accuracy_drop = max_accuracy_drop
        self._holdout: pd.DataFrame | None = None

    def _load_holdout(self) -> pd.DataFrame:
        if self._holdout is None:
            if self._holdout_path.endswith(".csv"):
                self._holdout = pd.read_csv(self._holdout_path)
            else:
                self._holdout = pd.read_parquet(self._holdout_path)
        return self._holdout

    def evaluate(
        self,
        model: Any,
        baseline_accuracy: float,
        feature_cols: list[str] | None = None,
    ) -> tuple[bool, dict[str, float]]:
        """
        Evaluate model on holdout data.

        Returns
        -------
        passed : bool
            True if accuracy drop is within threshold.
        metrics : dict
            accuracy, accuracy_drop, baseline_accuracy.
        """
        from sklearn.metrics import accuracy_score

        df = self._load_holdout()
        if feature_cols is None:
            feature_cols = [c for c in df.columns if c != self._label_col]

        X = df[feature_cols].values
        y_true = df[self._label_col].values
        y_pred = model.predict(X)
        accuracy = float(accuracy_score(y_true, y_pred))
        drop = baseline_accuracy - accuracy

        metrics = {
            "accuracy": accuracy,
            "baseline_accuracy": baseline_accuracy,
            "accuracy_drop": drop,
        }
        passed = drop <= self._max_accuracy_drop

        if passed:
            logger.info("Validation passed — accuracy=%.4f drop=%.4f.", accuracy, drop)
        else:
            logger.warning(
                "Validation FAILED — accuracy=%.4f drop=%.4f > threshold=%.4f. "
                "Rollback recommended.",
                accuracy,
                drop,
                self._max_accuracy_drop,
            )
        return passed, metrics
