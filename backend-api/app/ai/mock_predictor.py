"""
mock_predictor.py
=================
Development-time mock predictor for SafeSkin AI.

When trained model files (.h5) are not yet available this module returns
realistic-looking predictions so the full API surface can be tested without
GPU infrastructure or a trained model.

All methods seed from Python's random module (no fixed seed) so responses
vary between requests, simulating a real model.
"""

import logging
import random
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Condition class catalogue
# ---------------------------------------------------------------------------
CONDITION_CLASSES = [
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

CONDITION_DISPLAY_NAMES = {
    "acne_vulgaris": "Acne Vulgaris",
    "eczema_atopic_dermatitis": "Eczema / Atopic Dermatitis",
    "psoriasis": "Psoriasis",
    "melanoma": "Melanoma",
    "basal_cell_carcinoma": "Basal Cell Carcinoma",
    "seborrheic_keratosis": "Seborrheic Keratosis",
    "tinea_ringworm": "Tinea / Ringworm",
    "urticaria_hives": "Urticaria / Hives",
    "vitiligo": "Vitiligo",
    "rosacea": "Rosacea",
}

# Conditions that do NOT have a meaningful severity staging
NO_SEVERITY_CONDITIONS = {"melanoma", "basal_cell_carcinoma", "seborrheic_keratosis", "vitiligo"}

SEVERITY_LEVELS = ["mild", "moderate", "severe"]


class MockPredictor:
    """
    Returns realistic mock responses for all SafeSkin AI prediction endpoints.

    Used when:
      - Model .h5 files are not yet present (pre-training phase).
      - Running unit tests without a GPU environment.
      - Local frontend development / API integration testing.

    All responses include ``"mock": True`` so callers can distinguish them
    from real model output and display an appropriate disclaimer to the user.
    """

    # ------------------------------------------------------------------
    #  Quality Check Mock
    # ------------------------------------------------------------------

    def mock_quality_check(self, image_path: str = "") -> Dict[str, Any]:
        """
        Return a mock image quality assessment result.

        Score is randomly drawn from 75-95 to simulate a good-quality image.
        All four checks are passed so the image proceeds to classification.

        Parameters
        ----------
        image_path : str
            Unused in mock mode; accepted for API parity.

        Returns
        -------
        dict
            Same structure as :class:`ImageQualityChecker.check_quality`.
        """
        score = random.randint(75, 95)
        blur_var = round(random.uniform(120.0, 450.0), 2)
        brightness = round(random.uniform(85.0, 175.0), 2)
        width = random.choice([512, 640, 1024, 1280])
        height = random.choice([512, 640, 1024, 1280])
        skin_pct = round(random.uniform(20.0, 65.0), 2)

        return {
            "score": score,
            "status": "good",
            "checks": {
                "blur": {
                    "passed": True,
                    "variance": blur_var,
                    "threshold": 100.0,
                },
                "brightness": {
                    "passed": True,
                    "mean": brightness,
                    "label": "normal",
                    "min_threshold": 40.0,
                    "max_threshold": 220.0,
                },
                "resolution": {
                    "passed": True,
                    "width": width,
                    "height": height,
                    "min_required": "224x224",
                },
                "skin_visibility": {
                    "passed": True,
                    "skin_percentage": skin_pct,
                    "min_required": 5.0,
                },
            },
            "message": f"Image quality is good (score: {score}/100). All checks passed.",
            "mock": True,
        }

    # ------------------------------------------------------------------
    #  Healthy Screening Mock
    # ------------------------------------------------------------------

    def mock_screening(self) -> Dict[str, Any]:
        """
        Return a mock healthy / potentially-affected screening result.

        Probabilities are drawn from a Dirichlet distribution with slightly
        higher weight for 'healthy' (mimicking a realistic class imbalance).

        Returns
        -------
        dict
            Same structure as :class:`HealthyScreener.predict`.
        """
        # Dirichlet alpha: [healthy_weight, affected_weight]
        # Weight healthy slightly more (real-world bias)
        probs = np.random.dirichlet([3.5, 2.5]).astype(float)
        healthy_prob = float(probs[0])
        affected_prob = float(probs[1])

        max_prob = max(healthy_prob, affected_prob)
        if max_prob >= 0.90:
            confidence_level = "high"
            result = "healthy" if healthy_prob > affected_prob else "potentially_affected"
        elif max_prob >= 0.70:
            confidence_level = "moderate"
            result = "healthy" if healthy_prob > affected_prob else "potentially_affected"
        else:
            confidence_level = "low"
            result = "uncertain"

        return {
            "result": result,
            "confidence": round(max_prob, 4),
            "confidence_level": confidence_level,
            "probabilities": {
                "healthy": round(healthy_prob, 4),
                "potentially_affected": round(affected_prob, 4),
            },
            "mock": True,
        }

    # ------------------------------------------------------------------
    #  Condition Classification Mock
    # ------------------------------------------------------------------

    def mock_classification(self) -> Dict[str, Any]:
        """
        Return a mock skin-condition classification result.

        Picks one of the 10 condition classes with a randomly sampled
        Dirichlet probability vector.  The top class receives a boosted
        probability to produce realistic confidence levels.

        Returns
        -------
        dict
            Same structure as :class:`ConditionClassifier.predict`.
        """
        n = len(CONDITION_CLASSES)

        # Boost one class to simulate a peaked distribution
        alphas = np.ones(n, dtype=float) * 0.5
        boosted_idx = random.randint(0, n - 1)
        alphas[boosted_idx] = 4.0

        probs = np.random.dirichlet(alphas).astype(float)
        top_idx = int(np.argmax(probs))
        condition_id = CONDITION_CLASSES[top_idx]
        confidence = float(probs[top_idx])

        # Confidence level
        if confidence >= 0.90:
            confidence_level = "high"
        elif confidence >= 0.70:
            confidence_level = "moderate"
        else:
            confidence_level = "low"

        # Severity estimation
        if condition_id in NO_SEVERITY_CONDITIONS:
            severity = "unable_to_assess"
        else:
            if confidence < 0.50:
                severity = "mild"
            elif confidence < 0.75:
                severity = "moderate"
            else:
                severity = "severe"

        all_probs = {
            CONDITION_CLASSES[i]: round(float(probs[i]), 4) for i in range(n)
        }

        return {
            "condition": condition_id,
            "display_name": CONDITION_DISPLAY_NAMES.get(condition_id, condition_id),
            "confidence": round(confidence, 4),
            "confidence_level": confidence_level,
            "severity_estimate": severity,
            "all_probabilities": all_probs,
            "mock": True,
        }

    # ------------------------------------------------------------------
    #  Full pipeline mock
    # ------------------------------------------------------------------

    def mock_full_pipeline(self, image_path: str = "") -> Dict[str, Any]:
        """
        Simulate the complete SafeSkin AI screening pipeline in mock mode.

        Combines quality check → healthy screening → condition classification
        into a single convenience response for integration testing.

        Returns
        -------
        dict
            {
              "quality":        dict,  # mock_quality_check result
              "screening":      dict,  # mock_screening result
              "classification": dict   # mock_classification result (if affected)
            }
        """
        quality = self.mock_quality_check(image_path)
        screening = self.mock_screening()

        result: Dict[str, Any] = {
            "quality": quality,
            "screening": screening,
            "classification": None,
        }

        # Only run classification if screening suggests a potential issue
        if screening["result"] in ("potentially_affected", "uncertain"):
            result["classification"] = self.mock_classification()

        return result

    # ------------------------------------------------------------------
    #  Grad-CAM mock
    # ------------------------------------------------------------------

    def mock_gradcam_path(
        self, user_id: str = "test-user", screening_id: str = "test-screening"
    ) -> str:
        """
        Return a mock Grad-CAM storage path.

        In production this would be a real Supabase Storage URL.
        In mock mode it returns a placeholder path so the frontend can
        render a 'coming soon' placeholder image.

        Returns
        -------
        str
            Mock storage path string.
        """
        return f"gradcam-results/{user_id}/{screening_id}.png"
