"""
confidence_analyzer.py
======================
Confidence analysis and probabilistic calibration utilities for SafeSkin AI.

This module provides:
  - Threshold-based confidence classification (high / moderate / low)
  - Temperature scaling for post-hoc calibration of over-confident models
  - Shannon entropy for measuring prediction uncertainty
  - Simple entropy-based out-of-distribution (OOD) detection

These tools are applied after the primary classifiers to decide whether to
surface a result to the user or request a GP review.
"""

import logging
import math
from typing import Dict, Any

import numpy as np

logger = logging.getLogger(__name__)


class ConfidenceAnalyzer:
    """
    Analyzes and calibrates model prediction confidence.

    Attributes
    ----------
    HIGH_THRESHOLD : float
        Minimum confidence for a 'high' confidence classification (0.90).
    MODERATE_THRESHOLD : float
        Minimum confidence for a 'moderate' confidence classification (0.70).

    Usage
    -----
        analyzer = ConfidenceAnalyzer()
        result = analyzer.analyze(confidence=0.85)
        # {"level": "moderate", "is_confident": True, "recommendation": "..."}

        calibrated = analyzer.apply_temperature_scaling(logits, temperature=1.5)
        entropy = analyzer.compute_entropy(probabilities)
        ood = analyzer.is_out_of_distribution(entropy)
    """

    HIGH_THRESHOLD: float = 0.90
    MODERATE_THRESHOLD: float = 0.70

    # ------------------------------------------------------------------
    #  Primary confidence analysis
    # ------------------------------------------------------------------

    def analyze(self, confidence: float) -> Dict[str, Any]:
        """
        Analyse a scalar confidence score and return actionable metadata.

        Parameters
        ----------
        confidence : float
            Predicted probability of the top class (0.0 – 1.0).

        Returns
        -------
        dict
            {
              "level":          str,   # "high" | "moderate" | "low"
              "is_confident":   bool,  # True for high or moderate
              "recommendation": str,   # Advice string for the frontend
              "confidence":     float  # Echo the input for convenience
            }
        """
        confidence = float(np.clip(confidence, 0.0, 1.0))

        if confidence >= self.HIGH_THRESHOLD:
            level = "high"
            is_confident = True
            recommendation = (
                "The AI has high confidence in this result. "
                "Please consult a dermatologist to confirm the diagnosis."
            )
        elif confidence >= self.MODERATE_THRESHOLD:
            level = "moderate"
            is_confident = True
            recommendation = (
                "The AI has moderate confidence. "
                "A dermatologist visit is strongly recommended for an accurate diagnosis."
            )
        else:
            level = "low"
            is_confident = False
            recommendation = (
                "The AI confidence is low. The image quality may be poor, or "
                "the condition may not match any known category. "
                "Please retake the photo or consult a medical professional directly."
            )

        return {
            "level": level,
            "is_confident": is_confident,
            "recommendation": recommendation,
            "confidence": round(confidence, 4),
        }

    # ------------------------------------------------------------------
    #  Temperature scaling
    # ------------------------------------------------------------------

    def apply_temperature_scaling(
        self, logits: np.ndarray, temperature: float = 1.5
    ) -> np.ndarray:
        """
        Apply temperature scaling to calibrate model confidence.

        Neural networks are often overconfident (produce probabilities too
        close to 1.0). Dividing the logits by a temperature T > 1 softens
        the distribution, yielding better-calibrated probabilities.

        Formula:
            p_i = exp(z_i / T) / Σ exp(z_j / T)

        Parameters
        ----------
        logits : np.ndarray
            Raw pre-softmax logit scores, shape (num_classes,) or
            (batch, num_classes).
        temperature : float
            Scaling factor. T = 1.0 is unchanged; T > 1 softens; T < 1 sharpens.
            Default 1.5 is a sensible starting value for over-confident models.

        Returns
        -------
        np.ndarray
            Calibrated softmax probabilities with the same shape as *logits*.
        """
        if temperature <= 0:
            raise ValueError(f"temperature must be > 0, got {temperature}")

        scaled_logits = np.array(logits, dtype=np.float64) / temperature

        # Numerically stable softmax
        shifted = scaled_logits - np.max(scaled_logits, axis=-1, keepdims=True)
        exp_vals = np.exp(shifted)
        probs = exp_vals / np.sum(exp_vals, axis=-1, keepdims=True)

        logger.debug(
            "Temperature scaling applied: T=%.2f | max_prob before=%.4f, after=%.4f",
            temperature,
            float(np.max(np.exp(logits - np.max(logits)) / np.sum(np.exp(logits - np.max(logits))))),
            float(np.max(probs)),
        )

        return probs.astype(np.float32)

    # ------------------------------------------------------------------
    #  Shannon entropy
    # ------------------------------------------------------------------

    def compute_entropy(self, probabilities: np.ndarray) -> float:
        """
        Compute the Shannon entropy of a probability distribution.

        Entropy measures how 'spread out' the probabilities are:
          - Low entropy  → peaked distribution → confident prediction
          - High entropy → flat distribution  → uncertain prediction

        Formula:
            H = -Σ p_i * log2(p_i)

        The result is normalised to [0, 1] by dividing by log2(num_classes)
        so it is comparable across models with different numbers of classes.

        Parameters
        ----------
        probabilities : np.ndarray
            Probability distribution, shape (num_classes,) or (batch, num_classes).
            Values must sum to 1 (or close to 1 after normalisation).

        Returns
        -------
        float
            Normalised Shannon entropy in [0, 1].
            Returns 0.0 if probabilities has only one element.
        """
        probs = np.array(probabilities, dtype=np.float64)
        if probs.ndim > 1:
            # Take the first sample in a batch
            probs = probs[0]

        num_classes = len(probs)
        if num_classes <= 1:
            return 0.0

        # Clip to avoid log(0)
        probs = np.clip(probs, 1e-10, 1.0)

        raw_entropy = -np.sum(probs * np.log2(probs))
        max_entropy = math.log2(num_classes)     # H_max = log2(K)
        normalised_entropy = raw_entropy / max_entropy

        return float(np.clip(normalised_entropy, 0.0, 1.0))

    # ------------------------------------------------------------------
    #  Out-of-distribution detection
    # ------------------------------------------------------------------

    def is_out_of_distribution(
        self, entropy: float, threshold: float = 0.8
    ) -> bool:
        """
        Determine whether a sample is likely out-of-distribution (OOD).

        A simple entropy-based heuristic: if the model's probability
        distribution is very flat (high entropy), the input image probably
        does not belong to any of the training categories.

        Parameters
        ----------
        entropy : float
            Normalised Shannon entropy from :meth:`compute_entropy` (0-1).
        threshold : float
            Entropy level above which the sample is flagged as OOD.
            Default 0.8 means 80 % of maximum possible entropy.

        Returns
        -------
        bool
            True  → sample is likely OOD; do not trust the prediction.
            False → sample appears to be in-distribution.
        """
        is_ood = entropy > threshold
        if is_ood:
            logger.warning(
                "OOD detected: entropy=%.4f > threshold=%.4f. "
                "Prediction should not be trusted.",
                entropy, threshold,
            )
        return is_ood

    # ------------------------------------------------------------------
    #  Composite analysis helper
    # ------------------------------------------------------------------

    def full_analysis(
        self,
        probabilities: np.ndarray,
        logits: np.ndarray | None = None,
        temperature: float = 1.5,
        ood_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Run the complete confidence analysis pipeline:
          1. Optionally apply temperature scaling to logits.
          2. Compute Shannon entropy.
          3. Check OOD status.
          4. Analyse top-class confidence.

        Parameters
        ----------
        probabilities : np.ndarray
            Raw softmax probabilities (after forward pass).
        logits : np.ndarray, optional
            Pre-softmax logits. If provided, temperature scaling is applied
            and the result replaces *probabilities* for the analysis.
        temperature : float
            Temperature for scaling (ignored when logits is None).
        ood_threshold : float
            Entropy threshold for OOD detection.

        Returns
        -------
        dict
            Combined analysis result.
        """
        probs = np.array(probabilities, dtype=np.float32)

        # Apply calibration if logits are available
        if logits is not None:
            probs = self.apply_temperature_scaling(logits, temperature)

        # Flatten batch dimension if present
        if probs.ndim > 1:
            probs = probs[0]

        entropy = self.compute_entropy(probs)
        ood = self.is_out_of_distribution(entropy, ood_threshold)
        top_confidence = float(np.max(probs))
        confidence_info = self.analyze(top_confidence)

        return {
            **confidence_info,
            "entropy": round(entropy, 4),
            "is_out_of_distribution": ood,
            "calibrated": logits is not None,
        }
