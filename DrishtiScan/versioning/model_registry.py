# =============================================================================
# DrishtiScan — app/model_registry.py
# Model versioning + A/B traffic splitting
#
# Supports:
#   - Multiple model versions (v1, v2, v3...)
#   - Traffic splitting (e.g. 80% v1, 20% v2 during rollout)
#   - Per-version performance tracking
#   - Instant rollback by changing env var
#
# How to use:
#   registry = ModelRegistry()
#   registry.load_all()
#
#   # In /predict endpoint — registry picks model based on traffic split
#   model, version = registry.get_model()
#   result = predictor.predict_with_model(model, image)
#   result["model_version"] = version
#
# Env vars:
#  MODEL_V1_PATH=model/drishtiscan_model.tflite
#  MODEL_V2_PATH=model/drishtiscan_v2.tflite
#   MODEL_V1_TRAFFIC=80    (80% of requests go to v1)
#   MODEL_V2_TRAFFIC=20    (20% go to v2)
#   ACTIVE_MODEL=v1        (force all traffic to v1 — for rollback)
# =============================================================================

import os
import json
import random
import logging
import time
from dataclasses import dataclass, field
from typing import Optional
import tensorflow as tf

logger = logging.getLogger("drishtiscan.registry")


@dataclass
class ModelVersion:
    """Holds one loaded model version with its metadata."""
    version:       str
    path:          str
    model:         Optional[object] = None
    labels:        dict             = field(default_factory=dict)
    loaded_at:     float            = 0.0
    traffic_pct:   int              = 100          # % of traffic to route here
    predictions:   int              = 0            # total predictions served
    avg_confidence:float            = 0.0          # rolling average confidence
    errors:        int              = 0


class ModelRegistry:
    """
    Manages multiple model versions with traffic splitting.

    Usage:
        registry = ModelRegistry()
        registry.load_all()

        # Get a model (respects traffic split)
        model, version_name, labels = registry.get_model()

        # Force a specific version (A/B testing, rollback)
        model, _, labels = registry.get_model(force_version="v1")

        # Record prediction outcome for tracking
        registry.record_prediction("v2", confidence=0.94)
    """

    def __init__(self):
        self.versions: dict[str, ModelVersion] = {}
        self._active_override = os.getenv("ACTIVE_MODEL", None)  # e.g. "v1"

        # Load version configs from env
        self._configs = self._load_configs()

    def _load_configs(self) -> list[dict]:
        """Read model version configs from environment variables."""
        configs = []

        # v1 config
        v1_path = os.getenv(
            "MODEL_V1_PATH",
            "model/drishtiscan_model.tflite"
)
        v1_labels = os.getenv("MODEL_V1_LABELS", "model/class_labels.json")
        v1_traffic = int(os.getenv("MODEL_V1_TRAFFIC", "100"))
        if os.path.exists(v1_path):
            configs.append({
                "version":     "v1",
                "path":        v1_path,
                "labels_path": v1_labels,
                "traffic_pct": v1_traffic,
            })

        # v2 config (only if MODEL_V2_PATH is set)
        v2_path = os.getenv("MODEL_V2_PATH", "")
        if v2_path and os.path.exists(v2_path):
            v2_labels  = os.getenv("MODEL_V2_LABELS", "model/class_labels_v2.json")
            v2_traffic = int(os.getenv("MODEL_V2_TRAFFIC", "0"))
            configs.append({
                "version":     "v2",
                "path":        v2_path,
                "labels_path": v2_labels,
                "traffic_pct": v2_traffic,
            })

        if not configs:
            logger.warning("No model files found! Prediction will fail.")
        return configs

    def load_all(self) -> None:
        """Load all configured model versions into memory."""
        for cfg in self._configs:
            self._load_version(cfg)

        total_traffic = sum(v.traffic_pct for v in self.versions.values())
        logger.info(f"ModelRegistry: {len(self.versions)} version(s) loaded | "
                    f"Total traffic: {total_traffic}%")

    def _load_version(self, cfg: dict) -> None:
        """Load one model version."""
        version = cfg["version"]
        path    = cfg["path"]

        logger.info(f"Loading model {version} from {path}...")
        start = time.time()

        try:

            # Support both .tflite and .h5/.keras
            if path.endswith(".tflite"):
                model = tf.lite.Interpreter(
                    model_path=path
                )
                model.allocate_tensors()

            else:
                model = tf.keras.models.load_model(path)

            labels = {}
            labels_path = cfg.get("labels_path", "")

            if os.path.exists(labels_path):
                with open(labels_path, "r") as f:
                    data = json.load(f)

                labels = data.get(
                    "index_to_class",
                    {}
                )

            elapsed = round(
                (time.time() - start) * 1000,
                1
            )

            self.versions[version] = ModelVersion(
                version     = version,
                path        = path,
                model       = model,
                labels      = labels,
                loaded_at   = time.time(),
                traffic_pct = cfg["traffic_pct"],
            )
            logger.info(f"  ✅ {version} loaded in {elapsed}ms | "
                        f"traffic={cfg['traffic_pct']}% | "
                        f"classes={len(labels)}")

        except Exception as e:
            logger.error(f"  ❌ Failed to load {version}: {e}")

    def get_model(
        self,
        force_version: Optional[str] = None
    ) -> tuple:
        """
        Return (model, version_name, labels) respecting traffic split.

        Args:
            force_version: If set, ignore traffic split and use this version.
                           Used for: rollback, A/B override, testing.

        Returns:
            (tf.keras.Model, version_string, labels_dict)
        """
        if not self.versions:
            raise RuntimeError("No models loaded. Call registry.load_all() first.")

        # Priority: explicit force → env override → traffic split
        target = force_version or self._active_override

        if target and target in self.versions:
            v = self.versions[target]
            return v.model, v.version, v.labels

        # Traffic split: weighted random selection
        # e.g. v1=80%, v2=20% → build a 100-slot wheel
        versions = list(self.versions.values())
        total    = sum(v.traffic_pct for v in versions)

        if total == 0:
            # All traffic = 0 — use first version as fallback
            v = versions[0]
            return v.model, v.version, v.labels

        roll = random.randint(1, total)
        cumulative = 0
        for v in versions:
            cumulative += v.traffic_pct
            if roll <= cumulative:
                return v.model, v.version, v.labels

        # Fallback
        v = versions[-1]
        return v.model, v.version, v.labels

    def record_prediction(self, version: str, confidence: float) -> None:
        """Track prediction stats per version (for comparing v1 vs v2)."""
        if version not in self.versions:
            return
        v = self.versions[version]
        v.predictions += 1
        # Rolling average confidence
        v.avg_confidence = (
            (v.avg_confidence * (v.predictions - 1) + confidence) / v.predictions
        )

    def record_error(self, version: str) -> None:
        """Track errors per version."""
        if version in self.versions:
            self.versions[version].errors += 1

    def get_stats(self) -> dict:
        """Return performance stats for all versions (shown at /models endpoint)."""
        return {
            name: {
                "version":        v.version,
                "traffic_pct":    v.traffic_pct,
                "predictions":    v.predictions,
                "avg_confidence": round(v.avg_confidence, 4),
                "errors":         v.errors,
                "error_rate":     round(v.errors / max(v.predictions, 1), 4),
                "classes":        len(v.labels),
            }
            for name, v in self.versions.items()
        }

    def set_traffic(self, version: str, pct: int) -> None:
        """
        Dynamically update traffic split at runtime.
        Use this for gradual rollout: start v2 at 5%, then 20%, then 50%...

        Call via POST /admin/traffic endpoint (add to main.py).
        """
        if version not in self.versions:
            raise ValueError(f"Unknown version: {version}")
        if not 0 <= pct <= 100:
            raise ValueError("Traffic percentage must be 0–100")
        self.versions[version].traffic_pct = pct
        logger.info(f"Traffic updated: {version} → {pct}%")

    def rollback(self, to_version: str = "v1") -> None:
        """
        Emergency rollback: send all traffic to a known-good version.
        Sets all other versions to 0% traffic.
        """
        if to_version not in self.versions:
            raise ValueError(f"Cannot rollback to unknown version: {to_version}")

        for name, v in self.versions.items():
            v.traffic_pct = 100 if name == to_version else 0

        logger.warning(f"🔁 ROLLBACK: All traffic → {to_version}")


# ── Singleton ──────────────────────────────────────────────────────────────────
registry = ModelRegistry()