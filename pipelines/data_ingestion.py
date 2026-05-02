import argparse
import pandas as pd
from src.data.make_dataset import generate_synthetic_data
from src.data.validation import validate_data

def run_ingestion(output_path: str):
    print("Starting data ingestion...")
    df = generate_synthetic_data(output_path)
    print("Validating ingested data...")
    if validate_data(df):
        print("Data ingestion and validation completed successfully.")
    else:
        print("Data ingestion failed during validation.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run data ingestion pipeline.")
    parser.add_argument("--output_path", type=str, default="data/raw/dataset.csv", help="Path to save the generated data.")
    args = parser.parse_args()

    run_ingestion(args.output_path)
