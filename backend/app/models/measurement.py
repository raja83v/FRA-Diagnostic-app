"""
FRA Measurement model.
Contains normalized FRA measurement data with frequency, magnitude,
and phase arrays. References transformer asset and stores original file metadata.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class WindingConfig(str, enum.Enum):
    """Winding configuration for FRA measurement."""
    HV_LV = "HV-LV"
    HV_TV = "HV-TV"
    LV_TV = "LV-TV"
    HV_GND = "HV-GND"
    LV_GND = "LV-GND"
    TV_GND = "TV-GND"
    HV_OPEN = "HV-Open"
    LV_OPEN = "LV-Open"
    OTHER = "Other"


class FRAMeasurement(Base):
    __tablename__ = "fra_measurements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    transformer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transformers.id"), nullable=False, index=True
    )
    measurement_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    winding_config: Mapped[str] = mapped_column(
        SAEnum(WindingConfig), default=WindingConfig.HV_LV, nullable=False
    )

    # FRA data arrays stored as JSON (SQLite compatible; PostgreSQL can use ARRAY)
    frequency_hz: Mapped[list] = mapped_column(JSON, nullable=False)
    magnitude_db: Mapped[list] = mapped_column(JSON, nullable=False)
    phase_degrees: Mapped[list | None] = mapped_column(JSON)

    # Source information
    vendor: Mapped[str | None] = mapped_column(String(100))
    original_format: Mapped[str | None] = mapped_column(String(50))
    original_filename: Mapped[str | None] = mapped_column(String(500))

    # Additional vendor-specific metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    # Temperature at time of measurement (affects FRA)
    temperature_celsius: Mapped[float | None] = mapped_column(Float)

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    transformer: Mapped["Transformer"] = relationship(
        "Transformer", back_populates="measurements"
    )
    fault_analyses: Mapped[list["FaultAnalysis"]] = relationship(
        "FaultAnalysis", back_populates="measurement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<FRAMeasurement(id={self.id}, transformer={self.transformer_id}, "
            f"date={self.measurement_date}, winding={self.winding_config})>"
        )
