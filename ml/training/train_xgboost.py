"""
XGBoost Training Pipeline for FRA Fault Classification.

Trains a multi-class gradient boosting classifier on extracted FRA features.
Handles class imbalance, hyperparameter tuning, and model serialization.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.model_selection import (
    StratifiedKFold,
    RandomizedSearchCV,
    train_test_split,
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    recall_score,
    precision_score,
)
from xgboost import XGBClassifier

import sys, os
# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ml.features.feature_extractor import FRAFeatureExtractor
from ml.data_generation.synthetic_fra import SyntheticDataset, FAULT_TYPES


# ---------------------------------------------------------------------------
# Training result container
# ---------------------------------------------------------------------------

@dataclass
class TrainingResult:
    """Result of a training run."""
    model: XGBClassifier
    scaler: StandardScaler
    label_encoder: LabelEncoder
    feature_names: list[str]
    metrics: dict
    training_duration_seconds: float
    n_samples: int

    def save(self, model_dir: str | Path, version: str = "v1.0.0") -> dict[str, str]:
        """
        Save all model artifacts to disk.

        Returns dict of saved file paths.
        """
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Save XGBoost model
        model_path = model_dir / f"xgboost_fra_{version}.joblib"
        joblib.dump(self.model, model_path)
        paths["model"] = str(model_path)

        # Save scaler
        scaler_path = model_dir / f"scaler_{version}.joblib"
        joblib.dump(self.scaler, scaler_path)
        paths["scaler"] = str(scaler_path)

        # Save label encoder
        encoder_path = model_dir / f"label_encoder_{version}.joblib"
        joblib.dump(self.label_encoder, encoder_path)
        paths["label_encoder"] = str(encoder_path)

        # Save feature names
        names_path = model_dir / f"feature_names_{version}.json"
        with open(names_path, "w") as f:
            json.dump(self.feature_names, f, indent=2)
        paths["feature_names"] = str(names_path)

        # Save metrics
        metrics_path = model_dir / f"metrics_{version}.json"
        with open(metrics_path, "w") as f:
            json.dump(self.metrics, f, indent=2, default=str)
        paths["metrics"] = str(metrics_path)

        print(f"\nModel artifacts saved to {model_dir}/")
        for name, p in paths.items():
            print(f"  {name}: {p}")

        return paths


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train_xgboost_classifier(
    dataset: SyntheticDataset,
    test_size: float = 0.2,
    tune_hyperparams: bool = True,
    n_iter_search: int = 20,
    random_state: int = 42,
) -> TrainingResult:
    """
    Train an XGBoost classifier on FRA features.

    Args:
        dataset: SyntheticDataset with FRA samples and labels.
        test_size: Fraction of data for test set.
        tune_hyperparams: Whether to run hyperparameter search.
        n_iter_search: Number of parameter combinations to try.
        random_state: Random seed for reproducibility.

    Returns:
        TrainingResult with model, scaler, metrics.
    """
    start_time = time.time()

    print("=" * 60)
    print("XGBoost FRA Fault Classification Training")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Feature extraction
    # ------------------------------------------------------------------
    print("\n[1/5] Extracting features...")
    extractor = FRAFeatureExtractor(target_points=800)

    frequencies = np.array([s.frequency_hz for s in dataset.samples])
    magnitudes = np.array([s.magnitude_db for s in dataset.samples])
    phases = np.array([s.phase_degrees for s in dataset.samples])

    X, feature_names = extractor.extract_batch(frequencies, magnitudes, phases)
    labels = np.array([s.label for s in dataset.samples])

    print(f"  Feature matrix shape: {X.shape}")
    print(f"  Number of features: {len(feature_names)}")

    # ------------------------------------------------------------------
    # Step 2: Encode labels and split data
    # ------------------------------------------------------------------
    print("\n[2/5] Preparing train/test split...")
    label_encoder = LabelEncoder()
    label_encoder.fit(FAULT_TYPES)  # Ensure consistent ordering
    y = label_encoder.transform(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )

    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")

    # Class distribution
    unique, counts = np.unique(y_train, return_counts=True)
    print("  Training class distribution:")
    for cls_idx, count in zip(unique, counts):
        cls_name = label_encoder.inverse_transform([cls_idx])[0]
        print(f"    {cls_name}: {count}")

    # ------------------------------------------------------------------
    # Step 3: Scale features
    # ------------------------------------------------------------------
    print("\n[3/5] Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ------------------------------------------------------------------
    # Step 4: Train model (with optional hyperparameter tuning)
    # ------------------------------------------------------------------
    n_classes = len(FAULT_TYPES)

    # Compute sample weights to handle class imbalance
    class_counts = np.bincount(y_train, minlength=n_classes)
    total = len(y_train)
    # Inverse frequency weighting
    class_weights = total / (n_classes * np.maximum(class_counts, 1))
    sample_weights = np.array([class_weights[yi] for yi in y_train])

    if tune_hyperparams:
        print(f"\n[4/5] Hyperparameter tuning ({n_iter_search} iterations)...")

        param_dist = {
            "n_estimators": [100, 200, 300, 500],
            "max_depth": [4, 6, 8, 10],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "min_child_weight": [1, 3, 5],
            "subsample": [0.7, 0.8, 0.9, 1.0],
            "colsample_bytree": [0.6, 0.7, 0.8, 0.9, 1.0],
            "gamma": [0, 0.1, 0.2, 0.5],
            "reg_alpha": [0, 0.01, 0.1],
            "reg_lambda": [0.5, 1.0, 2.0],
        }

        base_model = XGBClassifier(
            objective="multi:softprob",
            num_class=n_classes,
            eval_metric="mlogloss",
            random_state=random_state,
            use_label_encoder=False,
            verbosity=0,
        )

        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=random_state)

        search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter_search,
            cv=cv,
            scoring="f1_weighted",
            random_state=random_state,
            n_jobs=-1,
            verbose=1,
        )

        search.fit(X_train_scaled, y_train, sample_weight=sample_weights)
        model = search.best_estimator_
        print(f"  Best params: {search.best_params_}")
        print(f"  Best CV score: {search.best_score_:.4f}")
    else:
        print("\n[4/5] Training with default parameters...")
        model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=n_classes,
            eval_metric="mlogloss",
            random_state=random_state,
            use_label_encoder=False,
            verbosity=0,
        )
        model.fit(X_train_scaled, y_train, sample_weight=sample_weights)

    # ------------------------------------------------------------------
    # Step 5: Evaluate
    # ------------------------------------------------------------------
    print("\n[5/5] Evaluating model...")
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    recall_weighted = recall_score(y_test, y_pred, average="weighted")
    precision_weighted = precision_score(y_test, y_pred, average="weighted")

    target_names = [label_encoder.inverse_transform([i])[0] for i in range(n_classes)]
    report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    conf_matrix = confusion_matrix(y_test, y_pred).tolist()

    # Per-class recall
    per_class_recall = {}
    for cls_name in target_names:
        if cls_name in report:
            per_class_recall[cls_name] = report[cls_name]["recall"]

    # False positive rate per class
    per_class_fpr = {}
    cm = np.array(conf_matrix)
    for idx, cls_name in enumerate(target_names):
        fp = cm[:, idx].sum() - cm[idx, idx]
        tn = cm.sum() - cm[idx, :].sum() - cm[:, idx].sum() + cm[idx, idx]
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        per_class_fpr[cls_name] = fpr

    # Feature importance
    importance = dict(zip(feature_names, model.feature_importances_.tolist()))
    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15]

    training_duration = time.time() - start_time

    metrics = {
        "accuracy": accuracy,
        "f1_weighted": f1_weighted,
        "recall_weighted": recall_weighted,
        "precision_weighted": precision_weighted,
        "per_class_recall": per_class_recall,
        "per_class_fpr": per_class_fpr,
        "confusion_matrix": conf_matrix,
        "classification_report": report,
        "top_features": dict(top_features),
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "n_features": len(feature_names),
    }

    # Print summary
    print(f"\n{'='*60}")
    print("TRAINING RESULTS")
    print(f"{'='*60}")
    print(f"  Accuracy:           {accuracy:.4f}")
    print(f"  F1 (weighted):      {f1_weighted:.4f}")
    print(f"  Recall (weighted):  {recall_weighted:.4f}")
    print(f"  Precision (weighted): {precision_weighted:.4f}")
    print(f"  Training duration:  {training_duration:.1f}s")

    print(f"\n  Per-class recall:")
    for cls_name, recall_val in per_class_recall.items():
        status = "✓" if recall_val >= 0.80 else "✗"
        print(f"    {status} {cls_name}: {recall_val:.4f}")

    print(f"\n  Per-class false positive rate:")
    for cls_name, fpr_val in per_class_fpr.items():
        status = "✓" if fpr_val < 0.15 else "✗"
        print(f"    {status} {cls_name}: {fpr_val:.4f}")

    print(f"\n  Top-10 features:")
    for fname, fimportance in top_features[:10]:
        print(f"    {fname}: {fimportance:.4f}")

    # Validation against plan thresholds
    print(f"\n{'='*60}")
    print("VALIDATION vs. PLAN THRESHOLDS")
    print(f"{'='*60}")
    print(f"  Overall accuracy ≥ 85%: {'PASS' if accuracy >= 0.85 else 'FAIL'} ({accuracy:.1%})")

    all_recalls_pass = all(v >= 0.80 for v in per_class_recall.values())
    print(f"  All per-class recall ≥ 80%: {'PASS' if all_recalls_pass else 'FAIL'}")

    all_fpr_pass = all(v < 0.15 for v in per_class_fpr.values())
    print(f"  All per-class FPR < 15%: {'PASS' if all_fpr_pass else 'FAIL'}")

    return TrainingResult(
        model=model,
        scaler=scaler,
        label_encoder=label_encoder,
        feature_names=feature_names,
        metrics=metrics,
        training_duration_seconds=training_duration,
        n_samples=len(X),
    )
