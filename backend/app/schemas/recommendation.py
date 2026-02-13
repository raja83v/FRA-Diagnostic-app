"""
Pydantic schemas for Recommendation API.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    """Schema returned from API."""
    id: str
    fault_analysis_id: str
    transformer_id: str
    urgency: str
    title: str
    action_description: str
    fault_type: str | None = None
    due_date: datetime | None = None
    assigned_to: str | None = None
    status: str
    status_notes: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationStatusUpdate(BaseModel):
    """Schema for updating recommendation status."""
    status: str = Field(..., description="pending | in_progress | completed | deferred | cancelled")
    status_notes: str | None = None
    assigned_to: str | None = None
