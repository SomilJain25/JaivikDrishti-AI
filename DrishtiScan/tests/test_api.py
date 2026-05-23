"""
CropScan - API Test Suite
==============================
Tests for the FastAPI backend using pytest + httpx.

Run:
    pytest tests/ -v
    pytest tests/ -v --tb=short
"""

import io
import os
import sys
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.predict import CropScanPredictor, TREATMENT_DATABASE

# ─── Test Client ──────────────────────────────────────────────────────────────
client = TestClient(app)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def create_test_image(width: int = 224, height: int = 224, mode: str = "RGB") -> bytes:
    """Create a synthetic test image as bytes."""
    # Create a green leaf-like image
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    img_array[:, :, 1] = 120  # Green channel dominant
    img_array[:, :, 0] = 30   # Some red
    img_array[:, :, 2] = 20   # Some blue

    # Add some variation to look more realistic
    noise = np.random.randint(0, 40, (height, width, 3), dtype=np.uint8)
    img_array = np.clip(img_array.astype(int) + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(img_array, mode=mode)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def create_invalid_file() -> bytes:
    """Create a non-image file for testing error handling."""
    return b"This is not an image file. Just plain text."


# ─── Health Endpoint Tests ─────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_root_returns_200(self):
        """Health check should always return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_structure(self):
        """Health response should have all required fields."""
        response = client.get("/")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "platform" in data
        assert "model_loaded" in data
        assert "version" in data
        assert "endpoints" in data

    def test_service_name(self):
        """Service name should be CropScan."""
        response = client.get("/")
        assert response.json()["service"] == "CropScan"

    def test_platform_name(self):
        """Platform name should be JaivikDrishti AI."""
        response = client.get("/")
        assert "JaivikDrishti" in response.json()["platform"]


# ─── Predict Endpoint Tests ────────────────────────────────────────────────────

class TestPredictEndpoint:
    def test_predict_with_valid_jpeg(self):
        """POST /predict with valid JPEG should return 200 or 422 (if no model)."""
        image_bytes = create_test_image()
        response = client.post(
            "/predict",
            files={"file": ("test_leaf.jpg", image_bytes, "image/jpeg")}
        )
        # Either success (model loaded) or 422 (no model) — not 500
        assert response.status_code in [200, 422]

    def test_predict_with_valid_png(self):
        """POST /predict with valid PNG should work."""
        img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        response = client.post(
            "/predict",
            files={"file": ("test_leaf.png", buf.read(), "image/png")}
        )
        assert response.status_code in [200, 422]

    def test_predict_no_file_returns_422(self):
        """POST /predict without file should return 422."""
        response = client.post("/predict")
        assert response.status_code == 422

    def test_predict_empty_file_returns_400(self):
        """POST /predict with empty file should return 400."""
        response = client.post(
            "/predict",
            files={"file": ("empty.jpg", b"", "image/jpeg")}
        )
        assert response.status_code == 400

    def test_predict_invalid_file_type_returns_415(self):
        """POST /predict with non-image file should return 415."""
        response = client.post(
            "/predict",
            files={"file": ("document.pdf", b"%PDF-fake", "application/pdf")}
        )
        assert response.status_code == 415

    def test_predict_response_has_required_fields(self):
        """Successful prediction response should have all required fields."""
        image_bytes = create_test_image()
        response = client.post(
            "/predict",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")}
        )
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "disease" in data
            assert "confidence" in data
            assert "treatment" in data
            assert "top_predictions" in data
            assert "processing_time_ms" in data

    def test_predict_confidence_range(self):
        """Confidence score should be between 0 and 1."""
        image_bytes = create_test_image()
        response = client.post(
            "/predict",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")}
        )
        if response.status_code == 200:
            confidence = response.json()["confidence"]
            assert 0.0 <= confidence <= 1.0

    def test_process_time_header(self):
        """Response should include X-Process-Time-Ms header."""
        image_bytes = create_test_image()
        response = client.post(
            "/predict",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")}
        )
        assert "x-process-time-ms" in response.headers


# ─── Diseases Endpoint Tests ───────────────────────────────────────────────────

class TestDiseasesEndpoint:
    def test_list_diseases_returns_200(self):
        """GET /diseases should return 200."""
        response = client.get("/diseases")
        assert response.status_code == 200

    def test_diseases_response_structure(self):
        """Diseases response should have required fields."""
        response = client.get("/diseases")
        data = response.json()
        assert "total_classes" in data
        assert "diseases_by_crop" in data
        assert "all_diseases" in data

    def test_diseases_grouped_by_crop(self):
        """Diseases should be grouped by crop type."""
        response = client.get("/diseases")
        data = response.json()
        crops = data["diseases_by_crop"]
        assert isinstance(crops, dict)
        assert len(crops) > 0

    def test_total_classes_is_positive(self):
        """Total classes should be a positive number."""
        response = client.get("/diseases")
        assert response.json()["total_classes"] > 0


# ─── Treatments Endpoint Tests ─────────────────────────────────────────────────

class TestTreatmentsEndpoint:
    def test_known_disease_returns_treatment(self):
        """GET /treatments/{disease} for a known disease should return treatment."""
        response = client.get("/treatments/Tomato___Early_blight")
        assert response.status_code == 200
        data = response.json()
        assert "treatment" in data
        assert len(data["treatment"]) > 0

    def test_unknown_disease_returns_404(self):
        """GET /treatments for an unknown disease should return 404."""
        response = client.get("/treatments/Unknown___Fake_Disease")
        assert response.status_code == 404

    def test_healthy_plant_treatment(self):
        """Healthy plant should return a positive treatment message."""
        response = client.get("/treatments/Tomato___healthy")
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data["treatment"].lower() or "✅" in data["treatment"]


# ─── Predictor Unit Tests ──────────────────────────────────────────────────────

class TestCropScanPredictor:
    @pytest.fixture
    def predictor(self):
        """Create a predictor instance (without model for unit tests)."""
        return CropScanPredictor()

    def test_predictor_initializes(self, predictor):
        """Predictor should initialize without errors."""
        assert predictor is not None

    def test_preprocess_image_from_bytes(self, predictor):
        """Image preprocessing from bytes should return correct shape."""
        image_bytes = create_test_image()
        result = predictor.preprocess_image(image_bytes)
        assert result.shape == (1, 224, 224, 3)

    def test_preprocess_image_from_pil(self, predictor):
        """Image preprocessing from PIL Image should work."""
        img = Image.fromarray(np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8))
        result = predictor.preprocess_image(img)
        assert result.shape == (1, 224, 224, 3)

    def test_preprocess_image_normalized(self, predictor):
        """Preprocessed image should be normalized to [0, 1]."""
        image_bytes = create_test_image()
        result = predictor.preprocess_image(image_bytes)
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_preprocess_rgba_image(self, predictor):
        """RGBA image should be converted to RGB."""
        img = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 4), dtype=np.uint8), mode="RGBA"
        )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        result = predictor.preprocess_image(buf.read())
        assert result.shape == (1, 224, 224, 3)

    def test_preprocess_invalid_bytes_raises(self, predictor):
        """Invalid bytes should raise ValueError."""
        with pytest.raises(ValueError):
            predictor.preprocess_image(b"not an image")

    def test_get_treatment_known_disease(self, predictor):
        """Known disease should return a non-empty treatment string."""
        treatment = predictor.get_treatment("Tomato___Early_blight")
        assert isinstance(treatment, str)
        assert len(treatment) > 10

    def test_get_treatment_unknown_disease(self, predictor):
        """Unknown disease should return default treatment."""
        treatment = predictor.get_treatment("Unknown___Disease")
        assert isinstance(treatment, str)
        assert len(treatment) > 0

    def test_predict_without_model(self, predictor):
        """Prediction without model should return error status."""
        image_bytes = create_test_image()
        result = predictor.predict(image_bytes)
        # Should return error gracefully (not crash)
        assert result["status"] in ["success", "error"]

    def test_treatment_database_coverage(self):
        """Treatment database should have entries for major crops."""
        major_diseases = [
            "Tomato___Early_blight",
            "Potato___Late_blight",
            "Apple___Apple_scab",
            "Corn_(maize)___Common_rust_",
        ]
        for disease in major_diseases:
            assert disease in TREATMENT_DATABASE, f"Missing treatment for: {disease}"


# ─── Run Tests ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
