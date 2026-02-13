"""
Pydantic schemas for Fault Analysis API.
"""
from datetime import datetime
from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    """Schema for analysis results."""
    id: str
    measurement_id: str
    fault_type: str
    probability_score: float
    confidence_level: float
    all_probabilities: dict | None = None
    health_score: float | None = None
    model_version: str | None = None
    model_type: str | None = None
    feature_importance: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisRunRequest(BaseModel):
    """Request body for triggering analysis."""
    model_version: str | None = None
    include_feature_importance: bool = True


class AnalysisSummary(BaseModel):
    """Lightweight summary for listing analyses."""
    id: str
    measurement_id: str
    fault_type: str
    probability_score: float
    health_score: float | None = None
    model_version: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
