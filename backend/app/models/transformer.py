"""
Transformer asset model.
Stores transformer information including identification, location,
specifications, and criticality classification.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class TransformerCriticality(str, enum.Enum):
    """Transformer criticality classification for recommendation escalation."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    STANDARD = "standard"


class Transformer(Base):
    __tablename__ = "transformers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(500))
    substation: Mapped[str | None] = mapped_column(String(255))
    voltage_rating_kv: Mapped[float | None] = mapped_column(Float)
    power_rating_mva: Mapped[float | None] = mapped_column(Float)
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    year_of_manufacture: Mapped[int | None] = mapped_column()
    serial_number: Mapped[str | None] = mapped_column(String(255), unique=True)
    criticality: Mapped[str] = mapped_column(
        SAEnum(TransformerCriticality),
        default=TransformerCriticality.STANDARD,
        nullable=False,
    )
    baseline_measurement_id: Mapped[str | None] = mapped_column(String(36))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    measurements: Mapped[list["FRAMeasurement"]] = relationship(
        "FRAMeasurement", back_populates="transformer", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="transformer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Transformer(id={self.id}, name={self.name}, criticality={self.criticality})>"
