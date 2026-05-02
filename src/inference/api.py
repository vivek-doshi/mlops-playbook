import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PIPELINE_PATH = os.getenv("PIPELINE_PATH", "models/feature_pipeline.pkl")

# MLflow config (used if model registry loading is enabled)
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "churn_prediction")

MODEL_LOADED: bool = False

# Custom ML-specific metrics
PREDICTION_COUNTER = Counter(
    "mlops_predictions_total",
    "Total number of predictions made",
    ["prediction_class"],
)
PREDICTION_LATENCY = Histogram(
    "mlops_prediction_latency_seconds",
    "Prediction endpoint latency in seconds",
)
MODEL_LOAD_STATUS = Counter(
    "mlops_model_load_attempts_total",
    "Model load attempts",
    ["status"],  # "success" or "failure"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL_LOADED
    try:
        import mlflow

        from src.models.registry import get_production_model_uri

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        model_uri = get_production_model_uri(MLFLOW_EXPERIMENT_NAME + "_rf")

        if model_uri.startswith("runs:/") or model_uri.startswith("models:/"):
            app.state.model = mlflow.sklearn.load_model(model_uri)
        else:
            app.state.model = joblib.load(model_uri)

        app.state.feature_pipeline = joblib.load(PIPELINE_PATH)
        MODEL_LOADED = True
        MODEL_LOAD_STATUS.labels(status="success").inc()
        logger.info("Model and pipeline loaded successfully.")
    except Exception as e:
        MODEL_LOAD_STATUS.labels(status="failure").inc()
        logger.warning(f"Could not load model/pipeline: {e}. Ensure training pipeline is run first.")
    yield


app = FastAPI(title="MLOps Playbook Inference API", version="1.0", lifespan=lifespan)

# Auto-instrument FastAPI with standard HTTP metrics
Instrumentator().instrument(app).expose(app)


class InferenceRequest(BaseModel):
    feature_0: float
    feature_1: float
    feature_2: float
    feature_3: float
    feature_4: float
    feature_5: float
    feature_6: float
    feature_7: float
    feature_8: float
    feature_9: float


class InferenceResponse(BaseModel):
    prediction: int


class BatchInferenceRequest(BaseModel):
    """Batch prediction request — list of individual inference inputs."""

    requests: List[InferenceRequest]


class BatchInferenceResponse(BaseModel):
    predictions: List[int]
    count: int
    failed: int


@app.post("/predict", response_model=InferenceResponse)
def predict(request: InferenceRequest, api_req: Request):
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded. Run the training pipeline first.")

    start = time.time()
    try:
        # Convert request to DataFrame
        data = pd.DataFrame([request.model_dump()])

        # Transform features
        data_transformed = api_req.app.state.feature_pipeline.transform(data)

        # Predict
        prediction = api_req.app.state.model.predict(data_transformed)[0]

        PREDICTION_COUNTER.labels(prediction_class=str(int(prediction))).inc()
        PREDICTION_LATENCY.observe(time.time() - start)

        logger.info(f"Prediction made: {prediction}")
        return InferenceResponse(prediction=int(prediction))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchInferenceResponse)
def predict_batch(batch: BatchInferenceRequest):
    """
    Batch prediction endpoint.
    Accepts up to 1000 rows. Processes all rows and returns
    predictions with a count of successes and failures.
    """
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded. Run the training pipeline first.")

    MAX_BATCH_SIZE = 1000
    if len(batch.requests) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Batch size {len(batch.requests)} exceeds maximum of {MAX_BATCH_SIZE}.",
        )

    predictions = []
    failed = 0

    try:
        # Vectorised processing — convert all rows to DataFrame at once
        data = pd.DataFrame([r.model_dump() for r in batch.requests])
        data_transformed = app.state.feature_pipeline.transform(data)
        preds = app.state.model.predict(data_transformed)
        predictions = [int(p) for p in preds]

        # Update Prometheus counters per class
        for p in predictions:
            PREDICTION_COUNTER.labels(prediction_class=str(p)).inc()

        logger.info(f"Batch prediction completed: {len(predictions)} rows, {failed} failed")
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return BatchInferenceResponse(
        predictions=predictions,
        count=len(predictions),
        failed=failed,
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": MODEL_LOADED}


@app.get("/readiness")
def readiness_check():
    if MODEL_LOADED:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Not ready. Model not loaded.")
