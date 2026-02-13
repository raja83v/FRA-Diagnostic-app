"""
Fault Analysis model.
Records ML analysis results including fault type, probability score,
confidence level, and model version used for the prediction.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class FaultType(str, enum.Enum):
    """Transformer fault types detectable via FRA analysis."""
    AXIAL_DISPLACEMENT = "axial_displacement"
    RADIAL_DEFORMATION = "radial_deformation"
    CORE_GROUNDING = "core_grounding"
    WINDING_SHORT_CIRCUIT = "winding_short_circuit"
    LOOSE_CLAMPING = "loose_clamping"
    MOISTURE_INGRESS = "moisture_ingress"
    HEALTHY = "healthy"


class FaultAnalysis(Base):
    __tablename__ = "fault_analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    measurement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fra_measurements.id"), nullable=False, index=True
    )

    # Primary fault prediction
    fault_type: Mapped[str] = mapped_column(
        SAEnum(FaultType), nullable=False
    )
    probability_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)

    # All fault probabilities from ensemble (stored as JSON dict)
    all_probabilities: Mapped[dict | None] = mapped_column(JSON)

    # Overall transformer health score (0-100)
    health_score: Mapped[float | None] = mapped_column(Float)

    # Model information
    model_version: Mapped[str | None] = mapped_column(String(50))
    model_type: Mapped[str | None] = mapped_column(String(100))

    # Feature importance (from XGBoost, stored as JSON)
    feature_importance: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    measurement: Mapped["FRAMeasurement"] = relationship(
        "FRAMeasurement", back_populates="fault_analyses"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="fault_analysis", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<FaultAnalysis(id={self.id}, fault={self.fault_type}, "
            f"prob={self.probability_score:.2f}, health={self.health_score})>"
        )
