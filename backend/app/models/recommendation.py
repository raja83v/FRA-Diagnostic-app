"""
Recommendation model.
Stores generated maintenance recommendations with urgency level,
due date, assigned personnel, and completion status.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.transformer import Transformer
from app.models.fault_analysis import FaultAnalysis


class UrgencyLevel(str, enum.Enum):
    """Urgency classification for maintenance recommendations."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RecommendationStatus(str, enum.Enum):
    """Tracking status for recommendations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    fault_analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fault_analyses.id"), nullable=False, index=True
    )
    transformer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transformers.id"), nullable=False, index=True
    )

    # Recommendation details
    urgency: Mapped[str] = mapped_column(
        SAEnum(UrgencyLevel), nullable=False, default=UrgencyLevel.MEDIUM
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    fault_type: Mapped[str | None] = mapped_column(String(100))

    # Scheduling
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    assigned_to: Mapped[str | None] = mapped_column(String(255))

    # Status tracking
    status: Mapped[str] = mapped_column(
        SAEnum(RecommendationStatus),
        default=RecommendationStatus.PENDING,
        nullable=False,
    )
    status_notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    fault_analysis: Mapped["FaultAnalysis"] = relationship(
        "FaultAnalysis", back_populates="recommendations"
    )
    transformer: Mapped["Transformer"] = relationship(
        "Transformer", back_populates="recommendations"
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation(id={self.id}, urgency={self.urgency}, "
            f"status={self.status}, title={self.title[:40]})>"
        )
