# =============================================================================
# DrishtiScan — app/metrics.py
# Prometheus metrics instrumentation
#
# Exposes /metrics endpoint for Prometheus to scrape every 15s.
#
# Metrics tracked:
#   drishtiscan_predictions_total        — counter: total predictions by disease/status
#   drishtiscan_prediction_confidence    — histogram: confidence score distribution
#   drishtiscan_inference_duration_ms    — histogram: how long inference takes
#   drishtiscan_image_size_bytes         — histogram: uploaded image file sizes
#   drishtiscan_healthy_ratio            — gauge: % of scans that are healthy plants
#   http_requests_total                  — auto: request count by endpoint/method/status
#   http_request_duration_seconds        — auto: request latency histogram
# =============================================================================

import logging

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)

logger = logging.getLogger("drishtiscan.metrics")

# ── Custom business metrics ────────────────────────────────────────────────────

predictions_total = Counter(
    name="drishtiscan_predictions_total",
    documentation="Total number of disease predictions made",
    labelnames=["disease", "status", "is_healthy"],
)

prediction_confidence = Histogram(
    name="drishtiscan_prediction_confidence",
    documentation="Distribution of prediction confidence scores",
    buckets=[0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0],
)

inference_duration_ms = Histogram(
    name="drishtiscan_inference_duration_ms",
    documentation="Model inference duration in milliseconds",
    buckets=[50, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000],
)

image_size_bytes = Histogram(
    name="drishtiscan_image_size_bytes",
    documentation="Size of uploaded leaf images in bytes",
    buckets=[10_000, 50_000, 100_000, 300_000, 500_000, 1_000_000, 5_000_000],
)

healthy_scans_ratio = Gauge(
    name="drishtiscan_healthy_ratio",
    documentation="Rolling ratio of healthy plant scans (last 1000)",
)

errors_total = Counter(
    name="drishtiscan_errors_total",
    documentation="Total prediction errors",
    labelnames=["error_type"],
)

http_requests_total = Counter(
    name="http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request duration in seconds",
    labelnames=["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)

# Running totals for healthy ratio calculation
_total_scans   = 0
_healthy_scans = 0


def record_prediction(
    disease: str,
    confidence: float,
    inference_ms: float,
    image_bytes: int,
    status: str = "success",
) -> None:
    """
    Record metrics for a completed prediction.
    Call this at the end of every /predict handler.

    Args:
        disease:       Disease class name (e.g. "Tomato___Early_blight")
        confidence:    Model confidence score 0–1
        inference_ms:  Time taken for inference in milliseconds
        image_bytes:   Size of uploaded image in bytes
        status:        "success" or "error"
    """
    global _total_scans, _healthy_scans

    is_healthy = "true" if "healthy" in disease.lower() else "false"

    # Increment counters
    predictions_total.labels(
        disease=disease,
        status=status,
        is_healthy=is_healthy,
    ).inc()

    # Record confidence distribution
    prediction_confidence.observe(confidence)

    # Record inference time
    inference_duration_ms.observe(inference_ms)

    # Record image size
    image_size_bytes.observe(image_bytes)

    # Update healthy ratio gauge
    _total_scans += 1
    if is_healthy == "true":
        _healthy_scans += 1
    if _total_scans > 0:
        healthy_scans_ratio.set(_healthy_scans / _total_scans)

    logger.debug(
        f"Metric recorded | disease={disease} | conf={confidence:.3f} | "
        f"time={inference_ms:.0f}ms | size={image_bytes}B"
    )


def record_error(error_type: str) -> None:
    """Record a prediction error."""
    errors_total.labels(error_type=error_type).inc()


# ── Attach Prometheus to FastAPI ───────────────────────────────────────────────

def setup_metrics(app: FastAPI) -> None:
    """
    Attach Prometheus instrumentation to the FastAPI app.

    Adds:
      - Automatic HTTP metrics (latency, count, status codes)
      - /metrics endpoint (scraped by Prometheus every 15s)

    Call in main.py:
        from app.metrics import setup_metrics
        setup_metrics(app)
    """
    @app.middleware("http")
    async def prometheus_http_metrics(request: Request, call_next):
        import time

        start = time.perf_counter()
        response = await call_next(request)

        path = request.scope.get("route").path if request.scope.get("route") else request.url.path
        if path != "/metrics":
            duration = time.perf_counter() - start
            http_requests_total.labels(
                method=request.method,
                path=path,
                status=str(response.status_code),
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                path=path,
            ).observe(duration)

        return response

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    logger.info("Prometheus metrics enabled at /metrics")
