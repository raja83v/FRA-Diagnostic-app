"""
Fault Analysis API endpoints.
ML inference using trained XGBoost model for FRA fault classification.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.fault_analysis import FaultAnalysis
from app.models.measurement import FRAMeasurement
from app.models.transformer import Transformer
from app.schemas.analysis import AnalysisResponse, AnalysisRunRequest, AnalysisSummary
from app.services.auth import get_current_active_user
from app.services.ml_inference import get_inference_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Analysis"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("/", response_model=list[AnalysisSummary])
def list_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    measurement_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List fault analyses with optional filtering."""
    query = db.query(FaultAnalysis)

    if measurement_id:
        query = query.filter(FaultAnalysis.measurement_id == measurement_id)

    analyses = (
        query.order_by(FaultAnalysis.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [AnalysisSummary.model_validate(a) for a in analyses]


@router.get("/{analysis_id}/results", response_model=AnalysisResponse)
def get_analysis_results(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed analysis results with probabilities."""
    analysis = db.query(FaultAnalysis).filter(FaultAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis)


@router.post("/run/{measurement_id}", response_model=AnalysisResponse, status_code=201)
def run_analysis(
    measurement_id: str,
    body: AnalysisRunRequest = Body(default=AnalysisRunRequest()),
    db: Session = Depends(get_db),
):
    """
    Trigger ML analysis on a measurement.

    Uses the trained XGBoost model to classify faults from FRA data.
    Optionally compares against the transformer's baseline measurement.
    """
    # Fetch measurement
    measurement = (
        db.query(FRAMeasurement).filter(FRAMeasurement.id == measurement_id).first()
    )
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")

    # Get the inference service
    version = body.model_version or settings.ACTIVE_MODEL_VERSION
    service = get_inference_service(
        model_dir=settings.MODEL_DIR,
        version=version,
    )

    # Try to load model if not already loaded
    if not service.is_loaded:
        if not service.load():
            raise HTTPException(
                status_code=503,
                detail=(
                    "ML model not available. Train a model first by running: "
                    "python ml/train_and_evaluate.py"
                ),
            )

    # Fetch baseline measurement for comparison (if transformer has one)
    baseline_freq = None
    baseline_mag = None
    if measurement.transformer_id:
        transformer = db.query(Transformer).filter(
            Transformer.id == measurement.transformer_id
        ).first()
        if transformer and transformer.baseline_measurement_id:
            baseline = db.query(FRAMeasurement).filter(
                FRAMeasurement.id == transformer.baseline_measurement_id
            ).first()
            if baseline and baseline.id != measurement.id:
                baseline_freq = baseline.frequency_hz
                baseline_mag = baseline.magnitude_db

    # Run ML inference
    try:
        result = service.predict(
            frequency_hz=measurement.frequency_hz,
            magnitude_db=measurement.magnitude_db,
            phase_degrees=measurement.phase_degrees,
            baseline_freq=baseline_freq,
            baseline_mag=baseline_mag,
        )
    except Exception as e:
        logger.error(f"ML inference failed for measurement {measurement_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ML inference failed: {str(e)}",
        )

    # Store results in database
    analysis = FaultAnalysis(
        measurement_id=measurement_id,
        fault_type=result.fault_type,
        probability_score=result.probability_score,
        confidence_level=result.confidence_level,
        all_probabilities=result.all_probabilities,
        health_score=result.health_score,
        model_version=result.model_version,
        model_type=result.model_type,
        feature_importance=result.feature_importance if body.include_feature_importance else None,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    logger.info(
        f"Analysis complete: measurement={measurement_id}, "
        f"fault={result.fault_type}, health={result.health_score}"
    )

    return AnalysisResponse.model_validate(analysis)
