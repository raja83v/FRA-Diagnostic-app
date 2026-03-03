"""
Model Evaluation Module for FRA Fault Classifier.

Provides comprehensive evaluation including:
- Classification metrics (accuracy, precision, recall, F1)
- Confusion matrix analysis
- Per-class AUC-ROC
- Validation against plan thresholds
"""

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler, label_binarize
from xgboost import XGBClassifier

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ml.features.feature_extractor import FRAFeatureExtractor
from ml.data_generation.synthetic_fra import SyntheticDataset, FAULT_TYPES


# Plan validation thresholds
PLAN_THRESHOLDS = {
    "min_accuracy": 0.85,
    "target_accuracy": 0.92,
    "min_recall_per_class": 0.80,
    "target_recall_per_class": 0.90,
    "max_fpr": 0.15,
    "target_fpr": 0.08,
    "min_auc_roc": 0.85,
    "target_auc_roc": 0.93,
}


def evaluate_model(
    model_dir: str | Path,
    version: str = "v1.0.0",
    test_dataset: Optional[SyntheticDataset] = None,
    output_dir: Optional[str | Path] = None,
) -> dict:
    """
    Evaluate a trained model against test data and plan thresholds.

    Args:
        model_dir: Directory containing model artifacts.
        version: Model version string matching saved files.
        test_dataset: Optional test dataset. If None, generates fresh test data.
        output_dir: Where to save evaluation results. Defaults to ml/evaluation/.

    Returns:
        Dict of evaluation metrics.
    """
    model_dir = Path(model_dir)
    output_dir = Path(output_dir) if output_dir else Path("ml/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Load model artifacts
    # ------------------------------------------------------------------
    print("\nLoading model artifacts...")
    model: XGBClassifier = joblib.load(model_dir / f"xgboost_fra_{version}.joblib")
    scaler: StandardScaler = joblib.load(model_dir / f"scaler_{version}.joblib")
    label_encoder: LabelEncoder = joblib.load(model_dir / f"label_encoder_{version}.joblib")

    with open(model_dir / f"feature_names_{version}.json") as f:
        feature_names = json.load(f)

    print(f"  Model: {model_dir / f'xgboost_fra_{version}.joblib'}")
    print(f"  Classes: {list(label_encoder.classes_)}")

    # ------------------------------------------------------------------
    # Prepare test data
    # ------------------------------------------------------------------
    if test_dataset is None:
        print("\nGenerating fresh test dataset (seed=999)...")
        from ml.data_generation.synthetic_fra import SyntheticFRAGenerator
        gen = SyntheticFRAGenerator(seed=999)
        test_dataset = gen.generate(n_healthy=400, n_per_fault=60)

    print(f"\nExtracting features from {len(test_dataset.samples)} test samples...")
    extractor = FRAFeatureExtractor(target_points=800)

    frequencies = np.array([s.frequency_hz for s in test_dataset.samples])
    magnitudes = np.array([s.magnitude_db for s in test_dataset.samples])
    phases = np.array([s.phase_degrees for s in test_dataset.samples])

    X, _ = extractor.extract_batch(frequencies, magnitudes, phases)
    y_true = label_encoder.transform([s.label for s in test_dataset.samples])

    X_scaled = scaler.transform(X)

    # ------------------------------------------------------------------
    # Generate predictions
    # ------------------------------------------------------------------
    print("Running predictions...")
    y_pred = model.predict(X_scaled)
    y_pred_proba = model.predict_proba(X_scaled)

    # ------------------------------------------------------------------
    # Compute metrics
    # ------------------------------------------------------------------
    n_classes = len(label_encoder.classes_)
    target_names = list(label_encoder.classes_)

    accuracy = accuracy_score(y_true, y_pred)
    f1_w = f1_score(y_true, y_pred, average="weighted")

    # Per-class AUC-ROC
    y_true_bin = label_binarize(y_true, classes=list(range(n_classes)))
    per_class_auc = {}
    for idx, cls_name in enumerate(target_names):
        if y_true_bin[:, idx].sum() > 0:
            auc = roc_auc_score(y_true_bin[:, idx], y_pred_proba[:, idx])
            per_class_auc[cls_name] = auc
        else:
            per_class_auc[cls_name] = 0.0
    mean_auc = np.mean(list(per_class_auc.values()))

    # Classification report
    report = classification_report(y_true, y_pred, target_names=target_names, output_dict=True)
    conf_mat = confusion_matrix(y_true, y_pred).tolist()

    # Per-class FPR
    cm = np.array(conf_mat)
    per_class_fpr = {}
    for idx, cls_name in enumerate(target_names):
        fp = cm[:, idx].sum() - cm[idx, idx]
        tn = cm.sum() - cm[idx, :].sum() - cm[:, idx].sum() + cm[idx, idx]
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        per_class_fpr[cls_name] = fpr

    # ------------------------------------------------------------------
    # Validate against plan thresholds
    # ------------------------------------------------------------------
    validations = {
        "accuracy_min_pass": accuracy >= PLAN_THRESHOLDS["min_accuracy"],
        "accuracy_target_pass": accuracy >= PLAN_THRESHOLDS["target_accuracy"],
        "all_recall_min_pass": all(
            report.get(cls, {}).get("recall", 0) >= PLAN_THRESHOLDS["min_recall_per_class"]
            for cls in target_names
        ),
        "all_fpr_max_pass": all(
            v < PLAN_THRESHOLDS["max_fpr"] for v in per_class_fpr.values()
        ),
        "auc_roc_min_pass": mean_auc >= PLAN_THRESHOLDS["min_auc_roc"],
    }

    # ------------------------------------------------------------------
    # Build results
    # ------------------------------------------------------------------
    results = {
        "version": version,
        "n_test_samples": len(y_true),
        "accuracy": accuracy,
        "f1_weighted": f1_w,
        "mean_auc_roc": mean_auc,
        "per_class_auc_roc": per_class_auc,
        "per_class_fpr": per_class_fpr,
        "confusion_matrix": conf_mat,
        "classification_report": report,
        "validations": validations,
        "thresholds": PLAN_THRESHOLDS,
    }

    # ------------------------------------------------------------------
    # Print results
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"  Accuracy:        {accuracy:.4f}  (min: {PLAN_THRESHOLDS['min_accuracy']}, target: {PLAN_THRESHOLDS['target_accuracy']})")
    print(f"  F1 (weighted):   {f1_w:.4f}")
    print(f"  Mean AUC-ROC:    {mean_auc:.4f}  (min: {PLAN_THRESHOLDS['min_auc_roc']}, target: {PLAN_THRESHOLDS['target_auc_roc']})")

    print(f"\n  Per-class AUC-ROC:")
    for cls_name, auc in per_class_auc.items():
        status = "✓" if auc >= PLAN_THRESHOLDS["min_auc_roc"] else "✗"
        print(f"    {status} {cls_name}: {auc:.4f}")

    print(f"\n  Per-class recall:")
    for cls_name in target_names:
        if cls_name in report:
            r = report[cls_name]["recall"]
            status = "✓" if r >= PLAN_THRESHOLDS["min_recall_per_class"] else "✗"
            print(f"    {status} {cls_name}: {r:.4f}")

    print(f"\n  Threshold validation:")
    for check, passed in validations.items():
        print(f"    {'✓' if passed else '✗'} {check}: {'PASS' if passed else 'FAIL'}")

    # ------------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------------
    results_path = output_dir / f"evaluation_{version}.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {results_path}")

    return results
