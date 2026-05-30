"""
Purpose:
    Preference dataset builder for RLHF training.  Converts raw human-feedback
    annotations (CSV or JSONL) into a HuggingFace Dataset of
    (prompt, chosen, rejected) triples compatible with TRL RewardTrainer and
    the PPO trainer.

    The resulting dataset is saved locally as a Parquet file and optionally
    pushed to the HuggingFace Hub.

Usage:
    python llmops/rlhf/preference_dataset.py \\
        --input-path  data/annotations.jsonl \\
        --output-path data/preference_dataset/ \\
        --format      jsonl

Dependencies:
    datasets>=2.18
    pyyaml>=6.0
    pandas>=2.0
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    import pandas as pd
    from datasets import Dataset
except ImportError as exc:
    print(
        f"ERROR: {exc}\nInstall with: pip install datasets pandas",
        file=sys.stderr,
    )
    sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# Loaders
# ──────────────────────────────────────────────────────────────────────────────

def _load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file as a list of dicts."""
    records = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _load_csv(path: Path) -> list[dict]:
    """Load a CSV file.  Required columns: prompt, chosen, rejected."""
    records = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            records.append(dict(row))
    return records


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

_REQUIRED_COLUMNS = {"prompt", "chosen", "rejected"}


def _validate_records(records: list[dict]) -> list[dict]:
    """Filter out records missing required columns and warn about them."""
    valid = []
    for i, rec in enumerate(records):
        missing = _REQUIRED_COLUMNS - rec.keys()
        if missing:
            print(
                f"  SKIP row {i}: missing fields {missing}",
                file=sys.stderr,
            )
            continue
        if not rec["prompt"].strip() or not rec["chosen"].strip() or not rec["rejected"].strip():
            print(f"  SKIP row {i}: empty prompt, chosen, or rejected field.", file=sys.stderr)
            continue
        valid.append(rec)
    return valid


# ──────────────────────────────────────────────────────────────────────────────
# Builder
# ──────────────────────────────────────────────────────────────────────────────

def build_preference_dataset(
    input_path: Path,
    output_path: Path,
    fmt: str = "jsonl",
    hub_repo: str | None = None,
) -> Dataset:
    """
    Build and save a preference dataset.

    Parameters
    ----------
    input_path : Path
        Source annotation file (JSONL or CSV).
    output_path : Path
        Directory to save the Parquet dataset.
    fmt : str
        Input format: 'jsonl' or 'csv'.
    hub_repo : str | None
        Optional HuggingFace Hub repository ID to push the dataset to.
    """
    if fmt == "jsonl":
        records = _load_jsonl(input_path)
    elif fmt == "csv":
        records = _load_csv(input_path)
    else:
        raise ValueError(f"Unsupported format: '{fmt}'. Use 'jsonl' or 'csv'.")

    print(f"Loaded {len(records)} annotation records from {input_path}.")
    valid = _validate_records(records)
    print(f"Valid records after validation: {len(valid)}")

    if not valid:
        print("ERROR: No valid records to build dataset from.", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(valid, columns=["prompt", "chosen", "rejected"])
    dataset = Dataset.from_pandas(df, preserve_index=False)

    output_path.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(output_path))
    print(f"✓ Preference dataset saved to {output_path}  ({len(dataset)} examples).")

    if hub_repo:
        dataset.push_to_hub(hub_repo)
        print(f"✓ Pushed to HuggingFace Hub: {hub_repo}")

    return dataset


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a preference dataset for RLHF.")
    parser.add_argument("--input-path", required=True, help="Path to annotation file.")
    parser.add_argument("--output-path", required=True, help="Directory to write the dataset.")
    parser.add_argument(
        "--format",
        choices=["jsonl", "csv"],
        default="jsonl",
        dest="fmt",
        help="Input annotation file format (default: jsonl).",
    )
    parser.add_argument(
        "--hub-repo",
        default=None,
        help="Optional HuggingFace Hub repo ID to push the dataset to.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    build_preference_dataset(
        input_path=Path(args.input_path),
        output_path=Path(args.output_path),
        fmt=args.fmt,
        hub_repo=args.hub_repo,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
