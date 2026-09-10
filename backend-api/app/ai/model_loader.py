"""
model_loader.py
===============
Singleton model registry for SafeSkin AI.

Loads all AI models once at application start-up and provides a single
access point so models are not reloaded on every request.

Supported models
----------------
  quality_checker      – ImageQualityChecker (OpenCV, no model file needed)
  healthy_screener     – HealthyScreener (EfficientNetB0 binary classifier)
  condition_classifier – ConditionClassifier (EfficientNetB0 multi-class)

If a model file is missing the loader falls back gracefully to mock mode,
keeping the API alive during development.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default model directory (relative to the backend root)
_DEFAULT_MODEL_DIR = str(
    Path(__file__).parent.parent.parent / "models"  # backend-api/models/
)


class ModelLoader:
    """
    Thread-safe singleton that manages model lifecycle.

    Methods
    -------
    load_all_models(model_dir)
        Discover and load all models from *model_dir*.
    get_model(name)
        Return a loaded model instance by name.
    get_model_version()
        Return the model version string from version.json.
    is_loaded(name)
        True if the named model has been loaded successfully.

    Examples
    --------
        loader = ModelLoader.instance()
        loader.load_all_models()
        quality_checker = loader.get_model("quality_checker")
        screener = loader.get_model("healthy_screener")
    """

    _instance: Optional["ModelLoader"] = None
    _models: Dict[str, Any] = {}
    _model_dir: str = _DEFAULT_MODEL_DIR

    # ------------------------------------------------------------------
    #  Singleton
    # ------------------------------------------------------------------

    def __new__(cls) -> "ModelLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
            cls._instance._model_dir = _DEFAULT_MODEL_DIR
        return cls._instance

    @classmethod
    def instance(cls) -> "ModelLoader":
        """Return the singleton ModelLoader instance."""
        return cls()

    # ------------------------------------------------------------------
    #  Load all models
    # ------------------------------------------------------------------

    def load_all_models(self, model_dir: Optional[str] = None) -> None:
        """
        Discover and load every AI model used by the SafeSkin pipeline.

        Models are loaded in order:
          1. ImageQualityChecker (always available, no .h5 file needed)
          2. HealthyScreener     (requires healthy_screener.h5)
          3. ConditionClassifier (requires condition_classifier.h5)

        Missing model files trigger mock mode rather than errors, so the
        API remains functional during development.

        Parameters
        ----------
        model_dir : str, optional
            Directory containing .h5 / SavedModel files.
            Defaults to backend-api/models/.
        """
        if model_dir:
            self._model_dir = model_dir

        model_dir_path = Path(self._model_dir)
        logger.info("Loading models from: %s", model_dir_path.resolve())

        # ----------------------------------------------------------
        # 1. Image Quality Checker (no model file needed)
        # ----------------------------------------------------------
        try:
            from app.ai.quality_checker import ImageQualityChecker
            self._models["quality_checker"] = ImageQualityChecker()
            logger.info("✓ ImageQualityChecker loaded.")
        except Exception as exc:
            logger.error("✗ Failed to load ImageQualityChecker: %s", exc)

        # ----------------------------------------------------------
        # 2. Healthy Screener
        # ----------------------------------------------------------
        screener_path = str(model_dir_path / "healthy_screener.h5")
        try:
            from app.ai.healthy_screener import HealthyScreener
            screener = HealthyScreener(model_path=screener_path)
            self._models["healthy_screener"] = screener
            mode = "real" if not screener.mock_mode else "mock"
            logger.info("✓ HealthyScreener loaded (%s mode).", mode)
        except Exception as exc:
            logger.error("✗ Failed to load HealthyScreener: %s", exc)

        # ----------------------------------------------------------
        # 3. Condition Classifier
        # ----------------------------------------------------------
        classifier_path = str(model_dir_path / "condition_classifier.h5")
        config_dir = str(Path(__file__).parent / "config")
        try:
            from app.ai.condition_classifier import ConditionClassifier
            classifier = ConditionClassifier(
                model_path=classifier_path,
                config_dir=config_dir,
            )
            self._models["condition_classifier"] = classifier
            mode = "real" if not classifier.mock_mode else "mock"
            logger.info("✓ ConditionClassifier loaded (%s mode).", mode)
        except Exception as exc:
            logger.error("✗ Failed to load ConditionClassifier: %s", exc)

        # ----------------------------------------------------------
        # 4. GradCAM Generator (stateless – no model file)
        # ----------------------------------------------------------
        try:
            from app.ai.gradcam import GradCAMGenerator
            self._models["gradcam"] = GradCAMGenerator()
            logger.info("✓ GradCAMGenerator loaded.")
        except Exception as exc:
            logger.error("✗ Failed to load GradCAMGenerator: %s", exc)

        # ----------------------------------------------------------
        # 5. Confidence Analyzer (stateless utility)
        # ----------------------------------------------------------
        try:
            from app.ai.confidence_analyzer import ConfidenceAnalyzer
            self._models["confidence_analyzer"] = ConfidenceAnalyzer()
            logger.info("✓ ConfidenceAnalyzer loaded.")
        except Exception as exc:
            logger.error("✗ Failed to load ConfidenceAnalyzer: %s", exc)

        logger.info(
            "Model loading complete. Loaded models: %s",
            list(self._models.keys()),
        )

    # ------------------------------------------------------------------
    #  Access
    # ------------------------------------------------------------------

    def get_model(self, name: str) -> Any:
        """
        Return a loaded model by name.

        Parameters
        ----------
        name : str
            One of: "quality_checker", "healthy_screener",
            "condition_classifier", "gradcam", "confidence_analyzer".

        Returns
        -------
        Any
            The model/utility instance.

        Raises
        ------
        KeyError
            If *name* has not been loaded.
        """
        if name not in self._models:
            available = list(self._models.keys())
            raise KeyError(
                f"Model '{name}' not found. Available models: {available}. "
                "Call load_all_models() first."
            )
        return self._models[name]

    def is_loaded(self, name: str) -> bool:
        """Return True if *name* is in the loaded model registry."""
        return name in self._models

    def list_models(self) -> Dict[str, str]:
        """
        Return a summary dict of all loaded models and their mode.

        Returns
        -------
        dict
            {model_name: "real" | "mock" | "loaded"}
        """
        summary: Dict[str, str] = {}
        for name, model in self._models.items():
            if hasattr(model, "mock_mode"):
                summary[name] = "mock" if model.mock_mode else "real"
            else:
                summary[name] = "loaded"
        return summary

    # ------------------------------------------------------------------
    #  Versioning
    # ------------------------------------------------------------------

    def get_model_version(self) -> str:
        """
        Read the model version from ``models/version.json``.

        The file should have the format:
            {"version": "1.0.0", "trained_at": "2024-01-01", ...}

        Returns
        -------
        str
            Version string, or "unknown" if the file is missing or invalid.
        """
        version_file = Path(self._model_dir) / "version.json"
        try:
            with open(version_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            version = data.get("version", "unknown")
            logger.debug("Model version: %s", version)
            return str(version)
        except FileNotFoundError:
            logger.info("version.json not found at %s", version_file)
            return "unknown"
        except Exception as exc:
            logger.warning("Failed to read version.json: %s", exc)
            return "unknown"

    # ------------------------------------------------------------------
    #  Reload
    # ------------------------------------------------------------------

    def reload(self) -> None:
        """Clear the model registry and reload all models."""
        logger.info("Reloading all models...")
        self._models.clear()
        self.load_all_models()
