/**
 * API Service Layer — JaivikDrishti AI
 * Connects to CropScan FastAPI backend at http://localhost:8000
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Helper ────────────────────────────────────────────────────────────────

const handleResponse = async (res) => {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || `HTTP ${res.status}`);
  }
  return res.json();
};

// ─── Disease Detection ─────────────────────────────────────────────────────

/**
 * Upload image for disease detection
 * Calls: POST /predict
 * @param {File} imageFile
 */
export const detectDisease = async (imageFile) => {
  const formData = new FormData();
  formData.append("file", imageFile);

  const res = await fetch(`${BASE_URL}/predict`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type — browser sets it with boundary for FormData
  });

  const data = await handleResponse(res);

  // ── Map backend response to frontend shape ────────────────────────────
  // Backend returns: { status, disease, confidence, confidence_percent,
  //                    treatment, is_uncertain, top_predictions, processing_time_ms }
  return {
    success: data.status === "success",
    disease: formatDiseaseName(data.disease),       // "Tomato___Early_blight" → "Tomato Early Blight"
    rawDisease: data.disease,                        // keep original for /treatments lookup
    confidence: data.confidence * 100,              // 0-1 → 0-100
    confidencePercent: data.confidence_percent,     // "94.3%"
    severity: getSeverity(data.confidence),         // derived
    isUncertain: data.is_uncertain,
    uncertaintyWarning: data.uncertainty_warning,
    treatment: parseTreatment(data.treatment),      // split into array if string
    topPredictions: data.top_predictions || [],
    processingTimeMs: data.processing_time_ms,
  };
};

/**
 * Upload image + get Grad-CAM heatmap
 * Calls: POST /predict/gradcam
 * @param {File} imageFile
 */
export const detectDiseaseWithGradcam = async (imageFile) => {
  const formData = new FormData();
  formData.append("file", imageFile);

  const res = await fetch(`${BASE_URL}/predict/gradcam`, {
    method: "POST",
    body: formData,
  });

  const data = await handleResponse(res);

  return {
    success: data.status === "success",
    disease: formatDiseaseName(data.disease),
    rawDisease: data.disease,
    confidence: data.confidence * 100,
    confidencePercent: data.confidence_percent,
    severity: getSeverity(data.confidence),
    isUncertain: data.is_uncertain,
    treatment: parseTreatment(data.treatment),
    topPredictions: data.top_predictions || [],
    gradcamImage: data.gradcam_image,               // base64 PNG heatmap
    processingTimeMs: data.processing_time_ms,
  };
};

// ─── Diseases List ─────────────────────────────────────────────────────────

/**
 * Get all detectable diseases grouped by crop
 * Calls: GET /diseases
 */
export const getDiseases = async () => {
  const res = await fetch(`${BASE_URL}/diseases`);
  return handleResponse(res);
  // Returns: { total_classes, diseases_by_crop, all_diseases }
};

// ─── Treatment Info ────────────────────────────────────────────────────────

/**
 * Get treatment for a specific disease
 * Calls: GET /treatments/{disease_name}
 * @param {string} diseaseName  e.g. "Tomato___Early_blight"
 */
export const getTreatment = async (diseaseName) => {
  const encoded = encodeURIComponent(diseaseName);
  const res = await fetch(`${BASE_URL}/treatments/${encoded}`);
  return handleResponse(res);
  // Returns: { disease, treatment, exact_match }
};

// ─── Health Check ──────────────────────────────────────────────────────────

/**
 * Check if backend is running
 * Calls: GET /
 */
export const checkHealth = async () => {
  try {
    const res = await fetch(`${BASE_URL}/`);
    const data = await handleResponse(res);
    return { online: true, modelLoaded: data.model_loaded, ...data };
  } catch {
    return { online: false, modelLoaded: false };
  }
};

// ─── Mock / Unchanged (no backend endpoints yet) ───────────────────────────

/**
 * Get crop price prediction (still mock — no backend endpoint)
 */
export const predictPrice = async (crop, state) => {
  await new Promise((r) => setTimeout(r, 1000));
  // Keep your existing mock here — replace when you add /price endpoint
  const basePrices = { wheat: 2200, rice: 2100, cotton: 6200, sugarcane: 320, potato: 1800, tomato: 2500, onion: 3200, soybean: 4500 };
  const stateMultiplier = { Punjab: 1.1, Haryana: 1.08, UP: 0.95, MP: 0.92, Maharashtra: 1.0, Gujarat: 1.05, Karnataka: 0.98, AP: 1.02, Telangana: 1.03, Bihar: 0.9 };
  const base = basePrices[crop] || 2000;
  const mult = stateMultiplier[state] || 1.0;
  return {
    success: true,
    currentPrice: Math.round(base * mult),
    predictedPrice: Math.round(base * mult * 1.08),
    trend: "up",
    trendPercent: 8.5,
    bestSellMonth: "December",
    marketDemand: "High",
    priceHistory: [
      { month: "Jan", price: Math.round(base * mult * 0.92) },
      { month: "Feb", price: Math.round(base * mult * 0.95) },
      { month: "Mar", price: Math.round(base * mult * 0.98) },
      { month: "Apr", price: Math.round(base * mult * 1.0) },
      { month: "May", price: Math.round(base * mult * 1.02) },
      { month: "Jun", price: Math.round(base * mult * 1.05) },
    ],
  };
};

/**
 * Predict crop yield (still mock — no backend endpoint)
 */
export const predictYield = async (soilType, temp, rainfall, crop) => {
  await new Promise((r) => setTimeout(r, 1000));
  const yieldFactors = { wheat: { base: 45, tempOpt: 22, rainOpt: 450 }, rice: { base: 60, tempOpt: 28, rainOpt: 1200 }, cotton: { base: 25, tempOpt: 30, rainOpt: 800 }, sugarcane: { base: 80, tempOpt: 32, rainOpt: 1500 }, maize: { base: 50, tempOpt: 26, rainOpt: 600 } };
  const soilFactor = { loamy: 1.2, clay: 1.0, sandy: 0.8, black: 1.15, red: 0.9, alluvial: 1.25 };
  const cropData = yieldFactors[crop] || yieldFactors.wheat;
  const sFactor = soilFactor[soilType] || 1.0;
  const tempDiff = Math.abs(temp - cropData.tempOpt) / cropData.tempOpt;
  const rainDiff = Math.abs(rainfall - cropData.rainOpt) / cropData.rainOpt;
  const yieldPerAcre = Math.round(cropData.base * sFactor * (1 - tempDiff * 0.3) * (1 - rainDiff * 0.3));
  return {
    success: true,
    estimatedYield: yieldPerAcre,
    unit: "quintals/acre",
    confidence: 87,
    recommendations: [
      temp < cropData.tempOpt ? "Consider mulching to retain soil warmth" : "Ensure adequate irrigation during peak heat",
      rainfall < cropData.rainOpt ? "Install drip irrigation system" : "Improve drainage to prevent waterlogging",
      "Apply balanced NPK fertilizer based on soil test",
    ],
  };
};

/**
 * Chatbot response (still mock — no backend endpoint)
 */
export const getChatResponse = async (message) => {
  await new Promise((r) => setTimeout(r, 800));
  const responses = { hi: "Namaste! Main KrishiBot hoon. Aapki kya madad kar sakta hoon?", hello: "Hello! I am KrishiBot. How can I help you with farming today?", fertilizer: "For most crops, a balanced NPK (10-26-26) fertilizer works well. Always do a soil test first!", water: "Drip irrigation saves 40% water. Water early morning or evening to reduce evaporation.", pest: "Use neem oil (5ml/L) as organic pest control. For severe infestations, consult your local KVK.", organic: "Vermicompost, green manuring, and bio-fertilizers are great for organic farming.", default: "That is a great question! For detailed advice, please contact your nearest Krishi Vigyan Kendra." };
  const lowerMsg = message.toLowerCase();
  let response = responses.default;
  for (const [key, value] of Object.entries(responses)) {
    if (lowerMsg.includes(key)) { response = value; break; }
  }
  return { success: true, message: response };
};

/**
 * Get weather data (mock)
 */
export const getWeather = async () => {
  await new Promise((r) => setTimeout(r, 500));
  return { temp: 32, condition: "Partly Cloudy", humidity: 65, windSpeed: 12, forecast: [{ day: "Today", temp: 32, icon: "cloud" }, { day: "Tomorrow", temp: 34, icon: "sun" }, { day: "Wed", temp: 31, icon: "rain" }] };
};

// ─── Utility Helpers ───────────────────────────────────────────────────────

/**
 * "Tomato___Early_blight" → "Tomato Early Blight"
 */
const formatDiseaseName = (raw) => {
  if (!raw) return "Unknown";
  return raw
    .replace(/___/g, " ")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

/**
 * Derive severity label from confidence score (0–1)
 */
const getSeverity = (confidence) => {
  if (confidence >= 0.85) return "High";
  if (confidence >= 0.65) return "Moderate";
  return "Low";
};

/**
 * Backend returns treatment as a single string — split into array for UI
 */
const parseTreatment = (treatment) => {
  if (!treatment) return [];
  if (Array.isArray(treatment)) return treatment;
  // Split on newlines or numbered list patterns
  return treatment
    .split(/\n|\d+\.\s/)
    .map((t) => t.trim())
    .filter(Boolean);
};