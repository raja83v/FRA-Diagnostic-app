"""
Recommendation API endpoints.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.recommendation import Recommendation, RecommendationStatus
from app.schemas.recommendation import RecommendationResponse, RecommendationStatusUpdate

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])


@router.get("/", response_model=list[RecommendationResponse])
def list_recommendations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    transformer_id: str | None = None,
    status: str | None = None,
    urgency: str | None = None,
    db: Session = Depends(get_db),
):
    """List recommendations with optional filtering."""
    query = db.query(Recommendation)

    if transformer_id:
        query = query.filter(Recommendation.transformer_id == transformer_id)
    if status:
        query = query.filter(Recommendation.status == status)
    if urgency:
        query = query.filter(Recommendation.urgency == urgency)

    recommendations = (
        query.order_by(Recommendation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [RecommendationResponse.model_validate(r) for r in recommendations]


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db)):
    """Get a specific recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return RecommendationResponse.model_validate(rec)


@router.get(
    "/transformer/{transformer_id}",
    response_model=list[RecommendationResponse],
)
def get_transformer_recommendations(
    transformer_id: str,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Get all recommendations for a specific transformer."""
    query = db.query(Recommendation).filter(
        Recommendation.transformer_id == transformer_id
    )
    if status:
        query = query.filter(Recommendation.status == status)

    recs = query.order_by(Recommendation.created_at.desc()).all()
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.put("/{recommendation_id}/status", response_model=RecommendationResponse)
def update_recommendation_status(
    recommendation_id: str,
    data: RecommendationStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the status of a recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # Validate status enum
    try:
        RecommendationStatus(data.status)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status: {data.status}. Must be: pending, in_progress, completed, deferred, cancelled",
        )

    rec.status = data.status
    if data.status_notes:
        rec.status_notes = data.status_notes
    if data.assigned_to is not None:
        rec.assigned_to = data.assigned_to
    if data.status == "completed":
        rec.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(rec)
    return RecommendationResponse.model_validate(rec)
