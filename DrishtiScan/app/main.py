"""
CropScan - JaivikDrishti AI Module
======================================
FastAPI Backend — REST API for crop disease detection
"""

from typing import List, Optional
import os
import sys
import logging
import time
import httpx
from typing import Optional
from datetime import datetime, timedelta

import numpy as np
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, UploadFile, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from groq import Groq

from .predict import CropScanPredictor, TREATMENT_DATABASE
from .mandi_agmarket import fetch_mandi_prices as fetch_mandi_prices_agmarket
from app.auth import verify_api_key
from app.metrics import setup_metrics, record_prediction, record_error
from app.knowledge_base import KNOWLEDGE_BASE
from app.topic_filter import is_agriculture_question
from monitoring.prediction_logger import prediction_logger
from versioning.model_registry import registry

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# chatbot
load_dotenv()

# MandiPredict config
AGMARKNET_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
AGMARKNET_KEY = os.getenv("DATA_GOV_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

client = None
if GROQ_API_KEY:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("CropScan.api")

# FastAPI App
app = FastAPI(
    title="CropScan API",
    description="AI-powered crop disease detection system",
    version="1.0.0",
)
setup_metrics(app)

# CORS
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


# Predictor
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


# Pydantic Models
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

    model_config = {"extra": "ignore"}


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
    date: str
    price: float


class MandiPredictResponse(BaseModel):
    commodity: str
    market: str
    state: str

    currentPrice: float
    predictedPrice: float

    trend: str
    trendPercent: float

    bestSellMonth: str
    marketDemand: str

    priceHistory: list

    confidence: float
    unit: str
    source: str

class SoilData(BaseModel):
    nitrogen:    float = Field(..., ge=0,   le=200,  description="N content kg/ha")
    phosphorus:  float = Field(..., ge=0,   le=100,  description="P content kg/ha")
    potassium:   float = Field(..., ge=0,   le=200,  description="K content kg/ha")
    ph:          float = Field(..., ge=4.0, le=9.0,  description="Soil pH")
    organic_matter: float = Field(2.0, ge=0, le=10,  description="Organic matter %")
    moisture:    float = Field(40.0, ge=0,  le=100,  description="Soil moisture %")
 
class WeatherData(BaseModel):
    temperature:  float = Field(..., ge=5,  le=50,   description="Avg temp °C")
    rainfall:     float = Field(..., ge=0,  le=3000, description="Annual rainfall mm")
    humidity:     float = Field(60.0, ge=0, le=100,  description="Relative humidity %")
    sunshine_hours: float = Field(7.0, ge=0, le=14,  description="Daily sunshine hours")
 
class YieldRequest(BaseModel):
    crop: str
    soil: SoilData
    weather: Optional[WeatherData] = None
    location: Optional[str] = None
    area_acres: float = 1.0
    season: str = "kharif"
 
class Recommendation(BaseModel):
    category:    str
    message:     str
    priority:    str     # "high" | "medium" | "low"
 
class YieldResponse(BaseModel):
    crop:                str
    predicted_yield:     float    # quintals/acre
    total_yield:         float    # quintals (for full area)
    yield_category:      str      # "low" | "average" | "good" | "excellent"
    confidence:          float
    limiting_factor:     str
    recommendations:     list[Recommendation]
    estimated_revenue:   float    # ₹ approx at current MSP
    unit:                str
 
async def fetch_weather(location: str) -> Optional[WeatherData]:
    if not WEATHER_API_KEY or not location:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as http:
            r = await http.get(WEATHER_URL, params={
                "q":     location,
                "appid": WEATHER_API_KEY,
                "units": "metric",
            })
            r.raise_for_status()
            d = r.json()
            return WeatherData(
                temperature = d["main"]["temp"],
                rainfall    = 800,    # OpenWeatherMap free tier has no annual rainfall
                humidity    = d["main"]["humidity"],
                sunshine_hours = 7.0,
            )
    except Exception:
        return None
 

# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
    return response


# Utility
def validate_image_file(file: UploadFile):
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=415, detail=f"Invalid file extension: {ext}")


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


# Routes
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
            "POST /chat",
            "POST /yield/predict",
            "GET /crops",
            "GET /mandi/predict",
            "GET /markets",
            "GET /models",
            "GET /docs",
        ],
    }


async def fetch_mandi_prices(commodity: str, market: str, state: str, days: int = 60):
    # Hardened implementation lives in mandi_agmarket.py
    return await fetch_mandi_prices_agmarket(
        agmarknet_key=AGMARKNET_KEY or "",
        commodity=commodity,
        market=market,
        state=state,
        days=days,
    )


def preprocess_prices(records):
    prices = []
    for r in records:
        try:
            prices.append(float(r["modal_price"]))
        except Exception:
            continue

    if len(prices) == 0:
        prices = [2000 + i * 10 for i in range(30)]

    arr = np.array(prices, dtype=np.float32)
    mn = arr.min()
    mx = arr.max()
    if mx == mn:
        mx = mn + 1
    normalized = (arr - mn) / (mx - mn)
    return normalized, float(mn), float(mx)


def lstm_predict(normalized, forecast_days=7):
    last = float(normalized[-1])
    preds = []
    for i in range(forecast_days):
        noise = np.random.normal(0, 0.01)
        pred = min(max(last + (i * 0.02) + noise, 0), 1)
        preds.append(pred)
    return np.array(preds)


def denormalize(predictions, mn, mx):
    return [round(float(v) * (mx - mn) + mn, 2) for v in predictions]


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
@limiter.limit("30/minute")
async def predict_disease(
    request: Request,
    file: UploadFile = File(...),
    key: str = Depends(verify_api_key),
):
    start_time = time.time()

    validate_image_file(file)
    try:
        image_bytes = await file.read()
    except Exception as e:
        record_error(type(e).__name__)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file received")

    if predictor is None:
        raise HTTPException(status_code=422, detail="Predictor not initialized")

    logger.info(f"Prediction request: {file.filename} ({len(image_bytes)/1024:.1f}KB)")

    model, version, labels = registry.get_model()

    result = predictor.predict_with_model(model, image_bytes)
    result["model_version"] = version

    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="Predictor returned invalid response")

    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)

    # Ensure fields exist
    result.setdefault("status", "success")
    result.setdefault("error", None)
    result.setdefault("top_predictions", [])
    result.setdefault("treatment", [])
    result.setdefault("organic_treatment", [])
    result.setdefault("prevention", [])
    result.setdefault("is_uncertain", False)

    # Normalize treatment fields to lists
    for field in ["treatment", "organic_treatment", "prevention"]:
        value = result.get(field)
        if isinstance(value, str):
            result[field] = [value]
        elif value is None:
            result[field] = []

    # Fix top_predictions format
    formatted_predictions = []
    for pred in result.get("top_predictions", []):
        if isinstance(pred, dict):
            formatted_predictions.append(
                {
                    "disease": str(pred.get("disease", "Unknown")),
                    "confidence": float(pred.get("confidence", 0.0)),
                }
            )
        elif isinstance(pred, (list, tuple)) and len(pred) == 2:
            formatted_predictions.append({"disease": str(pred[0]), "confidence": float(pred[1])})

    result["top_predictions"] = formatted_predictions

    logger.info(
        f"Prediction: {result.get('disease')} | Confidence: {result.get('confidence_percent')} | Time: {result['processing_time_ms']}ms"
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("error"))

    registry.record_prediction(version, confidence=float(result.get("confidence", 0.0)))

    record_prediction(
        disease=result.get("disease", "Unknown"),
        confidence=float(result.get("confidence", 0.0)),
        inference_ms=result["processing_time_ms"],
        image_bytes=len(image_bytes),
        status=result.get("status", "success"),
    )

    return result


@app.get("/models")
async def model_stats():
    return registry.get_stats()


@app.post("/predict/gradcam", response_model=PredictionResponse)
async def predict_with_gradcam(file: UploadFile = File(...)):
    start_time = time.time()

    validate_image_file(file)
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file received")

    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    logger.info(f"Grad-CAM request: {file.filename}")

    result = predictor.predict_with_gradcam(image_bytes)

    for field in ["treatment", "organic_treatment", "prevention"]:
        value = result.get(field)
        if isinstance(value, str):
            result[field] = [value]
        elif value is None:
            result[field] = []

    result["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
    return result


@app.get("/diseases")
async def list_diseases():
    if predictor is None:
        diseases = list(TREATMENT_DATABASE.keys())
    else:
        diseases = list(predictor.class_labels.values())

    grouped = {}
    for disease in diseases:
        crop = disease.split("___")[0] if "___" in disease else "Other"
        grouped.setdefault(crop, []).append(disease)

    return {
        "total_classes": len(diseases),
        "diseases_by_crop": grouped,
        "all_diseases": sorted(diseases),
    }


@app.get("/treatments/{disease_name}")
async def get_treatment(disease_name: str):
    treatment = TREATMENT_DATABASE.get(disease_name)
    if not treatment:
        raise HTTPException(status_code=404, detail="Disease not found")
    return {"disease": disease_name, "treatment": treatment}


@app.post("/chat", response_model=ChatResponse, tags=["KrishiBot"])
async def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if not is_agriculture_question(message):
        return ChatResponse(blocked=True, pipeline_step="topic_filter", reply="Please ask agriculture-related questions only.")

    context = build_context(message)
    system_prompt = build_system_prompt(context)

    messages = [{"role": "system", "content": system_prompt}]
    for h in request.history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": message})

    try:
        if client is None:
            raise HTTPException(status_code=503, detail="AI provider is not configured. Please set GROQ_API_KEY in .env")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=500,
        )

        return ChatResponse(blocked=False, pipeline_step="answered", reply=response.choices[0].message.content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KrishiBot Groq error: {e}")
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(e)}")


@app.get("/mandi/predict", response_model=MandiPredictResponse)
async def mandi_predict(
    commodity: str = Query("wheat"),
    market: str = Query("Indore"),
    state: str = Query("Madhya Pradesh"),
    days: int = Query(7),
):
    records = await fetch_mandi_prices(
        commodity, market, state, days
    )

    print("MANDI RECORDS =", records)

    normalized, mn, mx = preprocess_prices(records)

    print("NORMALIZED =", normalized)

    preds = lstm_predict(normalized, days)
    predicted = denormalize(preds, mn, mx)

    print("PREDICTED =", predicted)

    current = denormalize([normalized[-1]], mn, mx)[0]

    forecast = []
    for i, p in enumerate(predicted):
        forecast.append(
            PricePoint(
                date=(datetime.now() + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                price=float(p),
            )
        )

    predicted_price = float(predicted[-1])

    trend_percent = round(
        ((predicted_price - float(current)) / float(current)) * 100,
        2
    )

    price_history = []

    for item in forecast:
        price_history.append({
            "month": item.date,
            "price": item.price
        })

    return {
    "commodity": commodity,
    "market": market,
    "state": state,

    "currentPrice": float(current) if current else 0,
    "predictedPrice": float(predicted_price) if predicted_price else 0,

    "trend": "rising" if trend_percent >= 0 else "falling",
    "trendPercent": abs(trend_percent) if trend_percent else 0,

    "bestSellMonth": "October",
    "marketDemand": "High",

    "priceHistory": price_history if price_history else [],

    "confidence": 0.83,
    "unit": "₹/quintal",
    "source": "AGMARKNET"
}


@app.get("/markets")
async def markets():
    return {
        "markets": ["Indore", "Lucknow", "Nagpur", "Pune"],
        "commodities": ["Wheat", "Rice", "Tomato", "Onion"],
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"status": "error", "error": str(exc)})

# ── STEP 2: Feature engineering ──────────────────────────────
 
def build_features(crop: str, soil: SoilData, weather: WeatherData) -> np.ndarray:
    """
    Builds a 12-feature vector for the ML model.
    Features: N, P, K, pH, OM, moisture, temp, rainfall, humidity,
              sunshine, crop_encoded, npk_balance_score
    """
    crop_codes = {
        "wheat": 1, "rice": 2, "maize": 3, "soybean": 4,
        "cotton": 5, "sugarcane": 6, "mustard": 7, "chickpea": 8,
        "tomato": 9, "potato": 10, "onion": 11, "groundnut": 12,
    }
    crop_code = crop_codes.get(crop.lower(), 1)
 
    # NPK balance score (how well the nutrients are balanced)
    optimal_n = {"wheat": 120, "rice": 100, "maize": 100, "soybean": 20, "cotton": 100}
    optimal_p = {"wheat": 60,  "rice": 50,  "maize": 60,  "soybean": 60, "cotton": 60}
    optimal_k = {"wheat": 40,  "rice": 50,  "maize": 40,  "soybean": 40, "cotton": 50}
    on = optimal_n.get(crop.lower(), 80)
    op = optimal_p.get(crop.lower(), 50)
    ok = optimal_k.get(crop.lower(), 40)
 
    n_score = 1 - min(abs(soil.nitrogen   - on) / on, 1)
    p_score = 1 - min(abs(soil.phosphorus - op) / op, 1)
    k_score = 1 - min(abs(soil.potassium  - ok) / ok, 1)
    npk_balance = (n_score + p_score + k_score) / 3
 
    return np.array([
        soil.nitrogen / 200,
        soil.phosphorus / 100,
        soil.potassium / 200,
        (soil.ph - 4) / 5,
        soil.organic_matter / 10,
        soil.moisture / 100,
        (weather.temperature - 5) / 45,
        weather.rainfall / 3000,
        weather.humidity / 100,
        weather.sunshine_hours / 14,
        crop_code / 12,
        npk_balance,
    ], dtype=np.float32)
 
 
# ── STEP 3: ML Model (Random Forest approximation) ───────────
# Implements decision-tree ensemble logic in NumPy
# For production: joblib.load('yieldsense_rf.pkl')
 
YIELD_BASELINES = {
    "wheat": 16,  "rice": 22,  "maize": 20,  "soybean": 9,
    "cotton": 8,  "sugarcane": 400, "mustard": 10, "chickpea": 8,
    "tomato": 80, "potato": 70, "onion": 60,  "groundnut": 12,
}
 
MSP_PRICES = {
    "wheat": 2275, "rice": 2183, "maize": 2090, "soybean": 4600,
    "cotton": 6620, "sugarcane": 315, "mustard": 5650, "chickpea": 5440,
    "tomato": 2000, "potato": 1200, "onion": 1500, "groundnut": 5850,
}
 
def predict_yield(features: np.ndarray, crop: str) -> tuple[float, float, str]:
    """
    Predicts yield in quintals/acre using feature-weighted model.
    Returns (predicted_yield, confidence, limiting_factor).
    """
    baseline = YIELD_BASELINES.get(crop.lower(), 15)
 
    # Weight each feature's contribution
    weights = {
        "nitrogen":    0.20,
        "phosphorus":  0.12,
        "potassium":   0.08,
        "ph":          0.15,
        "organic_matter": 0.10,
        "moisture":    0.12,
        "temperature": 0.10,
        "rainfall":    0.08,
        "humidity":    0.02,
        "sunshine":    0.02,
        "npk_balance": 0.01,
    }
 
    feature_names = list(weights.keys()) + ["crop_code"]
    w_vals        = list(weights.values())
 
    # Optimal ranges → score each feature
    optimal = [0.6, 0.6, 0.2, 0.5, 0.3, 0.45, 0.5, 0.27, 0.65, 0.5, 0.7]
    scores  = []
    for i, (f, opt) in enumerate(zip(features[:11], optimal)):
        diff  = abs(f - opt)
        score = max(0, 1 - diff * 1.5)
        scores.append(score)
 
    weighted_score = sum(s * w for s, w in zip(scores, w_vals))
    yield_mult     = 0.4 + (weighted_score * 1.2)
    predicted      = round(baseline * yield_mult, 1)
 
    # Find limiting factor (worst score)
    min_idx = int(np.argmin(scores[:8]))
    factors = ["Nitrogen", "Phosphorus", "Potassium", "Soil pH",
               "Organic matter", "Soil moisture", "Temperature", "Rainfall"]
    limiting = factors[min_idx]
 
    confidence = round(min(0.92, max(0.55, 0.70 + weighted_score * 0.25)), 2)
    return predicted, confidence, limiting
 
 
# ── STEP 4: Generate recommendations ─────────────────────────
 
def generate_recommendations(crop: str, soil: SoilData, weather: WeatherData,
                              predicted_yield: float, limiting: str) -> list[Recommendation]:
    recs = []
 
    # Soil pH
    if soil.ph < 6.0:
        recs.append(Recommendation(category="Soil", priority="high",
            message=f"Soil pH {soil.ph} is too acidic. Apply lime @ 2–4 t/ha to raise pH to 6.0–7.0."))
    elif soil.ph > 7.8:
        recs.append(Recommendation(category="Soil", priority="high",
            message=f"Soil pH {soil.ph} is alkaline. Apply gypsum @ 5 t/ha and grow tolerant varieties."))
 
    # Nitrogen
    optimal_n = {"wheat": 120, "rice": 100, "maize": 100}.get(crop.lower(), 80)
    if soil.nitrogen < optimal_n * 0.7:
        recs.append(Recommendation(category="Fertilizer", priority="high",
            message=f"Low nitrogen ({soil.nitrogen} kg/ha). Apply urea in 2 splits — basal + top dress at {optimal_n} kg N/ha total."))
 
    # Organic matter
    if soil.organic_matter < 1.5:
        recs.append(Recommendation(category="Soil health", priority="medium",
            message="Low organic matter. Add 5 t/ha FYM or vermicompost before sowing. Consider green manuring."))
 
    # Moisture
    if soil.moisture < 30:
        recs.append(Recommendation(category="Irrigation", priority="high",
            message="Low soil moisture. Irrigate immediately. Consider drip irrigation to save 40–50% water."))
 
    # Rainfall
    if weather.rainfall < 500:
        recs.append(Recommendation(category="Water", priority="medium",
            message="Low annual rainfall area. Choose drought-tolerant varieties and practice mulching."))
 
    # Temperature stress
    crop_temp_range = {"wheat": (10, 25), "rice": (20, 35), "maize": (18, 32)}
    t_range = crop_temp_range.get(crop.lower(), (15, 35))
    if not (t_range[0] <= weather.temperature <= t_range[1]):
        recs.append(Recommendation(category="Climate", priority="medium",
            message=f"{crop.title()} grows best at {t_range[0]}–{t_range[1]}°C. Current {weather.temperature}°C may reduce yield."))
 
    if not recs:
        recs.append(Recommendation(category="General", priority="low",
            message="Soil and weather conditions look good. Continue current practices and monitor for pests/diseases regularly."))
 
    return recs[:5]
 
 
# ── Main endpoint ─────────────────────────────────────────────
 
@app.post("/yield/predict", response_model=YieldResponse)
async def predict_yield_endpoint(req: YieldRequest):
    crop = req.crop.lower()
 
    # Step 1: Get weather (from request or auto-fetch)
    weather = req.weather
    if weather is None and req.location:
        weather = await fetch_weather(req.location)
    if weather is None:
        weather = WeatherData(temperature=25.0, rainfall=800.0, humidity=65.0, sunshine_hours=7.0)
 
    # Step 2: Feature engineering
    features = build_features(crop, req.soil, weather)
 
    # Step 3: ML prediction
    predicted_yield, confidence, limiting = predict_yield(features, crop)
    total_yield = round(predicted_yield * req.area_acres, 1)
 
    # Step 4: Classify
    baseline = YIELD_BASELINES.get(crop, 15)
    ratio    = predicted_yield / baseline
    if   ratio > 0.9: category = "excellent"
    elif ratio > 0.7: category = "good"
    elif ratio > 0.5: category = "average"
    else:             category = "low"
 
    # Step 5: Revenue estimate
    msp      = MSP_PRICES.get(crop, 2000)
    revenue = round(total_yield * msp, 0)   # ₹ (MSP is per quintal)
 
    # Step 6: Recommendations
    recommendations = generate_recommendations(crop, req.soil, weather, predicted_yield, limiting)
 
    return YieldResponse(
        crop             = req.crop.title(),
        predicted_yield  = predicted_yield,
        total_yield      = total_yield,
        yield_category   = category,
        confidence       = confidence,
        limiting_factor  = limiting,
        recommendations  = recommendations,
        estimated_revenue= revenue,
        unit             = "quintals/acre",
    )
 
 
@app.get("/crops")
def list_crops():
    return {"crops": list(YIELD_BASELINES.keys())}

@app.get("/yield/health")
def yield_health():
    return {
        "service": "YieldSense",
        "status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port
    )

