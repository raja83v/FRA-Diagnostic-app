"""
Import History API endpoints.
Lists past import attempts with filtering.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.import_history import ImportHistory


class ImportHistoryResponse(BaseModel):
    """Schema for import history records."""
    id: str
    original_filename: str
    file_size_bytes: int
    status: str
    measurement_id: str | None = None
    transformer_id: str | None = None
    detected_vendor: str | None = None
    detected_format: str | None = None
    parser_used: str | None = None
    data_points: int | None = None
    frequency_range: str | None = None
    warnings_json: list[str] | None = None
    errors_json: list[str] | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/v1/imports", tags=["Import History"])


@router.get("/", response_model=list[ImportHistoryResponse])
def list_imports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    transformer_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List import history records with optional filtering."""
    query = db.query(ImportHistory)

    if status:
        query = query.filter(ImportHistory.status == status)
    if transformer_id:
        query = query.filter(ImportHistory.transformer_id == transformer_id)

    records = (
        query.order_by(ImportHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [ImportHistoryResponse.model_validate(r) for r in records]


@router.get("/stats")
def import_stats(db: Session = Depends(get_db)):
    """Get summary statistics of imports."""
    total = db.query(ImportHistory).count()
    success = db.query(ImportHistory).filter(ImportHistory.status == "success").count()
    failed = db.query(ImportHistory).filter(ImportHistory.status == "failed").count()
    partial = db.query(ImportHistory).filter(ImportHistory.status == "partial").count()

    return {
        "total_imports": total,
        "successful": success,
        "failed": failed,
        "partial": partial,
    }
