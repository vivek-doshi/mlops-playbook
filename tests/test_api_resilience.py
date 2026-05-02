import pytest
from fastapi.testclient import TestClient

import src.inference.api as api
from src.inference.api import app


@pytest.fixture(autouse=True)
def reset_model_loaded():
    # Make sure we start with False before each test
    api.MODEL_LOADED = False
    yield
    api.MODEL_LOADED = False


def test_health_endpoint_no_model():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_predict_no_model_returns_503(monkeypatch):
    def mock_load(path):
        raise Exception("Model not found")

    monkeypatch.setattr(api.joblib, "load", mock_load)

    with TestClient(api.app) as client:
        response = client.post(
            "/predict",
            json={
                "feature_0": 0.1,
                "feature_1": 0.2,
                "feature_2": 0.3,
                "feature_3": 0.4,
                "feature_4": 0.5,
                "feature_5": 0.6,
                "feature_6": 0.7,
                "feature_7": 0.8,
                "feature_8": 0.9,
                "feature_9": 1.0,
            },
        )
        assert response.status_code == 503
        assert "Model not loaded" in response.json()["detail"]


def test_readiness_no_model_returns_503(monkeypatch):
    def mock_load(path):
        raise Exception("Model not found")

    monkeypatch.setattr(api.joblib, "load", mock_load)

    with TestClient(api.app) as client:
        response = client.get("/readiness")
        assert response.status_code == 503
