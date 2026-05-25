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
from app.auth import verify_api_key
from fastapi import Depends
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi import Limiter
from slowapi.extension import _rate_limit_exceeded_handler
from app.metrics import setup_metrics
from app.metrics import record_prediction
from app.metrics import record_error
from monitoring.prediction_logger import prediction_logger
from versioning.model_registry import registry
from dotenv import load_dotenv
import openai
from app.knowledge_base import KNOWLEDGE_BASE
from app.topic_filter import is_agriculture_question

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
setup_metrics(app)


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

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# ─────────────────────────────────────────────────────────────
# Predictor
# ─────────────────────────────────────────────────────────────
predictor: Optional[CropScanPredictor] = None


@app.on_event("startup")
async def startup_event():
    global predictor

    logger.info("Starting CropScan API...")

    try:
        registry.load_all()
        predictor = CropScanPredictor()
        _model, version, _labels = registry.get_model()
        logger.info(f"Model registry loaded active version: {version}")
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
    model_version: Optional[str] = None
    error: Optional[str] = None

    model_config = {
        "extra": "ignore"
    }

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    blocked: bool
    pipeline_step: str
    reply: str


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

def build_context(user_question: str):
    return KNOWLEDGE_BASE


def build_system_prompt(context: str):

    return f"""
You are KrishiBot, an agricultural AI assistant.

Knowledge:
{context}

Rules:
- Answer only agriculture questions
- Use simple farmer-friendly language
- Mention Indian crops/schemes if relevant
"""


def build_fallback_reply(message: str):
    lower = message.lower()

    if any(word in lower for word in ["potato", "potatoes"]):
        return (
            "Potato grows underground because the part we eat is a tuber, not a fruit. "
            "The plant sends swollen underground stems into the soil, where they store "
            "food made by the leaves. Keeping tubers underground also protects them "
            "from sunlight, which can turn them green and bitter."
        )

    if "black soil" in lower or "black cotton soil" in lower:
        return (
            "Black soil is good for cotton, soybean, sorghum, maize, pulses, and some "
            "oilseeds. It holds water well, so avoid waterlogging and add organic matter "
            "to improve soil structure."
        )

    if "aphid" in lower or "aphids" in lower:
        return (
            "For aphids, start with yellow sticky traps and neem oil spray at about 5 ml "
            "per litre of water. Check the underside of leaves, avoid excess nitrogen, "
            "and use a recommended insecticide only if infestation is heavy."
        )

    if "npk" in lower or "fertilizer" in lower or "fertiliser" in lower:
        return (
            "NPK needs depend on crop and soil test results. As a general rule, apply "
            "organic manure before sowing and split nitrogen doses instead of applying "
            "all at once. For accurate advice, use a Soil Health Card or local KVK test."
        )

    if "pm-kisan" in lower or "pm kisan" in lower:
        return (
            "PM-KISAN provides financial support to eligible farmer families through "
            "direct bank transfer. Farmers should check land record, Aadhaar, and bank "
            "details on the official PM-KISAN portal or at the local agriculture office."
        )

    if "drip" in lower or "sprinkler" in lower:
        return (
            "Drip irrigation is best for vegetables, orchards, and row crops because it "
            "saves water near the root zone. Sprinkler irrigation is useful for wheat, "
            "groundnut, fodder, and uneven land, but avoid it when leaf diseases are high."
        )

    return (
        "I can help with crops, soil, pests, irrigation, fertilizers, and Indian farming "
        "schemes. Please share the crop name, soil type, season, and the problem you are "
        "seeing so I can give more specific guidance."
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
            "GET /models",
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

@limiter.limit("30/minute")
async def predict_disease(
    request: Request,
    file: UploadFile = File(...),
    key: str = Depends(verify_api_key)
):
    start_time = time.time()

    validate_image_file(file)

    try:
        image_bytes = await file.read()

    except Exception as e:
        record_error(type(e).__name__)

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
            status_code=422,
            detail="Predictor not initialized"
    )
    logger.info(
        f"Prediction request: "
        f"{file.filename} "
        f"({len(image_bytes)/1024:.1f}KB)"
    )

    model, version, labels = registry.get_model()

    result = predictor.predict_with_model(
        model,
        image_bytes
    )

    result["model_version"] = version

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

    # Normalize treatment fields to lists for Pydantic validation
    for field in ["treatment", "organic_treatment", "prevention"]:
        value = result.get(field)
        if isinstance(value, str):
            result[field] = [value]
        elif value is None:
            result[field] = []

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
    
    registry.record_prediction(
        version,
        confidence=float(result.get("confidence", 0.0))
    )

    record_prediction(
        disease=result.get("disease", "Unknown"),
        confidence=float(
            result.get("confidence", 0.0)
        ),
        inference_ms=result["processing_time_ms"],
        image_bytes=len(image_bytes),
        status=result.get("status", "success")
    )
    return result


@app.get("/models")
async def model_stats():
    return registry.get_stats()

# ─────────────────────────────────────────────────────────────
# GradCAM
# ─────────────────────────────────────────────────────────────
@app.post("/predict/gradcam", response_model=PredictionResponse)
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

    # Normalize treatment fields to lists for Pydantic validation
    for field in ["treatment", "organic_treatment", "prevention"]:
        value = result.get(field)
        if isinstance(value, str):
            result[field] = [value]
        elif value is None:
            result[field] = []

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

@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["KrishiBot"]
)
async def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    if not is_agriculture_question(message):

        return ChatResponse(
            blocked=True,
            pipeline_step="topic_filter",
            reply="Please ask agriculture-related questions only."
        )

    context = build_context(message)

    system_prompt = build_system_prompt(
        context
    )

    messages = [
        {
            "role":"system",
            "content":system_prompt
        }
    ]

    for h in request.history:

        messages.append(
            {
                "role": h.role,
                "content": h.content
            }
        )

    messages.append(
        {
            "role":"user",
            "content":message
        }
    )

    try:

        if client is None:
            return ChatResponse(
                blocked=False,
                pipeline_step="local_fallback",
                reply=build_fallback_reply(message)
            )

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=500,
            messages=messages
        )

        return ChatResponse(
            blocked=False,
            pipeline_step="answered",
            reply=response.choices[0].message.content
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.warning(f"KrishiBot OpenAI fallback used: {e}")

        return ChatResponse(
            blocked=False,
            pipeline_step="local_fallback",
            reply=build_fallback_reply(message)
        )


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

#chatbot
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None

if OPENAI_API_KEY:
    client = openai.OpenAI(
        api_key=OPENAI_API_KEY
    )
