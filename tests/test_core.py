import pytest
from fastapi.testclient import TestClient
import pandas as pd
from src.data.make_dataset import generate_synthetic_data
from src.data.validation import validate_data
from src.inference.api import app

client = TestClient(app)

def test_data_generation(tmp_path):
    output_path = tmp_path / "dataset.csv"
    df = generate_synthetic_data(str(output_path), n_samples=50)

    assert len(df) == 50
    assert "target" in df.columns
    assert output_path.exists()

def test_data_validation(tmp_path):
    output_path = tmp_path / "dataset.csv"
    df = generate_synthetic_data(str(output_path), n_samples=50)
    is_valid = validate_data(df)
    assert is_valid == True

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
