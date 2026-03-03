"""
ML Inference Service for FRA Fault Classification.

Loads trained XGBoost model artifacts and provides predictions for
FRA measurements. Used by the analysis API endpoint.

Implements a lazy-loading singleton pattern: model is loaded once
on first prediction and reused for subsequent calls.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier

# Add project root to path for ml imports
import sys, os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ml.features.feature_extractor import FRAFeatureExtractor

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """Result of ML inference on a single FRA measurement."""
    fault_type: str
    probability_score: float
    all_probabilities: dict[str, float]
    health_score: float
    confidence_level: float
    feature_importance: dict[str, float]
    model_version: str
    model_type: str = "xgboost"


class FRAInferenceService:
    """
    Inference service for FRA fault classification.

    Lazy-loads model artifacts from disk on first prediction.
    Thread-safe for concurrent FastAPI requests (read-only after load).

    Usage:
        service = FRAInferenceService(model_dir="ml/saved_models", version="v1.0.0")
        if service.is_loaded or service.load():
            result = service.predict(frequency_hz, magnitude_db, phase_degrees)
    """

    def __init__(
        self,
        model_dir: str = "ml/saved_models",
        version: str = "v1.0.0",
        target_points: int = 800,
    ):
        self.model_dir = Path(model_dir)
        self.version = version
        self.target_points = target_points

        # Model artifacts (loaded lazily)
        self._model: Optional[XGBClassifier] = None
        self._scaler: Optional[StandardScaler] = None
        self._label_encoder: Optional[LabelEncoder] = None
        self._feature_names: Optional[list[str]] = None
        self._feature_extractor: Optional[FRAFeatureExtractor] = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Check if model artifacts are loaded and ready."""
        return self._is_loaded

    def load(self) -> bool:
        """
        Load model artifacts from disk.

        Returns:
            True if loaded successfully, False otherwise.
        """
        try:
            model_path = self.model_dir / f"xgboost_fra_{self.version}.joblib"
            scaler_path = self.model_dir / f"scaler_{self.version}.joblib"
            encoder_path = self.model_dir / f"label_encoder_{self.version}.joblib"
            names_path = self.model_dir / f"feature_names_{self.version}.json"

            # Check all files exist
            for path in [model_path, scaler_path, encoder_path, names_path]:
                if not path.exists():
                    logger.warning(f"Model artifact not found: {path}")
                    return False

            self._model = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)
            self._label_encoder = joblib.load(encoder_path)

            with open(names_path) as f:
                self._feature_names = json.load(f)

            self._feature_extractor = FRAFeatureExtractor(target_points=self.target_points)
            self._is_loaded = True

            logger.info(
                f"ML model loaded: xgboost_fra_{self.version} "
                f"({len(self._feature_names)} features, "
                f"{len(self._label_encoder.classes_)} classes)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self._is_loaded = False
            return False

    def predict(
        self,
        frequency_hz: list[float] | np.ndarray,
        magnitude_db: list[float] | np.ndarray,
        phase_degrees: Optional[list[float] | np.ndarray] = None,
        baseline_freq: Optional[list[float] | np.ndarray] = None,
        baseline_mag: Optional[list[float] | np.ndarray] = None,
    ) -> InferenceResult:
        """
        Run fault classification on a single FRA measurement.

        Args:
            frequency_hz: Frequency array (Hz).
            magnitude_db: Magnitude array (dB).
            phase_degrees: Phase array (degrees), optional.
            baseline_freq: Baseline frequency array for comparison.
            baseline_mag: Baseline magnitude array for comparison.

        Returns:
            InferenceResult with fault type, probabilities, and confidence.

        Raises:
            RuntimeError: If model is not loaded.
            ValueError: If input data is invalid.
        """
        # Ensure model is loaded
        if not self._is_loaded:
            if not self.load():
                raise RuntimeError(
                    "ML model not loaded. Train a model first by running: "
                    "python ml/train_and_evaluate.py"
                )

        # Convert inputs
        freq = np.asarray(frequency_hz, dtype=np.float64)
        mag = np.asarray(magnitude_db, dtype=np.float64)
        phase = np.asarray(phase_degrees, dtype=np.float64) if phase_degrees is not None else None

        bl_freq = np.asarray(baseline_freq, dtype=np.float64) if baseline_freq is not None else None
        bl_mag = np.asarray(baseline_mag, dtype=np.float64) if baseline_mag is not None else None

        # Validate
        if len(freq) < 10:
            raise ValueError(f"Too few data points: {len(freq)} (minimum: 10)")
        if len(freq) != len(mag):
            raise ValueError(f"Frequency/magnitude length mismatch: {len(freq)} vs {len(mag)}")

        # Extract features
        result = self._feature_extractor.extract(
            freq, mag, phase,
            baseline_freq=bl_freq,
            baseline_mag=bl_mag,
        )

        # Scale features
        X = result.feature_values.reshape(1, -1)
        X_scaled = self._scaler.transform(X)

        # Predict
        pred_class = self._model.predict(X_scaled)[0]
        pred_proba = self._model.predict_proba(X_scaled)[0]

        # Map to fault type names
        fault_type = self._label_encoder.inverse_transform([pred_class])[0]
        all_probs = {}
        for idx, cls_name in enumerate(self._label_encoder.classes_):
            all_probs[cls_name] = round(float(pred_proba[idx]), 4)

        # Health score: healthy probability * 100
        health_score = round(all_probs.get("healthy", 0.0) * 100, 1)

        # Confidence: difference between top-1 and top-2 probabilities
        sorted_probs = sorted(pred_proba, reverse=True)
        if len(sorted_probs) >= 2:
            confidence = round(float(sorted_probs[0] - sorted_probs[1]), 4)
        else:
            confidence = round(float(sorted_probs[0]), 4)

        # Clamp confidence to reasonable range [0.1, 0.99]
        confidence = max(0.1, min(0.99, confidence + 0.3))

        # Feature importance (global from model)
        feature_importance = {}
        if self._feature_names and hasattr(self._model, 'feature_importances_'):
            importances = self._model.feature_importances_
            # Return top-20 most important features
            importance_pairs = sorted(
                zip(self._feature_names, importances),
                key=lambda x: x[1],
                reverse=True,
            )[:20]
            feature_importance = {name: round(float(imp), 4) for name, imp in importance_pairs}

        return InferenceResult(
            fault_type=fault_type,
            probability_score=round(float(all_probs[fault_type]), 4),
            all_probabilities=all_probs,
            health_score=health_score,
            confidence_level=confidence,
            feature_importance=feature_importance,
            model_version=f"xgboost-{self.version}",
            model_type="xgboost",
        )


# ---------------------------------------------------------------------------
# Global singleton — reused across FastAPI requests
# ---------------------------------------------------------------------------

_inference_service: Optional[FRAInferenceService] = None


def get_inference_service(
    model_dir: str = "ml/saved_models",
    version: str = "v1.0.0",
) -> FRAInferenceService:
    """
    Get or create the global inference service singleton.

    Used as a FastAPI dependency.
    """
    global _inference_service
    if _inference_service is None:
        _inference_service = FRAInferenceService(model_dir=model_dir, version=version)
    return _inference_service
