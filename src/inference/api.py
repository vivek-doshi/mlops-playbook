import logging
import os
from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
PIPELINE_PATH = os.getenv("PIPELINE_PATH", "models/feature_pipeline.pkl")

# MLflow config (used if model registry loading is enabled)
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns.db")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "churn_prediction")

MODEL_LOADED: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL_LOADED
    try:
        app.state.model = joblib.load(MODEL_PATH)
        app.state.feature_pipeline = joblib.load(PIPELINE_PATH)
        MODEL_LOADED = True
        logger.info("Model and pipeline loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load model/pipeline: {e}. Ensure training pipeline is run first.")
    yield


app = FastAPI(title="MLOps Playbook Inference API", version="1.0", lifespan=lifespan)


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


@app.post("/predict", response_model=InferenceResponse)
def predict(request: InferenceRequest, api_req: Request):
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded. Run the training pipeline first.")

    try:
        # Convert request to DataFrame
        data = pd.DataFrame([request.model_dump()])

        # Transform features
        data_transformed = api_req.app.state.feature_pipeline.transform(data)

        # Predict
        prediction = api_req.app.state.model.predict(data_transformed)[0]

        logger.info(f"Prediction made: {prediction}")
        return InferenceResponse(prediction=int(prediction))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": MODEL_LOADED}


@app.get("/readiness")
def readiness_check():
    if MODEL_LOADED:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Not ready. Model not loaded.")
