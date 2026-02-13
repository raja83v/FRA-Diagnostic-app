"""
Pydantic schemas for Transformer API.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class TransformerBase(BaseModel):
    """Shared properties for Transformer."""
    name: str = Field(..., max_length=255, description="Transformer name/identifier")
    location: str | None = Field(None, max_length=500)
    substation: str | None = Field(None, max_length=255)
    voltage_rating_kv: float | None = Field(None, gt=0)
    power_rating_mva: float | None = Field(None, gt=0)
    manufacturer: str | None = Field(None, max_length=255)
    year_of_manufacture: int | None = Field(None, ge=1900, le=2100)
    serial_number: str | None = Field(None, max_length=255)
    criticality: str = Field("standard", description="critical | important | standard")
    notes: str | None = None


class TransformerCreate(TransformerBase):
    """Schema for creating a new transformer."""
    pass


class TransformerUpdate(BaseModel):
    """Schema for updating a transformer (all fields optional)."""
    name: str | None = Field(None, max_length=255)
    location: str | None = None
    substation: str | None = None
    voltage_rating_kv: float | None = None
    power_rating_mva: float | None = None
    manufacturer: str | None = None
    year_of_manufacture: int | None = None
    serial_number: str | None = None
    criticality: str | None = None
    baseline_measurement_id: str | None = None
    notes: str | None = None


class TransformerResponse(TransformerBase):
    """Schema returned from API."""
    id: str
    baseline_measurement_id: str | None = None
    created_at: datetime
    updated_at: datetime
    measurement_count: int = 0

    model_config = {"from_attributes": True}
