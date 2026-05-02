from fastapi.testclient import TestClient

import src.inference.api as api


def test_predict_batch_no_model(monkeypatch):
    def mock_load(path):
        raise Exception("Model not found")

    monkeypatch.setattr(api.joblib, "load", mock_load)

    with TestClient(api.app) as client:
        response = client.post(
            "/predict/batch",
            json={
                "requests": [
                    {
                        "feature_0": 0.0,
                        "feature_1": 0.0,
                        "feature_2": 0.0,
                        "feature_3": 0.0,
                        "feature_4": 0.0,
                        "feature_5": 0.0,
                        "feature_6": 0.0,
                        "feature_7": 0.0,
                        "feature_8": 0.0,
                        "feature_9": 0.0,
                    }
                ]
            },
        )
        assert response.status_code == 503


def test_predict_batch_success(monkeypatch):
    class MockModel:
        def predict(self, x):
            return [1] * len(x)

    class MockPipeline:
        def transform(self, x):
            return x

    def mock_load(path):
        raise Exception("Mocking model")

    monkeypatch.setattr(api.joblib, "load", mock_load)

    with TestClient(api.app) as client:
        api.app.state.model = MockModel()
        api.app.state.feature_pipeline = MockPipeline()
        api.MODEL_LOADED = True

        reqs = [
            {
                "feature_0": 0.0,
                "feature_1": 0.0,
                "feature_2": 0.0,
                "feature_3": 0.0,
                "feature_4": 0.0,
                "feature_5": 0.0,
                "feature_6": 0.0,
                "feature_7": 0.0,
                "feature_8": 0.0,
                "feature_9": 0.0,
            }
            for _ in range(5)
        ]

        response = client.post("/predict/batch", json={"requests": reqs})
        assert response.status_code == 200
        res = response.json()
        assert res["count"] == 5
        assert res["failed"] == 0
        assert len(res["predictions"]) == 5
        assert all(p in [0, 1] for p in res["predictions"])


def test_predict_batch_exceeds_max(monkeypatch):
    monkeypatch.setattr(api, "MODEL_LOADED", True)
    with TestClient(api.app) as client:
        # Create 1001 requests
        reqs = [
            {
                "feature_0": 0.0,
                "feature_1": 0.0,
                "feature_2": 0.0,
                "feature_3": 0.0,
                "feature_4": 0.0,
                "feature_5": 0.0,
                "feature_6": 0.0,
                "feature_7": 0.0,
                "feature_8": 0.0,
                "feature_9": 0.0,
            }
            for _ in range(1001)
        ]
        response = client.post("/predict/batch", json={"requests": reqs})
        assert response.status_code == 422
