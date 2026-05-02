from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MLOps Playbook Inference API", version="1.0")

# Load model and pipeline
MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
PIPELINE_PATH = os.getenv("PIPELINE_PATH", "models/feature_pipeline.pkl")

try:
    model = joblib.load(MODEL_PATH)
    feature_pipeline = joblib.load(PIPELINE_PATH)
    logger.info("Model and pipeline loaded successfully.")
except Exception as e:
    logger.warning(f"Could not load model/pipeline: {e}. Ensure training pipeline is run first.")

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
def predict(request: InferenceRequest):
    try:
        # Convert request to DataFrame
        data = pd.DataFrame([request.model_dump()])

        # Transform features
        data_transformed = feature_pipeline.transform(data)

        # Predict
        prediction = model.predict(data_transformed)[0]

        logger.info(f"Prediction made: {prediction}")
        return InferenceResponse(prediction=int(prediction))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
