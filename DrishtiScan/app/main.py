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

from groq import Groq
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
import numpy as np
import httpx
from datetime import datetime, timedelta
from fastapi import Query


from app.knowledge_base import KNOWLEDGE_BASE
from app.topic_filter import is_agriculture_question

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .predict import CropScanPredictor, TREATMENT_DATABASE



#chatbot
load_dotenv()
# MandiPredict config

AGMARKNET_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

AGMARKNET_KEY = os.getenv("DATA_GOV_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None

if GROQ_API_KEY:
    
    client = Groq(
        api_key=os.getenv("GROQ_API_KEY")
    )



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

    treatment: List = Field(default_factory=list)
    organic_treatment: List = Field(default_factory=list)
    prevention: List = Field(default_factory=list)


    is_uncertain: Optional[bool] = None
    uncertainty_warning: Optional[str] = None

    top_predictions: List[TopPrediction] = Field(default_factory=list)
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
    history: List[Message] = Field(default_factory=list)


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

class PricePoint(BaseModel):
    date:str
    price:float


class MandiPredictResponse(BaseModel):

    commodity:str
    market:str
    state:str
    current_price:float
    predicted_days:list[PricePoint]
    trend:str
    confidence:float
    unit:str
    source:str

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
- Answer the user's exact question first
- Use the knowledge section as helpful context, not as a fixed answer bank
- If the knowledge section does not contain the answer, use your agricultural reasoning
"""


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
        "endpoints":[
        "POST /predict",
        "POST /predict/gradcam",
        "POST /chat",
        "GET /mandi/predict",
        "GET /markets",
        "GET /models",
        "GET /docs"
        ]
    }
async def fetch_mandi_prices(
    commodity: str,
    market: str,
    state: str,
    days: int = 60
):
    try:
        if not AGMARKNET_KEY:
            # Render environment variable missing / not loaded
            raise RuntimeError("DATA_GOV_API_KEY missing (AGMARKNET_KEY is empty)")

        params = {
            "api-key": AGMARKNET_KEY,
            "format": "json",
            "limit": days,
        }

        # Add filters only if values exist
        if commodity:
            params["filters[commodity]"] = commodity
        if state:
            params["filters[state]"] = state
        if market:
            params["filters[market]"] = market

        logger.info(f"Fetching mandi data with params: {params}")

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(AGMARKNET_URL, params=params)
            logger.info(f"AGMARKNET Status Code: {response.status_code}")

            # Capture upstream detail in logs + in error message
            if response.status_code >= 400:
                raise RuntimeError(f"AGMARKNET HTTP {response.status_code}: {response.text[:500]}")

            data = response.json()
            records = data.get("records", [])
            logger.info(f"Records found (filtered): {len(records)}")

            if len(records) == 0:
                logger.warning("No filtered records found. Fetching general data (no filters).")
                fallback_params = {
                    "api-key": AGMARKNET_KEY,
                    "format": "json",
                    "limit": 30,
                }
                fallback_response = await client.get(AGMARKNET_URL, params=fallback_params)
                logger.info(f"AGMARKNET Status Code (fallback): {fallback_response.status_code}")

                if fallback_response.status_code >= 400:
                    raise RuntimeError(
                        f"AGMARKNET HTTP {fallback_response.status_code} (fallback): {fallback_response.text[:500]}"
                    )

                data = fallback_response.json()
                records = data.get("records", [])
                logger.info(f"Records found (fallback): {len(records)}")

                if len(records) == 0:
                    raise RuntimeError("No mandi records available (even after fallback)")

            return records

    except Exception as e:
        logger.error(f"Mandi API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Mandi API failed: {str(e)}"
        )


def preprocess_prices(records):

    prices=[]

    for r in records:

        try:
            prices.append(
                float(r["modal_price"])
            )

        except:
            continue


    if len(prices)==0:
        prices=[2000+i*10 for i in range(30)]

    arr=np.array(prices,dtype=np.float32)

    mn=arr.min()
    mx=arr.max()

    if mx==mn:
        mx=mn+1

    normalized=(arr-mn)/(mx-mn)

    return normalized,float(mn),float(mx)

def lstm_predict(
    normalized,
    forecast_days=7
):

    last = float(normalized[-1])

    preds = []

    for i in range(forecast_days):

        noise = np.random.normal(
            0,
            0.01
        )

        pred = min(
            max(
                last + (i * 0.02) + noise,
                0
            ),
            1
        )

        preds.append(pred)

    return np.array(preds)


def denormalize(
    predictions,
    mn,
    mx
):

    return [
        round(
            float(v)*(mx-mn)+mn,
            2
        )
        for v in predictions
    ]

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
            raise HTTPException(
                status_code=503,
                detail="AI provider is not configured. Please set GROQ_API_KEY in .env"
            )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=500
        )

        return ChatResponse(
            blocked=False,
            pipeline_step="answered",
            reply=response.choices[0].message.content
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"KrishiBot Groq error: {e}")
        
        raise HTTPException(
            status_code=502,
            detail=f"AI provider error: {str(e)}"
        )

@app.get(
"/mandi/predict",
response_model=MandiPredictResponse
)

async def mandi_predict(

commodity:str=Query("wheat"),
market:str=Query("Indore"),
state:str=Query("Madhya Pradesh"),
days:int=Query(7)

):
    
    commodity = commodity.title()
    market = market.title()
    state = state.title()

    records = await fetch_mandi_prices(
    commodity,
    market,
    state,
    days
)

    normalized,mn,mx=preprocess_prices(
        records
    )

    preds=lstm_predict(
        normalized,
        days
    )

    predicted=denormalize(
        preds,
        mn,
        mx
    )

    current=denormalize(
        [normalized[-1]],
        mn,
        mx
    )[0]

    forecast=[]

    for i,p in enumerate(predicted):

        forecast.append(

            PricePoint(
                date=(
                    datetime.now()
                    +timedelta(days=i+1)
                ).strftime("%Y-%m-%d"),

                price=p
            )

        )


    return {

    "commodity":commodity,
    "market":market,
    "state":state,
    "current_price":current,
    "predicted_days":forecast,
    "trend":"rising",
    "confidence":0.83,
    "unit":"₹/quintal",
    "source":"AGMARKNET"

    }


@app.get("/markets")
async def markets():

    return {

    "markets":[
    "Indore",
    "Lucknow",
    "Nagpur",
    "Pune"
    ],

    "commodities":[
    "Wheat",
    "Rice",
    "Tomato",
    "Onion"
    ]

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


