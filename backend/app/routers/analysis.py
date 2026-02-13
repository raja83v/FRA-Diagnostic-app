"""
Fault Analysis API endpoints.
ML inference endpoints (actual ML logic added in Phase 4).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.fault_analysis import FaultAnalysis
from app.models.measurement import FRAMeasurement
from app.schemas.analysis import AnalysisResponse, AnalysisSummary

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


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
def run_analysis(measurement_id: str, db: Session = Depends(get_db)):
    """
    Trigger ML analysis on a measurement.

    Phase 1: Returns a placeholder result.
    Phase 4: Will run actual ensemble ML inference.
    """
    measurement = (
        db.query(FRAMeasurement).filter(FRAMeasurement.id == measurement_id).first()
    )
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")

    # --- PLACEHOLDER: Phase 4 will replace this with real ML inference ---
    import random

    fault_types = [
        "healthy",
        "axial_displacement",
        "radial_deformation",
        "core_grounding",
        "winding_short_circuit",
        "loose_clamping",
        "moisture_ingress",
    ]

    # Generate mock probabilities
    raw_probs = {ft: random.uniform(0, 1) for ft in fault_types}
    total = sum(raw_probs.values())
    all_probs = {ft: round(p / total, 4) for ft, p in raw_probs.items()}

    primary_fault = max(all_probs, key=all_probs.get)  # type: ignore[arg-type]
    primary_prob = all_probs[primary_fault]

    health_score = round(all_probs.get("healthy", 0.5) * 100, 1)

    analysis = FaultAnalysis(
        measurement_id=measurement_id,
        fault_type=primary_fault,
        probability_score=primary_prob,
        confidence_level=round(random.uniform(0.6, 0.95), 3),
        all_probabilities=all_probs,
        health_score=health_score,
        model_version="placeholder-v0.0",
        model_type="random_placeholder",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    # --- END PLACEHOLDER ---

    return AnalysisResponse.model_validate(analysis)
