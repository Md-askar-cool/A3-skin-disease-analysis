"""
healthy_screener.py
===================
Binary skin-condition screener for SafeSkin AI.

Uses EfficientNetB0 transfer learning to classify an image as:
  * healthy            – no visible skin condition
  * potentially_affected – possible skin condition detected

When no trained model file is present the module falls back to the
MockPredictor so the API remains functional during development.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports – guarded so the module loads even without GPU deps
# ---------------------------------------------------------------------------
try:
    import tensorflow as tf
    from tensorflow.keras.applications import EfficientNetB0
    from tensorflow.keras import layers, Model
    TF_AVAILABLE = True
except ImportError:  # pragma: no cover
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed – HealthyScreener will use mock mode.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:  # pragma: no cover
    CV2_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IMG_SIZE = (224, 224)
CLASS_NAMES = ["healthy", "potentially_affected"]


class HealthyScreener:
    """
    Binary classifier: distinguishes healthy skin from potentially-affected skin.

    Parameters
    ----------
    model_path : str, optional
        Path to a saved Keras model file (.h5 or SavedModel directory).
        If None or the file does not exist the screener operates in mock mode.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model: Optional[Any] = None
        self.mock_mode: bool = False
        self._model_path = model_path

        if model_path and Path(model_path).exists():
            self._load_model(model_path)
        else:
            logger.warning(
                "HealthyScreener: model file not found at '%s'. "
                "Running in mock mode.",
                model_path,
            )
            self.mock_mode = True

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Classify a skin image as healthy or potentially affected.

        Parameters
        ----------
        image_path : str
            Path to the input image.

        Returns
        -------
        dict
            {
              "result":       str,   # "healthy" | "potentially_affected" | "uncertain"
              "confidence":   float, # 0.0 – 1.0
              "confidence_level": str,  # "high" | "moderate" | "low"
              "probabilities": {
                  "healthy":              float,
                  "potentially_affected": float,
              },
              "mock": bool           # True when no real model is loaded
            }
        """
        if self.mock_mode or not TF_AVAILABLE:
            return self._mock_predict()

        try:
            img_array = self.preprocess_image(image_path)
            raw_probs = self.model.predict(img_array, verbose=0)[0]   # shape (2,)
            result_dict = self._apply_threshold(raw_probs)
            result_dict["mock"] = False
            return result_dict
        except Exception as exc:
            logger.error("HealthyScreener.predict error: %s", exc, exc_info=True)
            fallback = self._mock_predict()
            fallback["error"] = str(exc)
            return fallback

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Load and pre-process an image for EfficientNetB0 inference.

        Steps:
          1. Read image with OpenCV (BGR → RGB).
          2. Resize to 224 × 224.
          3. Normalise pixel values to [0, 1].
          4. Add batch dimension → shape (1, 224, 224, 3).

        Returns
        -------
        np.ndarray
            Float32 array of shape (1, 224, 224, 3).
        """
        if CV2_AVAILABLE:
            img = cv2.imread(str(image_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, IMG_SIZE)
        else:
            # Fallback: use PIL if OpenCV is unavailable
            from PIL import Image  # type: ignore
            img = np.array(Image.open(image_path).convert("RGB").resize(IMG_SIZE))

        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)          # (1, H, W, C)
        return img

    def _apply_threshold(self, probs: np.ndarray) -> Dict[str, Any]:
        """
        Convert raw softmax probabilities to a result dict with confidence level.

        Confidence tiers:
          ≥ 0.90 → high confidence
          0.70 – 0.90 → moderate confidence
          < 0.70 → uncertain (return "uncertain" result)

        Parameters
        ----------
        probs : np.ndarray
            Softmax probabilities of shape (num_classes,).

        Returns
        -------
        dict
        """
        max_prob = float(np.max(probs))
        class_idx = int(np.argmax(probs))
        result_label = CLASS_NAMES[class_idx]

        if max_prob >= 0.90:
            confidence_level = "high"
            result = result_label
        elif max_prob >= 0.70:
            confidence_level = "moderate"
            result = result_label
        else:
            confidence_level = "low"
            result = "uncertain"

        return {
            "result": result,
            "confidence": round(max_prob, 4),
            "confidence_level": confidence_level,
            "probabilities": {
                CLASS_NAMES[i]: round(float(probs[i]), 4)
                for i in range(len(CLASS_NAMES))
            },
        }

    # ------------------------------------------------------------------
    #  Model construction (used by training scripts)
    # ------------------------------------------------------------------

    def build_model(self, num_classes: int = 2) -> "tf.keras.Model":
        """
        Build the EfficientNetB0 transfer-learning scaffold.

        Architecture:
          EfficientNetB0 (frozen base, ImageNet weights)
          → GlobalAveragePooling2D
          → BatchNormalization
          → Dropout(0.3)
          → Dense(256, relu)
          → Dropout(0.2)
          → Dense(num_classes, softmax)

        The base model is initially frozen for warm-up training.
        Call ``model.layers[0].trainable = True`` to unfreeze for fine-tuning.

        Parameters
        ----------
        num_classes : int
            Number of output classes (default 2).

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
        base_model.trainable = False  # Freeze during warm-up

        inputs = tf.keras.Input(shape=(224, 224, 3), name="input_image")
        # EfficientNetB0 includes its own preprocessing; pass include_preprocessing
        x = base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D(name="gap")(x)
        x = layers.BatchNormalization(name="bn")(x)
        x = layers.Dropout(0.3, name="dropout_1")(x)
        x = layers.Dense(256, activation="relu", name="dense_256")(x)
        x = layers.Dropout(0.2, name="dropout_2")(x)
        outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

        model = Model(inputs, outputs, name="SafeSkin_HealthyScreener")
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("HealthyScreener model built: %d output classes.", num_classes)
        return model

    @staticmethod
    def create_training_model() -> "tf.keras.Model":
        """
        Factory method: build and return a ready-to-train HealthyScreener model.

        Used by the training script ``train_healthy_screener.py``.
        """
        screener = HealthyScreener.__new__(HealthyScreener)
        return screener.build_model(num_classes=len(CLASS_NAMES))

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------

    def _load_model(self, model_path: str) -> None:
        """Load a Keras model from *model_path*."""
        if not TF_AVAILABLE:
            logger.warning("TensorFlow unavailable – cannot load model.")
            self.mock_mode = True
            return
        try:
            self.model = tf.keras.models.load_model(model_path)
            logger.info("HealthyScreener: loaded model from %s", model_path)
        except Exception as exc:
            logger.error("Failed to load model from %s: %s", model_path, exc)
            self.mock_mode = True

    def _mock_predict(self) -> Dict[str, Any]:
        """Return a realistic-looking mock prediction for development use."""
        # Weighted: 60 % chance of healthy, 40 % potentially_affected
        probs = np.random.dirichlet([3.0, 2.0]).astype(np.float32)
        result_dict = self._apply_threshold(probs)
        result_dict["mock"] = True
        return result_dict
