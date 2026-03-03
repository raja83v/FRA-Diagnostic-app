"""
FRA Fault Classifier — Training & Evaluation Runner.

Orchestrates the end-to-end ML pipeline:
1. Generate synthetic training data with physics-based fault injection
2. Extract features from FRA curves
3. Train XGBoost multi-class classifier
4. Evaluate against plan thresholds
5. Save model artifacts to ml/saved_models/

Usage:
    python ml/train_and_evaluate.py
    python ml/train_and_evaluate.py --n-healthy 3000 --n-per-fault 300 --tune
    python ml/train_and_evaluate.py --no-tune --version v1.1.0
"""

import argparse
import sys
import os
import time

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate the FRA fault classification model"
    )
    parser.add_argument(
        "--n-healthy", type=int, default=2000,
        help="Number of healthy training samples (default: 2000)"
    )
    parser.add_argument(
        "--n-per-fault", type=int, default=200,
        help="Number of training samples per fault type (default: 200)"
    )
    parser.add_argument(
        "--version", type=str, default="v1.0.0",
        help="Model version string (default: v1.0.0)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--tune", action="store_true", default=True,
        help="Enable hyperparameter tuning (default: True)"
    )
    parser.add_argument(
        "--no-tune", action="store_true",
        help="Disable hyperparameter tuning for faster training"
    )
    parser.add_argument(
        "--n-iter", type=int, default=20,
        help="Number of hyperparameter search iterations (default: 20)"
    )
    parser.add_argument(
        "--model-dir", type=str, default="ml/saved_models",
        help="Directory to save model artifacts (default: ml/saved_models)"
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Skip separate evaluation step"
    )
    args = parser.parse_args()

    if args.no_tune:
        args.tune = False

    total_start = time.time()

    print("=" * 70)
    print("  FRA FAULT CLASSIFIER — TRAINING PIPELINE")
    print("=" * 70)
    print(f"\n  Configuration:")
    print(f"    Healthy samples:    {args.n_healthy}")
    print(f"    Per-fault samples:  {args.n_per_fault}")
    print(f"    Total expected:     {args.n_healthy + args.n_per_fault * 6}")
    print(f"    Model version:      {args.version}")
    print(f"    Hyperparameter tuning: {'Yes' if args.tune else 'No'}")
    print(f"    Random seed:        {args.seed}")
    print(f"    Output directory:   {args.model_dir}")

    # ==================================================================
    # Step 1: Generate Synthetic Training Data
    # ==================================================================
    print(f"\n{'='*70}")
    print("  STEP 1: SYNTHETIC DATA GENERATION")
    print(f"{'='*70}\n")

    from ml.data_generation.synthetic_fra import SyntheticFRAGenerator

    gen = SyntheticFRAGenerator(seed=args.seed)
    dataset = gen.generate(
        n_healthy=args.n_healthy,
        n_per_fault=args.n_per_fault,
    )

    # Save training data for reproducibility
    data_path = "ml/data_generation/training_data.npz"
    dataset.save(data_path)

    # ==================================================================
    # Step 2: Train XGBoost Model
    # ==================================================================
    print(f"\n{'='*70}")
    print("  STEP 2: MODEL TRAINING")
    print(f"{'='*70}\n")

    from ml.training.train_xgboost import train_xgboost_classifier

    result = train_xgboost_classifier(
        dataset=dataset,
        test_size=0.2,
        tune_hyperparams=args.tune,
        n_iter_search=args.n_iter,
        random_state=args.seed,
    )

    # Save model artifacts
    paths = result.save(args.model_dir, version=args.version)

    # ==================================================================
    # Step 3: Independent Evaluation
    # ==================================================================
    if not args.skip_eval:
        print(f"\n{'='*70}")
        print("  STEP 3: INDEPENDENT EVALUATION")
        print(f"{'='*70}\n")

        from ml.evaluation.evaluate import evaluate_model

        eval_results = evaluate_model(
            model_dir=args.model_dir,
            version=args.version,
            test_dataset=None,  # Will generate fresh test data
            output_dir="ml/evaluation",
        )

    # ==================================================================
    # Summary
    # ==================================================================
    total_time = time.time() - total_start
    print(f"\n{'='*70}")
    print("  PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"\n  Total time: {total_time:.1f}s")
    print(f"  Model saved to: {args.model_dir}/")
    print(f"\n  Files created:")
    for name, path in paths.items():
        print(f"    {name}: {path}")

    print(f"\n  Training metrics:")
    print(f"    Accuracy:    {result.metrics['accuracy']:.4f}")
    print(f"    F1 weighted: {result.metrics['f1_weighted']:.4f}")
    print(f"    Recall weighted: {result.metrics['recall_weighted']:.4f}")

    accuracy = result.metrics['accuracy']
    if accuracy >= 0.85:
        print(f"\n  ✓ Model meets minimum accuracy threshold (≥85%): {accuracy:.1%}")
    else:
        print(f"\n  ✗ Model below minimum accuracy threshold (≥85%): {accuracy:.1%}")
        print(f"    Consider increasing training data or tuning hyperparameters.")

    print(f"\n  To use this model in the API:")
    print(f"    1. Start the backend: cd backend && uvicorn app.main:app --reload")
    print(f"    2. POST /api/v1/analysis/run/{{measurement_id}}")
    print(f"    The model will be loaded automatically on first inference request.")

    # Optional: register in DB
    _register_model_in_db(args, result, paths)


def _register_model_in_db(args, result, paths):
    """Register the trained model in the database's ml_models table."""
    try:
        # Add backend to path for DB imports
        backend_root = os.path.join(PROJECT_ROOT, 'backend')
        if backend_root not in sys.path:
            sys.path.insert(0, backend_root)

        from app.database import SessionLocal, engine, Base
        from app.models.ml_model import MLModel

        # Ensure tables exist
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            # Deactivate any existing active models
            db.query(MLModel).filter(MLModel.is_active == True).update(
                {"is_active": False}
            )

            from datetime import datetime, timezone

            model_record = MLModel(
                name=f"XGBoost FRA Classifier",
                version=args.version,
                model_type="xgboost",
                description=(
                    f"Trained on {result.n_samples} synthetic FRA samples. "
                    f"Accuracy: {result.metrics['accuracy']:.4f}, "
                    f"F1: {result.metrics['f1_weighted']:.4f}"
                ),
                training_date=datetime.now(timezone.utc),
                training_samples=result.n_samples,
                training_duration_seconds=result.training_duration_seconds,
                metrics=result.metrics,
                accuracy=result.metrics["accuracy"],
                recall=result.metrics["recall_weighted"],
                false_positive_rate=max(
                    result.metrics.get("per_class_fpr", {}).values(), default=0
                ),
                is_active=True,
                file_path=paths.get("model", ""),
            )
            db.add(model_record)
            db.commit()
            print(f"\n  ✓ Model registered in database (ml_models table, is_active=True)")
        finally:
            db.close()
    except Exception as e:
        print(f"\n  Note: Could not register model in DB (non-critical): {e}")


if __name__ == "__main__":
    main()
