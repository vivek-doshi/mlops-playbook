"""
Purpose:
    Data preprocessing pipeline component.
    Applies feature engineering, missing value imputation, and train/val/test
    splitting.  Writes processed splits to the pipeline artifact store.

Usage:
    Called as a pipeline step.  Standalone:
        python pipelines/components/preprocessing/component.py \\
            --input-path /tmp/raw_data.parquet \\
            --output-dir /tmp/processed/ \\
            --config-file pipelines/config/fraud-detection.yaml

Dependencies:
    pandas>=2.0
    scikit-learn>=1.4
    pyarrow>=14.0
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def preprocess(
    input_path: str,
    output_dir: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Preprocess raw data and write train/val/test splits.

    Returns metadata: split row counts and feature list.
    """
    df = pd.read_parquet(input_path)
    logger.info("Read %d rows from %s", len(df), input_path)

    label_col     = config.get("label_column", "label")
    test_size     = config.get("test_size",    0.1)
    val_size      = config.get("val_size",     0.1)
    scale_features = config.get("scale_features", True)
    drop_cols     = config.get("drop_columns", [])
    fill_strategy = config.get("fill_strategy", "median")

    # Drop unwanted columns.
    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Fill missing values.
    num_cols = df.select_dtypes("number").columns.tolist()
    if fill_strategy == "median":
        df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    elif fill_strategy == "mean":
        df[num_cols] = df[num_cols].fillna(df[num_cols].mean())
    elif fill_strategy == "zero":
        df[num_cols] = df[num_cols].fillna(0)

    feature_cols = [c for c in df.columns if c != label_col]

    # Split.
    X = df[feature_cols]
    y = df[label_col]

    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=(test_size + val_size), random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=test_size / (test_size + val_size), random_state=42
    )

    # Scale.
    if scale_features:
        scaler  = StandardScaler()
        X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_cols)
        X_val   = pd.DataFrame(scaler.transform(X_val),       columns=feature_cols)
        X_test  = pd.DataFrame(scaler.transform(X_test),      columns=feature_cols)

    # Write splits.
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name, X_split, y_split in [
        ("train", X_train, y_train),
        ("val",   X_val,   y_val),
        ("test",  X_test,  y_test),
    ]:
        split_df = X_split.reset_index(drop=True).copy()
        split_df[label_col] = y_split.reset_index(drop=True)
        split_df.to_parquet(out / f"{name}.parquet", index=False)

    logger.info("Splits: train=%d  val=%d  test=%d", len(X_train), len(X_val), len(X_test))

    return {
        "train_rows":  len(X_train),
        "val_rows":    len(X_val),
        "test_rows":   len(X_test),
        "feature_count": len(feature_cols),
        "features":    feature_cols,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocessing component.")
    parser.add_argument("--input-path",  required=True)
    parser.add_argument("--output-dir",  required=True)
    parser.add_argument("--config-file", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    preprocess(args.input_path, args.output_dir, config)
