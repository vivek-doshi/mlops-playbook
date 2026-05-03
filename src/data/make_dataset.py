import os

import pandas as pd
from sklearn.datasets import make_classification


def generate_synthetic_data(output_path: str, n_samples: int = 1000) -> pd.DataFrame:
    """
    Generates a synthetic dataset for classification.

    EDUCATIONAL NOTE:
    In a real-world scenario, this function would connect to a database (like PostgreSQL or Snowflake)
    or cloud storage (like S3) using credentials to fetch your organization's real data.
    We use synthetic data here purely so the repository runs out-of-the-box.
    """
    X, y = make_classification(
        n_samples=n_samples,
        n_features=10,
        n_informative=5,
        n_redundant=2,
        random_state=42,
    )

    # Create DataFrame
    feature_names = [f"feature_{i}" for i in range(10)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Synthetic data generated and saved to {output_path}")
    return df


if __name__ == "__main__":
    generate_synthetic_data("data/raw/dataset.csv")
