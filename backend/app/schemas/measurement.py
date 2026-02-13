"""
Pydantic schemas for FRA Measurement API.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class MeasurementBase(BaseModel):
    """Shared properties for FRA Measurement."""
    transformer_id: str
    measurement_date: datetime | None = None
    winding_config: str = Field("HV-LV", description="Winding configuration")
    vendor: str | None = None
    temperature_celsius: float | None = None
    notes: str | None = None


class MeasurementCreate(MeasurementBase):
    """Schema for creating a measurement via direct API (non-upload)."""
    frequency_hz: list[float]
    magnitude_db: list[float]
    phase_degrees: list[float] | None = None
    original_format: str | None = None
    metadata_json: dict | None = None


class MeasurementResponse(BaseModel):
    """Schema returned from API."""
    id: str
    transformer_id: str
    measurement_date: datetime
    winding_config: str
    frequency_hz: list[float]
    magnitude_db: list[float]
    phase_degrees: list[float] | None = None
    vendor: str | None = None
    original_format: str | None = None
    original_filename: str | None = None
    metadata_json: dict | None = None
    temperature_celsius: float | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MeasurementSummary(BaseModel):
    """Lightweight summary for listing measurements."""
    id: str
    transformer_id: str
    measurement_date: datetime
    winding_config: str
    vendor: str | None = None
    original_filename: str | None = None
    data_points: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    """Response after file upload and parsing."""
    measurement_id: str
    transformer_id: str
    filename: str
    vendor_detected: str | None = None
    data_points: int
    frequency_range: str
    validation_warnings: list[str] = []
    message: str = "File uploaded and parsed successfully"
