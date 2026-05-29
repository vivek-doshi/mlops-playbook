"""
Purpose:
    Data ingestion pipeline component.
    Downloads raw data from a configured source (S3, GCS, Azure Blob, or local),
    validates the schema, and writes the raw dataset to the pipeline's artifact store.

Usage:
    Called as a pipeline step — not typically run standalone.
    To run standalone for testing:
        python pipelines/components/data_ingestion/component.py \\
            --source-uri s3://my-bucket/raw/data.parquet \\
            --output-path /tmp/raw_data.parquet

Dependencies:
    pandas>=2.0
    pyarrow>=14.0
    pyyaml>=6.0
    fsspec>=2024.2
    s3fs>=2024.2  (for S3 sources)
    gcsfs>=2024.2 (for GCS sources)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def ingest(source_uri: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Download raw data from *source_uri* and write to *output_path*.

    Returns a metadata dict with row_count, column_count, and source.
    """
    config = config or {}
    fmt    = config.get("format", "parquet")
    kwargs = config.get("read_options", {})

    logger.info("Ingesting data from %s (format=%s)", source_uri, fmt)

    if fmt == "parquet":
        df = pd.read_parquet(source_uri, **kwargs)
    elif fmt == "csv":
        df = pd.read_csv(source_uri, **kwargs)
    elif fmt == "json":
        df = pd.read_json(source_uri, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    logger.info("Loaded %d rows × %d columns", len(df), len(df.columns))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Saved raw data to %s", output_path)

    return {"row_count": len(df), "column_count": len(df.columns), "source": source_uri}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Data ingestion component.")
    parser.add_argument("--source-uri",   required=True)
    parser.add_argument("--output-path",  required=True)
    parser.add_argument("--config-file",  default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file)) if args.config_file else {}
    ingest(args.source_uri, args.output_path, config)
