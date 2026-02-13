"""
Transformer CRUD API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.transformer import Transformer, TransformerCriticality
from app.models.measurement import FRAMeasurement
from app.schemas.transformer import (
    TransformerCreate,
    TransformerUpdate,
    TransformerResponse,
)

router = APIRouter(prefix="/api/v1/transformers", tags=["Transformers"])


@router.get("/", response_model=list[TransformerResponse])
def list_transformers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    criticality: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    """List all transformers with optional filtering."""
    query = db.query(Transformer)

    if criticality:
        query = query.filter(Transformer.criticality == criticality)
    if search:
        query = query.filter(Transformer.name.ilike(f"%{search}%"))

    transformers = query.order_by(Transformer.name).offset(skip).limit(limit).all()

    # Enrich with measurement count
    results = []
    for t in transformers:
        count = (
            db.query(func.count(FRAMeasurement.id))
            .filter(FRAMeasurement.transformer_id == t.id)
            .scalar()
        )
        resp = TransformerResponse.model_validate(t)
        resp.measurement_count = count
        results.append(resp)

    return results


@router.get("/{transformer_id}", response_model=TransformerResponse)
def get_transformer(transformer_id: str, db: Session = Depends(get_db)):
    """Get a specific transformer by ID."""
    transformer = db.query(Transformer).filter(Transformer.id == transformer_id).first()
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")

    count = (
        db.query(func.count(FRAMeasurement.id))
        .filter(FRAMeasurement.transformer_id == transformer.id)
        .scalar()
    )
    resp = TransformerResponse.model_validate(transformer)
    resp.measurement_count = count
    return resp


@router.post("/", response_model=TransformerResponse, status_code=201)
def create_transformer(data: TransformerCreate, db: Session = Depends(get_db)):
    """Create a new transformer asset record."""
    # Validate criticality enum
    try:
        TransformerCriticality(data.criticality)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid criticality: {data.criticality}. Must be: critical, important, standard",
        )

    transformer = Transformer(**data.model_dump())
    db.add(transformer)
    db.commit()
    db.refresh(transformer)

    resp = TransformerResponse.model_validate(transformer)
    resp.measurement_count = 0
    return resp


@router.put("/{transformer_id}", response_model=TransformerResponse)
def update_transformer(
    transformer_id: str, data: TransformerUpdate, db: Session = Depends(get_db)
):
    """Update an existing transformer."""
    transformer = db.query(Transformer).filter(Transformer.id == transformer_id).first()
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transformer, field, value)

    db.commit()
    db.refresh(transformer)

    count = (
        db.query(func.count(FRAMeasurement.id))
        .filter(FRAMeasurement.transformer_id == transformer.id)
        .scalar()
    )
    resp = TransformerResponse.model_validate(transformer)
    resp.measurement_count = count
    return resp


@router.delete("/{transformer_id}", status_code=204)
def delete_transformer(transformer_id: str, db: Session = Depends(get_db)):
    """Delete a transformer and all associated data."""
    transformer = db.query(Transformer).filter(Transformer.id == transformer_id).first()
    if not transformer:
        raise HTTPException(status_code=404, detail="Transformer not found")

    db.delete(transformer)
    db.commit()
