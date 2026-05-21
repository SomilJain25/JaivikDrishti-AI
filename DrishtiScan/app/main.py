"""
CropScan - JaivikDrishti AI Module
======================================
FastAPI Backend — REST API for crop disease detection
"""

import os
import sys
import logging
import time
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .predict import CropScanPredictor, TREATMENT_DATABASE


# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("CropScan.api")


# ─────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="CropScan API",
    description="AI-powered crop disease detection system",
    version="1.0.0",
)


# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# Predictor
# ─────────────────────────────────────────────────────────────
predictor: Optional[CropScanPredictor] = None


@app.on_event("startup")
async def startup_event():
    global predictor

    logger.info("Starting CropScan API...")

    try:
        predictor = CropScanPredictor()
        logger.info("Model loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        predictor = None


# ─────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────

class TopPrediction(BaseModel):
    disease: str
    confidence: float


class PredictionResponse(BaseModel):
    status: str

    disease: Optional[str] = None
    confidence: Optional[float] = None
    confidence_percent: Optional[str] = None

    treatment: Optional[list] = []
    organic_treatment: Optional[list] = []
    prevention: Optional[list] = []

    is_uncertain: Optional[bool] = None
    uncertainty_warning: Optional[str] = None

    top_predictions: List[TopPrediction] = []

    processing_time_ms: Optional[float] = None
    error: Optional[str] = None

    model_config = {
        "extra": "ignore"
    }


class HealthResponse(BaseModel):
    status: str
    service: str
    platform: str
    model_loaded: bool
    version: str
    endpoints: list


# ─────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))

    return response


# ─────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────
def validate_image_file(file: UploadFile):

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif"
    }

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}"
        )

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file extension: {ext}"
        )


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse)
async def root():

    return {
        "status": "healthy",
        "service": "CropScan",
        "platform": "JaivikDrishti AI",
        "model_loaded": predictor is not None,
        "version": "1.0.0",
        "endpoints": [
            "POST /predict",
            "POST /predict/gradcam",
            "GET /diseases",
            "GET /treatments/{disease_name}",
            "GET /docs"
        ]
    }


# ─────────────────────────────────────────────────────────────
# Predict Disease
# ─────────────────────────────────────────────────────────────
@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Prediction"]
)
async def predict_disease(
    file: UploadFile = File(...)
):
    start_time = time.time()

    validate_image_file(file)

    try:
        image_bytes = await file.read()

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {str(e)}"
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file received"
        )

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Predictor not initialized"
        )

    logger.info(
        f"Prediction request: "
        f"{file.filename} "
        f"({len(image_bytes)/1024:.1f}KB)"
    )

    result = predictor.predict(image_bytes)

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=500,
            detail="Predictor returned invalid response"
        )

    # Add processing time
    result["processing_time_ms"] = round(
        (time.time() - start_time) * 1000,
        2
    )

    # Ensure fields exist
    result.setdefault("status", "success")
    result.setdefault("error", None)
    result.setdefault("top_predictions", [])
    result.setdefault("treatment", [])
    result.setdefault("organic_treatment", [])
    result.setdefault("prevention", [])
    result.setdefault("is_uncertain", False)

    # FIX TOP PREDICTIONS FORMAT
    formatted_predictions = []

    for pred in result.get("top_predictions", []):

        if isinstance(pred, dict):
            formatted_predictions.append({
                "disease": str(pred.get("disease", "Unknown")),
                "confidence": float(
                    pred.get("confidence", 0.0)
                )
            })

        elif isinstance(pred, (list, tuple)) and len(pred) == 2:
            formatted_predictions.append({
                "disease": str(pred[0]),
                "confidence": float(pred[1])
            })

    result["top_predictions"] = formatted_predictions

    logger.info(
        f"Prediction: {result.get('disease')} | "
        f"Confidence: {result.get('confidence_percent')} | "
        f"Time: {result['processing_time_ms']}ms"
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=422,
            detail=result.get("error")
        )

    return result


# ─────────────────────────────────────────────────────────────
# GradCAM
# ─────────────────────────────────────────────────────────────
@app.post("/predict/gradcam")
async def predict_with_gradcam(
    file: UploadFile = File(...)
):
    start_time = time.time()

    validate_image_file(file)

    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file received"
        )

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Predictor not initialized"
        )

    logger.info(f"Grad-CAM request: {file.filename}")

    result = predictor.predict_with_gradcam(
        image_bytes
    )

    result["processing_time_ms"] = round(
        (time.time() - start_time) * 1000,
        2
    )

    return result


# ─────────────────────────────────────────────────────────────
# Diseases
# ─────────────────────────────────────────────────────────────
@app.get("/diseases")
async def list_diseases():

    if predictor is None:
        diseases = list(
            TREATMENT_DATABASE.keys()
        )
    else:
        diseases = list(
            predictor.class_labels.values()
        )

    grouped = {}

    for disease in diseases:

        crop = (
            disease.split("___")[0]
            if "___" in disease
            else "Other"
        )

        grouped.setdefault(crop, [])
        grouped[crop].append(disease)

    return {
        "total_classes": len(diseases),
        "diseases_by_crop": grouped,
        "all_diseases": sorted(diseases)
    }


# ─────────────────────────────────────────────────────────────
# Treatment
# ─────────────────────────────────────────────────────────────
@app.get("/treatments/{disease_name}")
async def get_treatment(
    disease_name: str
):

    treatment = TREATMENT_DATABASE.get(
        disease_name
    )

    if not treatment:
        raise HTTPException(
            status_code=404,
            detail="Disease not found"
        )

    return {
        "disease": disease_name,
        "treatment": treatment
    }


# ─────────────────────────────────────────────────────────────
# Global Exception Handler
# ─────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": str(exc)
        }
    )


# ─────────────────────────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )