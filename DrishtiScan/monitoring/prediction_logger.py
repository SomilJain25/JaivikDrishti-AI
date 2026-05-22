# =============================================================================
# DrishtiScan — app/prediction_logger.py
# Structured prediction logging — writes JSON logs for every prediction
#
# Every prediction is logged to:
#   logs/predictions.jsonl   — newline-delimited JSON (easy to parse/query)
#   logs/api.log             — human-readable for tail -f debugging
#
# Log record schema:
# {
#   "timestamp":    "2026-05-19T14:30:00.123Z",
#   "request_id":  "uuid4",
#   "disease":     "Tomato___Early_blight",
#   "confidence":  0.9432,
#   "is_uncertain": false,
#   "inference_ms": 143,
#   "image_size_kb": 234.5,
#   "top_predictions": [...],
#   "client_ip":   "123.45.67.89",
#   "auth_method": "api_key",
#   "gradcam":     false,
#   "status":      "success"
# }
# =============================================================================

import os
import json
import uuid
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Optional

# ── Setup dual logging ─────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

# Human-readable logger (for terminal/monitoring)
api_logger = logging.getLogger("drishtiscan.api")

# Structured JSON logger (for analytics and audit)
_jsonl_handler = logging.handlers.RotatingFileHandler(
    filename="logs/predictions.jsonl",
    maxBytes=50 * 1024 * 1024,   # 50 MB per file
    backupCount=10,               # keep 10 rotated files = up to 500 MB history
    encoding="utf-8",
)
_jsonl_handler.setFormatter(logging.Formatter("%(message)s"))  # raw JSON only

_prediction_log = logging.getLogger("drishtiscan.predictions.jsonl")
_prediction_log.addHandler(_jsonl_handler)
_prediction_log.setLevel(logging.INFO)
_prediction_log.propagate = False   # don't duplicate to root logger


class PredictionLogger:
    """
    Logs every prediction to structured JSONL file.

    Usage:
        logger = PredictionLogger()

        # In your /predict endpoint:
        log_id = logger.log(
            disease       = result["disease"],
            confidence    = result["confidence"],
            inference_ms  = result["processing_time_ms"],
            image_size_kb = len(image_bytes) / 1024,
            top_predictions = result["top_predictions"],
            client_ip     = request.client.host,
            gradcam       = False,
        )
    """

    def log(
        self,
        disease:          str,
        confidence:       float,
        inference_ms:     float,
        image_size_kb:    float,
        top_predictions:  list,
        client_ip:        str = "unknown",
        auth_method:      str = "unknown",
        gradcam:          bool = False,
        status:           str = "success",
        error:            Optional[str] = None,
    ) -> str:
        """
        Write one prediction record to the JSONL log.

        Returns:
            request_id: UUID string (can be returned in API response for tracing)
        """
        request_id = str(uuid.uuid4())
        is_healthy = "healthy" in disease.lower() if disease else False

        record = {
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "request_id":      request_id,
            "disease":         disease,
            "confidence":      round(confidence, 4),
            "is_healthy":      is_healthy,
            "is_uncertain":    confidence < 0.4,
            "inference_ms":    round(inference_ms, 1),
            "image_size_kb":   round(image_size_kb, 1),
            "top_predictions": [
                {"disease": p["disease"], "confidence": round(p["confidence"], 4)}
                for p in (top_predictions or [])[:3]
            ],
            "client_ip":       client_ip,
            "auth_method":     auth_method,
            "gradcam":         gradcam,
            "status":          status,
        }

        if error:
            record["error"] = error

        # Write JSON line to file
        _prediction_log.info(json.dumps(record, ensure_ascii=False))

        # Also log human-readable summary
        api_logger.info(
            f"[{request_id[:8]}] {status.upper()} | "
            f"{disease} | conf={confidence:.3f} | "
            f"{inference_ms:.0f}ms | {image_size_kb:.0f}KB | "
            f"gradcam={gradcam}"
        )

        return request_id

    def log_error(
        self,
        error_type: str,
        error_msg:  str,
        client_ip:  str = "unknown",
        image_size_kb: float = 0,
    ) -> str:
        """Log a failed prediction attempt."""
        return self.log(
            disease        = "error",
            confidence     = 0.0,
            inference_ms   = 0,
            image_size_kb  = image_size_kb,
            top_predictions= [],
            client_ip      = client_ip,
            status         = "error",
            error          = f"{error_type}: {error_msg}",
        )


# ── Singleton instance ─────────────────────────────────────────────────────────
prediction_logger = PredictionLogger()