"""
SafeSkin AI – ai package
========================
This package contains all AI/ML modules used by the SafeSkin backend API:

  quality_checker       – OpenCV-based image quality assessment
  healthy_screener      – Binary EfficientNetB0 classifier (healthy vs affected)
  condition_classifier  – Multi-class skin-condition classifier
  gradcam               – Grad-CAM explainability heatmap generator
  confidence_analyzer   – Prediction confidence calibration & OOD detection
  model_loader          – Singleton registry that loads and serves all models
  mock_predictor        – Development-time mock responses (no real models needed)
  performance_metrics   – Accuracy / AUC / ROC / confusion-matrix utilities

Usage example
-------------
    from app.ai.model_loader import ModelLoader
    from app.ai.quality_checker import ImageQualityChecker
    from app.ai.healthy_screener import HealthyScreener
    from app.ai.condition_classifier import ConditionClassifier
    from app.ai.gradcam import GradCAMGenerator
    from app.ai.confidence_analyzer import ConfidenceAnalyzer
"""

__version__ = "1.0.0"
__author__ = "SafeSkin AI Team"
