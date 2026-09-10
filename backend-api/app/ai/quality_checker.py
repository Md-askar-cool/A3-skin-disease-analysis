"""
quality_checker.py
==================
OpenCV-based image quality assessment for SafeSkin AI.

The ImageQualityChecker evaluates uploaded images on four axes:
  - Blur      (Laplacian variance)
  - Brightness (mean pixel intensity)
  - Resolution (minimum dimension check)
  - Skin Visibility (HSV-range skin-colour detection)

A weighted score (0-100) and a human-readable status are returned.
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


class ImageQualityChecker:
    """
    Assesses the quality of a skin-lesion image before it is passed to
    the AI classification pipeline.

    Returns a structured dict so the API can gate low-quality images and
    prompt the user to retake the photo before wasting GPU inference time.
    """

    # ------------------------------------------------------------------ #
    #  Thresholds – adjust here without touching logic                     #
    # ------------------------------------------------------------------ #
    BLUR_THRESHOLD = 100.0          # Laplacian variance below this → blurry
    MIN_BRIGHTNESS = 40.0           # Mean pixel value below this → too dark
    MAX_BRIGHTNESS = 220.0          # Mean pixel value above this → too bright
    MIN_WIDTH = 224                 # px
    MIN_HEIGHT = 224                # px
    MIN_SKIN_PERCENTAGE = 5.0       # At least 5 % of pixels should be skin-tone

    # Weighted contribution of each check to the final score
    WEIGHTS = {
        "blur": 0.30,
        "brightness": 0.25,
        "resolution": 0.20,
        "skin_visibility": 0.25,
    }

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def check_quality(self, image_path: str) -> Dict[str, Any]:
        """
        Run all quality checks on *image_path* and return a summary dict.

        Parameters
        ----------
        image_path : str
            Absolute or relative path to the image file.

        Returns
        -------
        dict
            {
              "score": int,          # 0-100 overall quality score
              "status": str,         # "good" | "poor" | "unacceptable"
              "checks": {
                "blur":           {"passed": bool, "variance": float},
                "brightness":     {"passed": bool, "mean": float, "label": str},
                "resolution":     {"passed": bool, "width": int, "height": int},
                "skin_visibility":{"passed": bool, "skin_percentage": float},
              },
              "message": str         # Human-readable summary
            }
        """
        img = self._load_image(image_path)
        if img is None:
            return self._error_result(f"Could not load image: {image_path}")

        # Run individual checks
        blur_ok, blur_var = self._check_blur(img)
        bright_ok, bright_mean, bright_label = self._check_brightness(img)
        res_ok, (width, height) = self._check_resolution(img)
        skin_ok, skin_pct = self._estimate_skin_visibility(img)

        checks: Dict[str, Any] = {
            "blur": {
                "passed": blur_ok,
                "variance": round(float(blur_var), 2),
                "threshold": self.BLUR_THRESHOLD,
            },
            "brightness": {
                "passed": bright_ok,
                "mean": round(float(bright_mean), 2),
                "label": bright_label,
                "min_threshold": self.MIN_BRIGHTNESS,
                "max_threshold": self.MAX_BRIGHTNESS,
            },
            "resolution": {
                "passed": res_ok,
                "width": int(width),
                "height": int(height),
                "min_required": f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}",
            },
            "skin_visibility": {
                "passed": skin_ok,
                "skin_percentage": round(float(skin_pct), 2),
                "min_required": self.MIN_SKIN_PERCENTAGE,
            },
        }

        score = self._compute_score(checks)
        status = self._score_to_status(score)
        message = self._build_message(score, status, checks)

        logger.info(
            "Quality check complete | path=%s score=%d status=%s",
            image_path, score, status,
        )

        return {
            "score": score,
            "status": status,
            "checks": checks,
            "message": message,
        }

    # ------------------------------------------------------------------ #
    #  Individual quality checks                                           #
    # ------------------------------------------------------------------ #

    def _check_blur(self, img: np.ndarray) -> Tuple[bool, float]:
        """
        Detect image blur using the Laplacian variance method.

        A sharp image has high edge energy → high variance of the Laplacian.
        A blurry image has low variance.

        Parameters
        ----------
        img : np.ndarray
            BGR image array (as loaded by OpenCV).

        Returns
        -------
        (is_clear, variance_value)
            is_clear = True  → image is sharp enough
            variance_value   → raw Laplacian variance (higher = sharper)
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        is_clear = variance >= self.BLUR_THRESHOLD
        return is_clear, variance

    def _check_brightness(
        self, img: np.ndarray
    ) -> Tuple[bool, float, str]:
        """
        Check whether the image has acceptable brightness.

        Parameters
        ----------
        img : np.ndarray
            BGR image array.

        Returns
        -------
        (is_acceptable, mean_brightness, label)
            label ∈ {'normal', 'too_dark', 'too_bright'}
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(gray.mean())

        if mean_brightness < self.MIN_BRIGHTNESS:
            return False, mean_brightness, "too_dark"
        if mean_brightness > self.MAX_BRIGHTNESS:
            return False, mean_brightness, "too_bright"
        return True, mean_brightness, "normal"

    def _check_resolution(
        self, img: np.ndarray
    ) -> Tuple[bool, Tuple[int, int]]:
        """
        Verify that the image meets the minimum resolution requirement (224×224).

        Parameters
        ----------
        img : np.ndarray
            BGR image array.

        Returns
        -------
        (is_acceptable, (width, height))
        """
        height, width = img.shape[:2]
        is_acceptable = (width >= self.MIN_WIDTH) and (height >= self.MIN_HEIGHT)
        return is_acceptable, (width, height)

    def _estimate_skin_visibility(
        self, img: np.ndarray
    ) -> Tuple[bool, float]:
        """
        Estimate the percentage of skin-tone pixels using HSV colour ranges.

        Two HSV ranges are combined to cover diverse skin tones:
          • Range 1: H 0–20   (warm reds / browns)
          • Range 2: H 170–180 (very-red end of the hue circle)

        Parameters
        ----------
        img : np.ndarray
            BGR image array.

        Returns
        -------
        (has_skin, skin_percentage)
            has_skin = True if at least MIN_SKIN_PERCENTAGE % of pixels are skin-tone.
            skin_percentage = fraction of pixels classified as skin (0-100).
        """
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Range 1: covers beige/brown/tan (H: 0-20)
        lower1 = np.array([0, 20, 70], dtype=np.uint8)
        upper1 = np.array([20, 255, 255], dtype=np.uint8)

        # Range 2: covers deep-red skin tones near 180° boundary (H: 170-180)
        lower2 = np.array([170, 20, 70], dtype=np.uint8)
        upper2 = np.array([180, 255, 255], dtype=np.uint8)

        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        skin_mask = cv2.bitwise_or(mask1, mask2)

        total_pixels = img.shape[0] * img.shape[1]
        skin_pixels = int(cv2.countNonZero(skin_mask))
        skin_percentage = (skin_pixels / total_pixels) * 100.0

        has_skin = skin_percentage >= self.MIN_SKIN_PERCENTAGE
        return has_skin, skin_percentage

    # ------------------------------------------------------------------ #
    #  Score computation                                                   #
    # ------------------------------------------------------------------ #

    def _compute_score(self, checks: Dict[str, Any]) -> int:
        """
        Compute weighted quality score (0-100).

        Weights:
          blur             30 %
          brightness       25 %
          resolution       20 %
          skin_visibility  25 %

        Each check contributes its full weight when passed, zero when failed.
        Within the brightness check a partial score is awarded based on how
        far the mean is from the acceptable range.

        Returns
        -------
        int
            0-100 quality score.
        """
        score = 0.0

        # --- Blur sub-score (0-30) ---
        blur_var = checks["blur"]["variance"]
        # Cap blur score at 2× threshold for headroom
        blur_sub = min(blur_var / (self.BLUR_THRESHOLD * 2), 1.0)
        score += blur_sub * self.WEIGHTS["blur"] * 100

        # --- Brightness sub-score (0-25) ---
        mean_b = checks["brightness"]["mean"]
        label = checks["brightness"]["label"]
        if label == "normal":
            # Ideal brightness is around 128; penalise deviation within the valid range
            deviation = abs(mean_b - 128) / 128
            bright_sub = max(0.0, 1.0 - deviation * 0.5)
        elif label == "too_dark":
            bright_sub = max(0.0, mean_b / self.MIN_BRIGHTNESS) * 0.4
        else:  # too_bright
            remaining = 255 - mean_b
            bright_sub = max(0.0, remaining / (255 - self.MAX_BRIGHTNESS)) * 0.4
        score += bright_sub * self.WEIGHTS["brightness"] * 100

        # --- Resolution sub-score (0-20) ---
        if checks["resolution"]["passed"]:
            # Bonus for larger images (up to 1024 on shortest side)
            min_dim = min(checks["resolution"]["width"], checks["resolution"]["height"])
            res_sub = min(min_dim / 1024, 1.0)
        else:
            min_dim = min(checks["resolution"]["width"], checks["resolution"]["height"])
            res_sub = (min_dim / self.MIN_WIDTH) * 0.5
        score += res_sub * self.WEIGHTS["resolution"] * 100

        # --- Skin visibility sub-score (0-25) ---
        skin_pct = checks["skin_visibility"]["skin_percentage"]
        # Target is ~40 % skin; penalise above 90 % (likely macro-only, no context)
        if skin_pct < self.MIN_SKIN_PERCENTAGE:
            skin_sub = skin_pct / self.MIN_SKIN_PERCENTAGE * 0.3
        elif skin_pct > 90:
            skin_sub = 0.7  # very high coverage – still acceptable
        else:
            skin_sub = min(skin_pct / 40.0, 1.0)
        score += skin_sub * self.WEIGHTS["skin_visibility"] * 100

        return int(round(min(max(score, 0), 100)))

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _load_image(self, image_path: str) -> np.ndarray | None:
        """Load image via OpenCV; return None on failure."""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning("cv2.imread returned None for path: %s", image_path)
            return img
        except Exception as exc:
            logger.error("Failed to load image %s: %s", image_path, exc)
            return None

    @staticmethod
    def _score_to_status(score: int) -> str:
        """Map numeric score to categorical status."""
        if score >= 70:
            return "good"
        if score >= 40:
            return "poor"
        return "unacceptable"

    @staticmethod
    def _build_message(score: int, status: str, checks: Dict[str, Any]) -> str:
        """Build a human-readable quality summary message."""
        failed = [k for k, v in checks.items() if not v["passed"]]
        if not failed:
            return f"Image quality is {status} (score: {score}/100). All checks passed."
        issues = ", ".join(failed).replace("_", " ")
        return (
            f"Image quality is {status} (score: {score}/100). "
            f"Issues detected: {issues}. Please retake the photo."
        )

    @staticmethod
    def _error_result(message: str) -> Dict[str, Any]:
        """Return a structured error result when the image cannot be loaded."""
        return {
            "score": 0,
            "status": "unacceptable",
            "checks": {},
            "message": message,
        }
