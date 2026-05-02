"""
Batch inference pipeline — offline scoring via the inference API.

Usage:
    python pipelines/batch_inference_pipeline.py \
        --input data/processed/dataset.csv \
        --output outputs/predictions.csv \
        --api-url http://localhost:8000

Or for direct (no API) scoring:
    python pipelines/batch_inference_pipeline.py \
        --input data/processed/dataset.csv \
        --output outputs/predictions.csv \
        --direct
"""

import argparse
import os
from pathlib import Path

import joblib
import pandas as pd
import requests

from src.utils.logger import logger


def batch_predict_via_api(df: pd.DataFrame, api_url: str, chunk_size: int = 500) -> list:
    """Send data to the /predict/batch endpoint in chunks."""
    all_predictions = []
    feature_cols = [c for c in df.columns if c != "target"]

    for i in range(0, len(df), chunk_size):
        chunk = df[feature_cols].iloc[i:i + chunk_size]
        payload = {"requests": chunk.to_dict(orient="records")}
        resp = requests.post(f"{api_url}/predict/batch", json=payload, timeout=30)
        resp.raise_for_status()
        all_predictions.extend(resp.json()["predictions"])
        logger.info(f"Scored rows {i}–{i + len(chunk)} of {len(df)}")

    return all_predictions


def batch_predict_direct(df: pd.DataFrame) -> list:
    """Score directly using saved model artifacts (no API required)."""
    model_path = os.getenv("MODEL_PATH", "models/model.pkl")
    pipeline_path = os.getenv("PIPELINE_PATH", "models/feature_pipeline.pkl")

    model = joblib.load(model_path)
    pipeline = joblib.load(pipeline_path)

    feature_cols = [c for c in df.columns if c != "target"]
    X = pipeline.transform(df[feature_cols])
    return [int(p) for p in model.predict(X)]


def run_batch_inference(input_path: str, output_path: str, api_url: str = None, direct: bool = False):
    logger.info(f"Loading input data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")

    if direct:
        logger.info("Running direct batch inference (no API)")
        predictions = batch_predict_direct(df)
    else:
        logger.info(f"Running batch inference via API at {api_url}")
        predictions = batch_predict_via_api(df, api_url)

    df["prediction"] = predictions
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path} ({len(predictions)} rows)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data/processed/dataset.csv")
    parser.add_argument("--output", type=str, default="outputs/predictions.csv")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000")
    parser.add_argument("--direct", action="store_true", help="Score directly without the API")
    args = parser.parse_args()

    run_batch_inference(args.input, args.output, args.api_url, args.direct)
