"""
condition_classifier.py
=======================
Multi-class skin-condition classifier for SafeSkin AI.

Classifies a skin image into one of 10 clinical condition categories using
EfficientNetB0 transfer learning. Severity is estimated for conditions that
have clinical staging (mild / moderate / severe).

All condition classes and display names are loaded from
``config/model_classes.json`` to keep the code data-driven.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports
# ---------------------------------------------------------------------------
try:
    import tensorflow as tf
    from tensorflow.keras.applications import EfficientNetB0
    from tensorflow.keras import layers, Model
    TF_AVAILABLE = True
except ImportError:  # pragma: no cover
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed – ConditionClassifier uses mock mode.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:  # pragma: no cover
    CV2_AVAILABLE = False

# ---------------------------------------------------------------------------
# Static data (kept here for direct import; also mirrored in model_classes.json)
# ---------------------------------------------------------------------------

#: All 10 skin-condition class IDs the model predicts.
CONDITION_CLASSES: List[str] = [
    "acne_vulgaris",
    "eczema_atopic_dermatitis",
    "psoriasis",
    "melanoma",
    "basal_cell_carcinoma",
    "seborrheic_keratosis",
    "tinea_ringworm",
    "urticaria_hives",
    "vitiligo",
    "rosacea",
]

#: Severity levels per condition.
#: Conditions without established staging return 'unable_to_assess'.
SEVERITY_MAP: Dict[str, List[str]] = {
    "acne_vulgaris":              ["mild", "moderate", "severe"],
    "eczema_atopic_dermatitis":   ["mild", "moderate", "severe"],
    "psoriasis":                  ["mild", "moderate", "severe"],
    "melanoma":                   ["unable_to_assess"],
    "basal_cell_carcinoma":       ["unable_to_assess"],
    "seborrheic_keratosis":       ["unable_to_assess"],
    "tinea_ringworm":             ["mild", "moderate", "severe"],
    "urticaria_hives":            ["mild", "moderate", "severe"],
    "vitiligo":                   ["unable_to_assess"],
    "rosacea":                    ["mild", "moderate", "severe"],
}

# Image size expected by EfficientNetB0
IMG_SIZE = (224, 224)


class ConditionClassifier:
    """
    Multi-class skin-condition classifier.

    Parameters
    ----------
    model_path : str, optional
        Path to a saved Keras model (.h5 or SavedModel directory).
        Falls back to mock mode when not provided or file is missing.
    config_dir : str, optional
        Directory containing ``model_classes.json``.
        Defaults to the ``config/`` sub-folder next to this file.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config_dir: Optional[str] = None,
    ) -> None:
        self.model: Optional[Any] = None
        self.mock_mode: bool = False
        self._model_path = model_path

        # Resolve config directory
        _here = Path(__file__).parent
        self._config_dir = Path(config_dir) if config_dir else _here / "config"

        # Load class list from JSON (dynamic, not hardcoded from module globals)
        self._classes: List[str] = self._load_classes()

        # Load model
        if model_path and Path(model_path).exists():
            self._load_model(model_path)
        else:
            logger.warning(
                "ConditionClassifier: model not found at '%s'. Mock mode active.",
                model_path,
            )
            self.mock_mode = True

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Classify the skin condition in *image_path*.

        Parameters
        ----------
        image_path : str

        Returns
        -------
        dict
            {
              "condition":        str,   # top predicted condition ID
              "display_name":     str,   # human-readable name
              "confidence":       float, # 0.0 – 1.0
              "confidence_level": str,   # "high" | "moderate" | "low"
              "severity_estimate":str,   # "mild" | "moderate" | "severe" | "unable_to_assess"
              "all_probabilities": {condition_id: float, ...},
              "mock": bool
            }
        """
        if self.mock_mode or not TF_AVAILABLE:
            return self._mock_predict()

        try:
            img_array = self._preprocess_image(image_path)
            raw_probs = self.model.predict(img_array, verbose=0)[0]  # (num_classes,)

            class_idx = int(np.argmax(raw_probs))
            confidence = float(raw_probs[class_idx])
            condition_id = self._classes[class_idx]

            confidence_level = self._confidence_level(confidence)
            severity = self._estimate_severity(condition_id, confidence)
            display_name = self._get_display_name(condition_id)

            all_probs = {
                self._classes[i]: round(float(raw_probs[i]), 4)
                for i in range(len(self._classes))
            }

            return {
                "condition": condition_id,
                "display_name": display_name,
                "confidence": round(confidence, 4),
                "confidence_level": confidence_level,
                "severity_estimate": severity,
                "all_probabilities": all_probs,
                "mock": False,
            }

        except Exception as exc:
            logger.error("ConditionClassifier.predict error: %s", exc, exc_info=True)
            fallback = self._mock_predict()
            fallback["error"] = str(exc)
            return fallback

    # ------------------------------------------------------------------
    #  Class loading
    # ------------------------------------------------------------------

    def _load_classes(self) -> List[str]:
        """
        Load condition class IDs from ``config/model_classes.json``.

        Falls back to the module-level CONDITION_CLASSES list if the file
        cannot be found or parsed.

        Returns
        -------
        list[str]
            Ordered list of class IDs matching model output indices.
        """
        config_file = self._config_dir / "model_classes.json"
        try:
            with open(config_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            classes = [entry["id"] for entry in data.get("classes", [])]
            if classes:
                logger.info("Loaded %d classes from %s", len(classes), config_file)
                return classes
            raise ValueError("Empty classes list in config JSON.")
        except Exception as exc:
            logger.warning(
                "Could not load classes from %s (%s). Using module defaults.",
                config_file, exc,
            )
            return list(CONDITION_CLASSES)

    # ------------------------------------------------------------------
    #  Severity estimation
    # ------------------------------------------------------------------

    def _estimate_severity(self, condition: str, confidence: float) -> str:
        """
        Estimate clinical severity based on condition type and prediction confidence.

        For conditions with severity levels (mild / moderate / severe) the
        method uses the confidence score as a proxy for disease burden:
          - confidence < 0.5  → mild
          - confidence < 0.75 → moderate
          - confidence ≥ 0.75 → severe

        For oncological or complex conditions (melanoma, BCC, etc.) severity
        cannot be reliably inferred from a photo alone; returns
        'unable_to_assess'.

        Parameters
        ----------
        condition : str
            Condition ID string from CONDITION_CLASSES.
        confidence : float
            Model confidence (0-1).

        Returns
        -------
        str
        """
        severity_options = SEVERITY_MAP.get(condition, ["unable_to_assess"])

        if severity_options == ["unable_to_assess"]:
            return "unable_to_assess"

        # Map confidence range → severity index
        if confidence < 0.50:
            idx = 0   # mild
        elif confidence < 0.75:
            idx = 1   # moderate
        else:
            idx = min(2, len(severity_options) - 1)  # severe

        return severity_options[idx]

    # ------------------------------------------------------------------
    #  Model construction
    # ------------------------------------------------------------------

    def build_model(self, num_classes: int) -> "tf.keras.Model":
        """
        Build an EfficientNetB0 model for multi-class skin-condition classification.

        Architecture:
          EfficientNetB0 (frozen base, ImageNet weights)
          → GlobalAveragePooling2D
          → BatchNormalization
          → Dropout(0.3)
          → Dense(512, relu)
          → Dropout(0.25)
          → Dense(num_classes, softmax)

        Parameters
        ----------
        num_classes : int
            Total number of condition classes.

        Returns
        -------
        tf.keras.Model
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required to build the model.")

        base_model = EfficientNetB0(
            include_top=False,
            weights="imagenet",
            input_shape=(224, 224, 3),
        )
        base_model.trainable = False  # Freeze for warm-up phase

        inputs = tf.keras.Input(shape=(224, 224, 3), name="input_image")
        x = base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D(name="gap")(x)
        x = layers.BatchNormalization(name="bn")(x)
        x = layers.Dropout(0.3, name="dropout_1")(x)
        x = layers.Dense(512, activation="relu", name="dense_512")(x)
        x = layers.Dropout(0.25, name="dropout_2")(x)
        outputs = layers.Dense(
            num_classes, activation="softmax", name="condition_predictions"
        )(x)

        model = Model(inputs, outputs, name="SafeSkin_ConditionClassifier")
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("ConditionClassifier model built with %d classes.", num_classes)
        return model

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """Load, resize, normalise, and batch an image for inference."""
        if CV2_AVAILABLE:
            img = cv2.imread(str(image_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, IMG_SIZE)
        else:
            from PIL import Image  # type: ignore
            img = np.array(Image.open(image_path).convert("RGB").resize(IMG_SIZE))

        img = img.astype(np.float32) / 255.0
        return np.expand_dims(img, axis=0)  # (1, 224, 224, 3)

    def _load_model(self, model_path: str) -> None:
        """Load a Keras model from disk."""
        if not TF_AVAILABLE:
            self.mock_mode = True
            return
        try:
            self.model = tf.keras.models.load_model(model_path)
            logger.info("ConditionClassifier: loaded model from %s", model_path)
        except Exception as exc:
            logger.error("Failed to load model from %s: %s", model_path, exc)
            self.mock_mode = True

    def _get_display_name(self, condition_id: str) -> str:
        """Return a human-readable display name for a condition ID."""
        config_file = self._config_dir / "model_classes.json"
        try:
            with open(config_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for entry in data.get("classes", []):
                if entry["id"] == condition_id:
                    return entry.get("display_name", condition_id)
        except Exception:
            pass
        # Fallback: capitalise and replace underscores
        return condition_id.replace("_", " ").title()

    @staticmethod
    def _confidence_level(confidence: float) -> str:
        """Map confidence float to a categorical level."""
        if confidence >= 0.90:
            return "high"
        if confidence >= 0.70:
            return "moderate"
        return "low"

    def _mock_predict(self) -> Dict[str, Any]:
        """Return a realistic mock classification result for development."""
        classes = self._classes
        probs = np.random.dirichlet(np.ones(len(classes))).astype(np.float32)
        class_idx = int(np.argmax(probs))
        condition_id = classes[class_idx]
        confidence = float(probs[class_idx])

        return {
            "condition": condition_id,
            "display_name": self._get_display_name(condition_id),
            "confidence": round(confidence, 4),
            "confidence_level": self._confidence_level(confidence),
            "severity_estimate": self._estimate_severity(condition_id, confidence),
            "all_probabilities": {
                classes[i]: round(float(probs[i]), 4) for i in range(len(classes))
            },
            "mock": True,
        }
