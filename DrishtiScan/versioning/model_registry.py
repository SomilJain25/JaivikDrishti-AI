"""
Lightweight model registry for DrishtiScan.

The registry keeps the active model version and exposes a small interface used
by app.main without changing the existing prediction pipeline.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from app.predict import CLASS_LABELS_PATH, MODEL_PATH, CropScanPredictor

logger = logging.getLogger("drishtiscan.model_registry")


@dataclass
class ModelEntry:
    version: str
    model_path: str
    labels_path: str
    predictor: Optional[CropScanPredictor] = None
    loaded_at: Optional[str] = None
    predictions: int = 0
    confidence_total: float = 0.0
    errors: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def average_confidence(self) -> float:
        if self.predictions == 0:
            return 0.0
        return round(self.confidence_total / self.predictions, 4)


class ModelRegistry:
    def __init__(self) -> None:
        self.active_version = os.getenv("MODEL_VERSION", "v1")
        self.models: Dict[str, ModelEntry] = {
            self.active_version: ModelEntry(
                version=self.active_version,
                model_path=os.getenv("MODEL_PATH", MODEL_PATH),
                labels_path=os.getenv("CLASS_LABELS_PATH", CLASS_LABELS_PATH),
                metadata={"source": "default"},
            )
        }

    def load_all(self) -> None:
        for version in list(self.models):
            self.load(version)

    def load(self, version: str) -> None:
        entry = self.models[version]
        if entry.predictor is not None:
            return

        logger.info("Loading model version %s from %s", version, entry.model_path)
        entry.predictor = CropScanPredictor(
            model_path=entry.model_path,
            labels_path=entry.labels_path,
        )
        entry.loaded_at = datetime.now(timezone.utc).isoformat()

    def get_model(self) -> Tuple[CropScanPredictor, str, dict]:
        if self.active_version not in self.models:
            raise RuntimeError(f"Active model version not registered: {self.active_version}")

        entry = self.models[self.active_version]
        if entry.predictor is None:
            self.load(self.active_version)

        if entry.predictor is None:
            raise RuntimeError(f"Model version not loaded: {self.active_version}")

        return entry.predictor, entry.version, entry.predictor.class_labels

    def record_prediction(self, version: str, confidence: float = 0.0) -> None:
        entry = self.models.get(version)
        if entry is None:
            return
        entry.predictions += 1
        entry.confidence_total += confidence

    def record_error(self, version: Optional[str] = None) -> None:
        entry = self.models.get(version or self.active_version)
        if entry is not None:
            entry.errors += 1

    def get_stats(self) -> dict:
        return {
            "active_version": self.active_version,
            "models": {
                version: {
                    "version": entry.version,
                    "model_path": entry.model_path,
                    "labels_path": entry.labels_path,
                    "loaded": entry.predictor is not None,
                    "loaded_at": entry.loaded_at,
                    "predictions": entry.predictions,
                    "average_confidence": entry.average_confidence,
                    "errors": entry.errors,
                    "metadata": entry.metadata,
                }
                for version, entry in self.models.items()
            },
        }


registry = ModelRegistry()
