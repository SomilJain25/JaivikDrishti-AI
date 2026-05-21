"""
CropScan - JaivikDrishti AI Module
======================================
FastAPI Backend — REST API for crop disease detection

Endpoints:
    GET  /            — Health check + API info
    POST /predict     — Upload leaf image, get disease prediction
    POST /predict/gradcam — Prediction with Grad-CAM heatmap
    GET  /diseases    — List all known diseases
    GET  /treatments/{disease_name} — Get treatment for a specific disease

Run:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Integration with JaivikDrishti AI platform:
    This API is designed to be consumed by:
    - KrishiBot (chatbot): POST /predict
    - Web dashboard: POST /predict/gradcam
    - Mobile app: POST /predict
"""

import os
import sys
import io
import logging
import time
from typing import Optional, List, Dict

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path so we can import predict.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .predict import CropScanPredictor, TREATMENT_DATABASE

# ─── Logging ──────────────────────────────────────────────────────────────────
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

# ─── FastAPI App Initialization ───────────────────────────────────────────────
app = FastAPI(
    title="CropScan API",
    description=(
        "🌿 AI-powered crop disease detection system — part of JaivikDrishti AI platform. "
        "Upload a plant leaf image to get disease prediction, confidence score, and treatment advice."
    ),
    version="1.0.0",
    contact={
        "name": "JaivikDrishti AI",
        "url": "https://JaivikDrishti.ai",
    },
    license_info={
        "name": "MIT",
    }
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
# Allow all origins for local development
# In production, replace "*" with your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Load Predictor (once at startup) ────────────────────────────────────────
predictor: Optional[CropScanPredictor] = None

@app.on_event("startup")
async def startup_event():
    """Load model when the API starts up."""
    global predictor
    logger.info("Starting CropScan API...")
    try:
        predictor = CropScanPredictor()
        logger.info("Model loaded and ready")
    except Exception as e:
        logger.warning(f"Model loading warning: {e}")
        logger.warning("API will start, but predictions require a trained model.")
        predictor = None

class TopPrediction(BaseModel):
    disease: str
    confidence: float

# ─── Request/Response Models ──────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    """Standard prediction response schema."""
    status: str                    # "success" or "error"
    disease: Optional[str] = None         # e.g., "Tomato___Early_blight"
    confidence: Optional[float] = None    # 0.0 to 1.0
    confidence_percent: Optional[str] = None  # e.g., "94.3%"
    treatment: Optional[str] = None       # Detailed treatment advice
    is_uncertain: Optional[bool] = None   # True if confidence < threshold
    uncertainty_warning: Optional[str] = None
    top_predictions: Optional[List[TopPrediction]] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None

    model_config = {
        'extra': 'ignore'
    }

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    platform: str
    model_loaded: bool
    version: str
    endpoints: list


# ─── Middleware: Request Timing ────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
    return response


# ─── Utility Functions ─────────────────────────────────────────────────────────

def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded file is a supported image format.
    
    Raises:
        HTTPException: If file type is not supported
    """
    ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed types: JPEG, PNG, WebP, GIF"
        )

    # Check file extension
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid file extension: {ext}. Allowed: {ALLOWED_EXTENSIONS}"
            )

    # Check file size (max 10MB)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    # Note: We check after reading in the endpoint


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """
    Health check endpoint.
    Returns API status and available endpoints.
    """
    return {
        "status": "healthy",
        "service": "CropScan",
        "platform": "JaivikDrishti AI",
        "model_loaded": predictor is not None and predictor.model is not None,
        "version": "1.0.0",
        "endpoints": [
            "POST /predict — Predict disease from leaf image",
            "POST /predict/gradcam — Predict with Grad-CAM visualization",
            "GET  /diseases — List all known disease classes",
            "GET  /treatments/{disease_name} — Get treatment for a disease",
            "GET  /docs — Swagger UI documentation"
        ]
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_disease(
    file: UploadFile = File(..., description="Plant leaf image (JPG, PNG, WebP)")
):
    """
    **Main prediction endpoint** — Upload a plant leaf image to detect disease.
    
    - **file**: Leaf image file (JPEG, PNG, WebP, max 10MB)
    
    Returns:
    - **disease**: Predicted disease class name
    - **confidence**: Prediction confidence (0–1)
    - **treatment**: Detailed treatment recommendation
    - **top_predictions**: Top 3 possible diseases
    
    ---
    **Used by**: KrishiBot chatbot, mobile app, web dashboard
    """
    start_time = time.time()

    # ── Validate file ────────────────────────────────────────────────────────
    validate_image_file(file)

    # ── Read file bytes ──────────────────────────────────────────────────────
    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Check file size
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file received.")

    # ── Run Prediction ───────────────────────────────────────────────────────
    logger.info(f"Prediction request: {file.filename} ({len(image_bytes)/1024:.1f}KB)")

    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    result = predictor.predict(image_bytes)
    if "error" not in result:
        result["error"] = None

    # ── Add processing time ──────────────────────────────────────────────────
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"Result: {result.get('disease')} | "
        f"Confidence: {result.get('confidence_percent')} | "
        f"Time: {result['processing_time_ms']}ms"
    )

    # ── Handle errors ────────────────────────────────────────────────────────
    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@app.post("/predict/gradcam", tags=["Prediction"])
async def predict_with_gradcam(
    file: UploadFile = File(..., description="Plant leaf image for Grad-CAM analysis")
):
    """
    **Enhanced prediction with Grad-CAM visualization.**
    
    Returns the same data as `/predict` PLUS a base64-encoded heatmap image
    showing which areas of the leaf the model focused on.
    
    Grad-CAM (Gradient-weighted Class Activation Mapping) highlights the
    most disease-relevant regions, making predictions transparent and trustworthy.
    
    - **gradcam_image**: Base64-encoded PNG heatmap overlay
    """
    start_time = time.time()
    validate_image_file(file)

    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file received.")

    logger.info(f"Grad-CAM request: {file.filename}")

    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    result = predictor.predict_with_gradcam(image_bytes)
    if "error" not in result:
        result["error"] = None
    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)

    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@app.get("/diseases", tags=["Information"])
async def list_diseases():
    """
    List all disease classes the model can detect.
    
    Returns disease names grouped by crop type.
    """
    if predictor is None or not predictor.class_labels:
        # Return from treatment database if model not loaded
        diseases = list(TREATMENT_DATABASE.keys())
    else:
        diseases = list(predictor.class_labels.values())

    # Group by crop
    grouped = {}
    for disease in diseases:
        crop = disease.split("___")[0] if "___" in disease else "Other"
        if crop not in grouped:
            grouped[crop] = []
        grouped[crop].append(disease)

    return {
        "total_classes": len(diseases),
        "diseases_by_crop": grouped,
        "all_diseases": sorted(diseases)
    }


@app.get("/treatments/{disease_name}", tags=["Information"])
async def get_treatment(disease_name: str):
    """
    Get treatment recommendation for a specific disease.
    
    - **disease_name**: Disease class name (e.g., `Tomato___Early_blight`)
    
    URL-encode any special characters in the disease name.
    """
    # Decode URL-encoded characters
    from urllib.parse import unquote
    disease_name = unquote(disease_name)

    treatment = TREATMENT_DATABASE.get(disease_name)

    if not treatment:
        # Try case-insensitive match
        for key, val in TREATMENT_DATABASE.items():
            if key.lower() == disease_name.lower():
                return {"disease": key, "treatment": val, "exact_match": False}

        raise HTTPException(
            status_code=404,
            detail=f"Disease '{disease_name}' not found in treatment database. "
                   f"Use GET /diseases to see all available disease names."
        )

    return {
        "disease": disease_name,
        "treatment": treatment,
        "exact_match": True
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler — returns clean JSON errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error. Please try again.",
            "detail": str(exc)
        }
    )


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )