"""
performance_metrics.py
======================
Model evaluation metrics for SafeSkin AI classifiers.

Provides comprehensive metrics for binary and multi-class classifiers:
  - Accuracy, Precision, Recall (Sensitivity), Specificity
  - F1-Score, False-Positive Rate, False-Negative Rate
  - Confusion matrix
  - Per-class metrics
  - ROC curve data and AUC score

All methods are pure functions operating on NumPy arrays, making them
easy to call from both training scripts and the model evaluation CLI.
"""

import logging
from typing import Dict, Any, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional scikit-learn import (used for ROC / AUC)
# ---------------------------------------------------------------------------
try:
    from sklearn.metrics import (  # type: ignore
        roc_curve,
        auc,
        confusion_matrix as sk_confusion_matrix,
    )
    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed – ROC/AUC metrics unavailable.")


class PerformanceMetrics:
    """
    Computes classification performance metrics for SafeSkin AI models.

    Usage (binary)
    --------------
        metrics = PerformanceMetrics()
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 1])
        y_prob = np.array([0.1, 0.9, 0.4, 0.2, 0.85])
        result = metrics.compute_metrics(y_true, y_pred, y_prob)

    Usage (multi-class)
    -------------------
        y_true = np.array([0, 1, 2, 1, 0])
        y_pred = np.array([0, 2, 2, 1, 0])
        y_prob = np.random.dirichlet(np.ones(3), size=5)
        result = metrics.compute_metrics(y_true, y_pred, y_prob)
    """

    # ------------------------------------------------------------------
    #  Primary metrics computation
    # ------------------------------------------------------------------

    def compute_metrics(
        self,
        y_true: Union[np.ndarray, List],
        y_pred: Union[np.ndarray, List],
        y_prob: Optional[Union[np.ndarray, List]] = None,
        class_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute a comprehensive set of classification metrics.

        Parameters
        ----------
        y_true : array-like of int
            Ground-truth class indices.
        y_pred : array-like of int
            Predicted class indices.
        y_prob : array-like, optional
            For binary: 1-D array of positive-class probabilities.
            For multi-class: 2-D array of shape (n_samples, n_classes).
        class_names : list of str, optional
            Human-readable names for each class index.

        Returns
        -------
        dict
            {
              "accuracy":         float,
              "precision":        float,   # macro-averaged
              "recall":           float,   # macro-averaged (= sensitivity)
              "specificity":      float,   # macro-averaged
              "f1":               float,   # macro-averaged
              "fpr":              float,   # macro-averaged false-positive rate
              "fnr":              float,   # macro-averaged false-negative rate
              "confusion_matrix": list[list[int]],
              "per_class":        {class_name: {precision, recall, f1, support}},
              "num_classes":      int,
              "n_samples":        int,
            }
        """
        y_true = np.array(y_true, dtype=int)
        y_pred = np.array(y_pred, dtype=int)
        n_samples = len(y_true)

        classes = sorted(np.unique(np.concatenate([y_true, y_pred])).tolist())
        n_classes = len(classes)

        if class_names and len(class_names) >= n_classes:
            label_map = {cls: class_names[cls] for cls in classes}
        else:
            label_map = {cls: f"class_{cls}" for cls in classes}

        # Overall accuracy
        accuracy = float(np.mean(y_true == y_pred))

        # Confusion matrix
        cm = self._confusion_matrix(y_true, y_pred, classes)

        # Per-class metrics
        per_class: Dict[str, Dict[str, float]] = {}
        precisions, recalls, specificities, f1s, fprs, fnrs = [], [], [], [], [], []

        for cls in classes:
            tp = int(cm[cls][cls])
            fp = int(sum(cm[other][cls] for other in classes if other != cls))
            fn = int(sum(cm[cls][other] for other in classes if other != cls))
            tn = int(
                sum(
                    cm[r][c]
                    for r in classes
                    for c in classes
                    if r != cls and c != cls
                )
            )
            support = int(np.sum(y_true == cls))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0          # sensitivity
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

            precisions.append(precision)
            recalls.append(recall)
            specificities.append(specificity)
            f1s.append(f1)
            fprs.append(fpr)
            fnrs.append(fnr)

            per_class[label_map[cls]] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "specificity": round(specificity, 4),
                "f1": round(f1, 4),
                "fpr": round(fpr, 4),
                "fnr": round(fnr, 4),
                "support": support,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
            }

        # Macro-averaged overall metrics
        result: Dict[str, Any] = {
            "accuracy": round(accuracy, 4),
            "precision": round(float(np.mean(precisions)), 4),
            "recall": round(float(np.mean(recalls)), 4),
            "specificity": round(float(np.mean(specificities)), 4),
            "f1": round(float(np.mean(f1s)), 4),
            "fpr": round(float(np.mean(fprs)), 4),
            "fnr": round(float(np.mean(fnrs)), 4),
            "confusion_matrix": [
                [int(cm[r][c]) for c in classes] for r in classes
            ],
            "confusion_matrix_labels": [label_map[c] for c in classes],
            "per_class": per_class,
            "num_classes": n_classes,
            "n_samples": n_samples,
        }

        logger.info(
            "Metrics computed | accuracy=%.4f, f1=%.4f, n=%d",
            accuracy, result["f1"], n_samples,
        )
        return result

    # ------------------------------------------------------------------
    #  ROC / AUC
    # ------------------------------------------------------------------

    def compute_roc_data(
        self,
        y_true: Union[np.ndarray, List],
        y_prob: Union[np.ndarray, List],
        class_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute ROC curve data and AUC scores.

        For binary classification a single ROC curve is returned.
        For multi-class, one-vs-rest ROC curves are returned per class.

        Parameters
        ----------
        y_true : array-like of int
            Ground-truth class labels.
        y_prob : array-like
            For binary: 1-D array of positive-class probabilities.
            For multi-class: 2-D (n_samples, n_classes).
        class_names : list of str, optional

        Returns
        -------
        dict
            {
              "binary" or "per_class": {
                class_name: {
                  "fpr": list[float],
                  "tpr": list[float],
                  "thresholds": list[float],
                  "auc": float,
                }
              },
              "macro_auc": float
            }
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn is required for ROC computation."}

        y_true = np.array(y_true, dtype=int)
        y_prob = np.array(y_prob, dtype=float)

        classes = sorted(np.unique(y_true).tolist())
        n_classes = len(classes)

        if class_names and len(class_names) >= n_classes:
            label_map = {cls: class_names[cls] for cls in classes}
        else:
            label_map = {cls: f"class_{cls}" for cls in classes}

        roc_results: Dict[str, Any] = {}
        auc_scores: List[float] = []

        if n_classes == 2 and y_prob.ndim == 1:
            # Binary classification
            fpr_arr, tpr_arr, thresholds = roc_curve(y_true, y_prob)
            auc_score = float(auc(fpr_arr, tpr_arr))
            auc_scores.append(auc_score)
            roc_results["binary"] = {
                "fpr": _round_list(fpr_arr.tolist()),
                "tpr": _round_list(tpr_arr.tolist()),
                "thresholds": _round_list(thresholds.tolist()),
                "auc": round(auc_score, 4),
            }
        else:
            # Multi-class: One-vs-Rest
            if y_prob.ndim == 1:
                raise ValueError(
                    "For multi-class ROC, y_prob must be 2-D (n_samples, n_classes)."
                )
            per_class_roc: Dict[str, Any] = {}
            for cls in classes:
                binary_true = (y_true == cls).astype(int)
                cls_prob = y_prob[:, cls]
                fpr_arr, tpr_arr, thresholds = roc_curve(binary_true, cls_prob)
                auc_score = float(auc(fpr_arr, tpr_arr))
                auc_scores.append(auc_score)
                per_class_roc[label_map[cls]] = {
                    "fpr": _round_list(fpr_arr.tolist()),
                    "tpr": _round_list(tpr_arr.tolist()),
                    "thresholds": _round_list(thresholds.tolist()),
                    "auc": round(auc_score, 4),
                }
            roc_results["per_class"] = per_class_roc

        roc_results["macro_auc"] = round(float(np.mean(auc_scores)), 4)
        logger.info("ROC data computed | macro_auc=%.4f", roc_results["macro_auc"])
        return roc_results

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _confusion_matrix(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        classes: List[int],
    ) -> Dict[int, Dict[int, int]]:
        """
        Build a nested-dict confusion matrix: cm[true_class][pred_class] = count.

        This is a pure-numpy implementation that does not require scikit-learn.
        """
        cm: Dict[int, Dict[int, int]] = {
            r: {c: 0 for c in classes} for r in classes
        }
        for true_label, pred_label in zip(y_true, y_pred):
            if true_label in cm and pred_label in cm[true_label]:
                cm[int(true_label)][int(pred_label)] += 1
        return cm

    def print_report(self, metrics: Dict[str, Any]) -> None:
        """Pretty-print a metrics dict to stdout (useful in training scripts)."""
        print("\n" + "=" * 60)
        print("  SafeSkin AI – Model Performance Report")
        print("=" * 60)
        print(f"  Samples     : {metrics.get('n_samples', 'N/A')}")
        print(f"  Classes     : {metrics.get('num_classes', 'N/A')}")
        print("-" * 60)
        print(f"  Accuracy    : {metrics.get('accuracy', 0):.4f}")
        print(f"  Precision   : {metrics.get('precision', 0):.4f}  (macro)")
        print(f"  Recall      : {metrics.get('recall', 0):.4f}  (macro)")
        print(f"  Specificity : {metrics.get('specificity', 0):.4f}  (macro)")
        print(f"  F1-Score    : {metrics.get('f1', 0):.4f}  (macro)")
        print(f"  FPR         : {metrics.get('fpr', 0):.4f}  (macro)")
        print(f"  FNR         : {metrics.get('fnr', 0):.4f}  (macro)")
        print("-" * 60)
        print("  Per-class breakdown:")
        for cls_name, cls_metrics in metrics.get("per_class", {}).items():
            print(
                f"    {cls_name:<35} "
                f"P={cls_metrics['precision']:.3f} "
                f"R={cls_metrics['recall']:.3f} "
                f"F1={cls_metrics['f1']:.3f} "
                f"(n={cls_metrics['support']})"
            )
        print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _round_list(values: List[float], decimals: int = 4) -> List[float]:
    """Round all floats in a list to *decimals* decimal places."""
    return [round(float(v), decimals) for v in values]
